"""Ссылки-приглашения и QR-коды для входа жителей по коду подъезда."""

from __future__ import annotations

import base64
import io

import segno


def build_join_url(origin: str, invite_code: str) -> str:
    """Собирает ссылку вида https://<домен>/join?code=КОД."""
    base = origin.rstrip("/") if origin else ""
    return f"{base}/join?code={invite_code}"


def qr_data_uri(url: str) -> str:
    """Кодирует QR-код ссылки в data URI (PNG) для <rx.image src=...>."""
    qr = segno.make(url, error="m")
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=6, border=2)
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
