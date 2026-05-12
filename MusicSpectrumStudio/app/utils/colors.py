"""Color helpers."""

from __future__ import annotations


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    v = value.lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    if len(v) != 6:
        return (255, 255, 255)
    try:
        return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))
    except ValueError:
        return (255, 255, 255)


def hex_to_rgba(value: str, alpha: int = 255) -> tuple[int, int, int, int]:
    r, g, b = hex_to_rgb(value)
    return (r, g, b, alpha)


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def lerp_color(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def hsv_to_rgb(h: float, s: float, v: float) -> tuple[int, int, int]:
    """h in [0,1), s/v in [0,1]."""
    import colorsys

    r, g, b = colorsys.hsv_to_rgb(h % 1.0, max(0.0, min(1.0, s)), max(0.0, min(1.0, v)))
    return int(r * 255), int(g * 255), int(b * 255)
