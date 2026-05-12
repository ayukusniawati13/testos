"""Groq API client with multi-key rotation.

Handles:
- transcription (whisper-large-v3-turbo, whisper-large-v3) via /audio/transcriptions
- chat completions for lyric correction via /chat/completions
- automatic rotation on 401 / 429 / quota errors
- a lightweight `test_key()` method used by the UI
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import Any

import requests

from ..constants import GROQ_BASE_URL

logger = logging.getLogger(__name__)


class GroqError(RuntimeError):
    pass


class AllKeysExhaustedError(GroqError):
    pass


class GroqAuthError(GroqError):
    pass


@dataclass
class KeyState:
    key: str
    label: str = ""
    enabled: bool = True
    cooldown_until: float = 0.0
    last_error: str = ""
    failures: int = 0


class GroqClient:
    """Thread-safe Groq client that rotates through a pool of API keys."""

    def __init__(self, keys: list[str | tuple[str, str]] | None = None, timeout: float = 120.0):
        self._lock = threading.Lock()
        self._keys: list[KeyState] = []
        self._cursor = 0
        self.timeout = timeout
        if keys:
            self.set_keys(keys)

    # ----- key management ---------------------------------------------------
    def set_keys(self, keys: list[str | tuple[str, str]]) -> None:
        states: list[KeyState] = []
        for item in keys:
            if isinstance(item, tuple):
                label, key = item
            else:
                label, key = "", item
            key = (key or "").strip()
            if not key:
                continue
            states.append(KeyState(key=key, label=label))
        with self._lock:
            self._keys = states
            self._cursor = 0

    def has_keys(self) -> bool:
        return any(s.enabled for s in self._keys)

    def key_summaries(self) -> list[dict[str, Any]]:
        with self._lock:
            now = time.time()
            return [
                {
                    "label": s.label,
                    "masked": _mask(s.key),
                    "enabled": s.enabled,
                    "cooldown": max(0.0, s.cooldown_until - now),
                    "failures": s.failures,
                    "last_error": s.last_error,
                }
                for s in self._keys
            ]

    def _next_key(self) -> KeyState:
        with self._lock:
            if not self._keys:
                raise AllKeysExhaustedError("Tidak ada API key Groq yang dikonfigurasi.")
            now = time.time()
            n = len(self._keys)
            for i in range(n):
                idx = (self._cursor + i) % n
                state = self._keys[idx]
                if state.enabled and state.cooldown_until <= now:
                    self._cursor = (idx + 1) % n
                    return state
            # All keys on cooldown; sleep until the earliest one is ready
            cooldowns = [s.cooldown_until for s in self._keys if s.enabled]
            if not cooldowns:
                raise AllKeysExhaustedError("Semua API key Groq dinonaktifkan atau tidak valid.")
            wait = max(0.0, min(cooldowns) - now)
        if wait > 0:
            logger.warning("Semua API key Groq sedang cooldown; menunggu %.1fs...", min(wait, 30))
            time.sleep(min(wait, 30))
            return self._next_key()
        raise AllKeysExhaustedError("Semua API key Groq dinonaktifkan atau tidak valid.")

    # ----- HTTP helpers -----------------------------------------------------
    def _post(
        self,
        endpoint: str,
        *,
        json_body: dict | None = None,
        files: dict | None = None,
        data: dict | None = None,
        max_retries: int | None = None,
    ) -> requests.Response:
        n = len(self._keys) if self._keys else 0
        if n == 0:
            raise AllKeysExhaustedError("Tidak ada API key Groq yang dikonfigurasi.")
        attempts = max_retries if max_retries is not None else max(2 * n, 2)
        last_exc: Exception | None = None
        url = GROQ_BASE_URL.rstrip("/") + endpoint
        for _ in range(attempts):
            state = self._next_key()
            headers = {"Authorization": f"Bearer {state.key}"}
            try:
                resp = requests.post(
                    url,
                    headers=headers,
                    json=json_body,
                    files=files,
                    data=data,
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                state.last_error = f"network: {exc}"
                state.failures += 1
                last_exc = exc
                # Network issues: cool down briefly, try next key
                state.cooldown_until = time.time() + 5.0
                continue

            if resp.status_code == 401:
                state.enabled = False
                state.last_error = "401 unauthorized"
                state.failures += 1
                logger.warning("Groq key %s ditolak (401); dinonaktifkan.", _mask(state.key))
                continue
            if resp.status_code == 429:
                retry_after = _retry_after(resp)
                state.cooldown_until = time.time() + retry_after
                state.last_error = f"429 rate-limit retry_after={retry_after:.1f}s"
                state.failures += 1
                logger.info("Groq key %s rate-limited; coba key berikutnya.", _mask(state.key))
                continue
            if resp.status_code in (402, 403):
                state.enabled = False
                state.last_error = f"{resp.status_code} {_short_body(resp)}"
                state.failures += 1
                logger.warning("Groq key %s ditolak (%s); dinonaktifkan.", _mask(state.key), resp.status_code)
                continue
            if 500 <= resp.status_code < 600:
                state.cooldown_until = time.time() + 3.0
                state.last_error = f"{resp.status_code} server error"
                state.failures += 1
                continue

            if resp.status_code >= 400:
                # Generic 4xx - bubble up after exhausting keys
                state.last_error = f"{resp.status_code} {_short_body(resp)}"
                state.failures += 1
                last_exc = GroqError(state.last_error)
                continue

            return resp

        if last_exc:
            raise GroqError(f"Semua percobaan gagal: {last_exc}")
        raise AllKeysExhaustedError("Semua API key Groq habis kuota / gagal.")

    # ----- public API -------------------------------------------------------
    def test_key(self, key: str) -> tuple[bool, str]:
        """Return (ok, message)."""
        key = (key or "").strip()
        if not key:
            return False, "API key kosong"
        try:
            resp = requests.get(
                GROQ_BASE_URL.rstrip("/") + "/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=15,
            )
        except requests.RequestException as exc:
            return False, f"network: {exc}"
        if resp.status_code == 200:
            try:
                data = resp.json()
                models = data.get("data") or []
                return True, f"OK ({len(models)} model tersedia)"
            except Exception:
                return True, "OK"
        if resp.status_code == 401:
            return False, "401 Unauthorized"
        return False, f"{resp.status_code} {_short_body(resp)}"

    def transcribe(
        self,
        audio_path: str,
        *,
        model: str,
        language: str | None = None,
        response_format: str = "verbose_json",
        timestamp_granularities: list[str] | None = None,
        prompt: str | None = None,
    ) -> dict[str, Any]:
        timestamp_granularities = timestamp_granularities or ["word", "segment"]
        data: dict[str, Any] = {
            "model": model,
            "response_format": response_format,
        }
        if language:
            data["language"] = language
        if prompt:
            data["prompt"] = prompt
        for g in timestamp_granularities:
            data.setdefault("timestamp_granularities[]", []).append(g) if isinstance(
                data.get("timestamp_granularities[]"), list
            ) else data.update({"timestamp_granularities[]": [g]})

        size = os.path.getsize(audio_path)
        if size > 25 * 1024 * 1024:
            logger.warning("Audio %s berukuran %.1f MB; Groq merekomendasikan <25 MB.", audio_path, size / 1e6)

        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f, "application/octet-stream")}
            resp = self._post(
                "/audio/transcriptions",
                files=files,
                data=data,
            )
        try:
            return resp.json()
        except ValueError as exc:
            raise GroqError(f"Respons transkripsi bukan JSON: {exc}") from exc

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        response_format: dict | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format
        resp = self._post("/chat/completions", json_body=payload)
        try:
            return resp.json()
        except ValueError as exc:
            raise GroqError(f"Respons chat bukan JSON: {exc}") from exc


def _mask(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "*" * len(key)
    return key[:4] + "…" + key[-4:]


def _retry_after(resp: requests.Response) -> float:
    header = resp.headers.get("Retry-After")
    if header:
        try:
            return float(header)
        except ValueError:
            pass
    try:
        body = resp.json()
        msg = json.dumps(body)
        # Pattern: "try again in 12.345s"
        import re

        m = re.search(r"try again in ([0-9.]+)s", msg, flags=re.I)
        if m:
            return float(m.group(1))
    except Exception:
        pass
    return 10.0


def _short_body(resp: requests.Response) -> str:
    try:
        body = resp.json()
        msg = (body.get("error") or {}).get("message") if isinstance(body, dict) else None
        if msg:
            return str(msg)[:200]
        return json.dumps(body)[:200]
    except Exception:
        return (resp.text or "")[:200]
