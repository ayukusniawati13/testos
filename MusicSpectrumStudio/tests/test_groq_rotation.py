"""Unit tests for the multi-key Groq client rotation logic."""

from __future__ import annotations

from unittest.mock import patch

import pytest
import requests

from app.core.groq_client import (
    AllKeysExhaustedError,
    GroqClient,
)


class FakeResponse:
    def __init__(self, status_code: int, json_body: dict | None = None, headers: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._json = json_body or {}
        self.headers = headers or {}
        self.text = text

    def json(self) -> dict:
        return self._json


def _post_factory(sequence: list[FakeResponse]) -> callable:
    iterator = iter(sequence)

    def fake_post(url, headers=None, json=None, files=None, data=None, timeout=None):
        try:
            return next(iterator)
        except StopIteration as exc:
            raise AssertionError("FakeResponse sequence exhausted") from exc

    return fake_post


def test_set_keys_filters_empty():
    client = GroqClient()
    client.set_keys([("a", ""), ("b", "gsk_real"), "  ", "gsk_x"])
    assert len(client.key_summaries()) == 2


def test_rotation_on_429_then_success():
    client = GroqClient([("k1", "gsk_one"), ("k2", "gsk_two")])
    responses = [
        FakeResponse(429, headers={"Retry-After": "0.01"}),
        FakeResponse(200, {"ok": True}),
    ]
    with patch("requests.post", side_effect=_post_factory(responses)):
        resp = client._post("/chat/completions", json_body={})
    assert resp.status_code == 200
    summaries = client.key_summaries()
    # first key should have a recorded failure
    assert summaries[0]["failures"] == 1


def test_rotation_disables_invalid_key():
    client = GroqClient([("k1", "gsk_one"), ("k2", "gsk_two")])
    responses = [
        FakeResponse(401, {"error": {"message": "invalid"}}),
        FakeResponse(200, {"ok": True}),
    ]
    with patch("requests.post", side_effect=_post_factory(responses)):
        resp = client._post("/chat/completions", json_body={})
    assert resp.status_code == 200
    summaries = client.key_summaries()
    assert summaries[0]["enabled"] is False
    assert summaries[1]["enabled"] is True


def test_all_keys_exhausted():
    client = GroqClient([("k1", "gsk_a"), ("k2", "gsk_b")])
    responses = [
        FakeResponse(401),
        FakeResponse(401),
    ]
    with patch("requests.post", side_effect=_post_factory(responses)):
        with pytest.raises(AllKeysExhaustedError):
            client._post("/chat/completions", json_body={})


def test_test_key_ok():
    client = GroqClient()
    fake = FakeResponse(200, {"data": [{"id": "whisper-large-v3"}]})
    with patch("requests.get", return_value=fake):
        ok, msg = client.test_key("gsk_valid")
    assert ok is True
    assert "OK" in msg


def test_test_key_bad():
    client = GroqClient()
    fake = FakeResponse(401, {"error": {"message": "Invalid API Key"}})
    with patch("requests.get", return_value=fake):
        ok, msg = client.test_key("gsk_bad")
    assert ok is False
    assert "401" in msg


def test_network_error_failover():
    client = GroqClient([("k1", "gsk_one"), ("k2", "gsk_two")])
    sequence = [requests.ConnectionError("boom"), FakeResponse(200, {"ok": True})]
    call_n = {"n": 0}

    def fake_post(*args, **kwargs):
        idx = call_n["n"]
        call_n["n"] += 1
        result = sequence[idx]
        if isinstance(result, Exception):
            raise result
        return result

    with patch("requests.post", side_effect=fake_post):
        resp = client._post("/chat/completions", json_body={})
    assert resp.status_code == 200
