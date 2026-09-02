"""Интеграция с ЮKassa (тестовый режим/sandbox).

По умолчанию используются публичные тестовые реквизиты ЮKassa, которые
работают без регистрации магазина (https://yookassa.ru) — реальные деньги
не списываются. Для продакшена задайте свои YOOKASSA_SHOP_ID и
YOOKASSA_SECRET_KEY через переменные окружения.
"""

import os
import uuid

import httpx

YK_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "54401")
YK_SECRET_KEY = os.getenv(
    "YOOKASSA_SECRET_KEY", "test_Fh8hUAVVBGUGbjmlzba6TB0iyUbos_lueTHE-axOwM0"
)
YK_API_URL = "https://api.yookassa.ru/v3"


class PaymentError(Exception):
    pass


async def create_payment(amount: float, description: str, return_url: str) -> dict:
    """Создаёт платёж в ЮKassa и возвращает ответ API (включая confirmation_url)."""
    payload = {
        "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": return_url},
        "capture": True,
        "description": description[:128],
    }
    try:
        async with httpx.AsyncClient(auth=(YK_SHOP_ID, YK_SECRET_KEY), timeout=15) as client:
            resp = await client.post(
                f"{YK_API_URL}/payments",
                json=payload,
                headers={"Idempotence-Key": str(uuid.uuid4())},
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError as exc:
        raise PaymentError(str(exc)) from exc


async def get_payment_status(payment_id: str) -> dict:
    """Возвращает текущий статус платежа (pending/waiting_for_capture/succeeded/canceled)."""
    try:
        async with httpx.AsyncClient(auth=(YK_SHOP_ID, YK_SECRET_KEY), timeout=15) as client:
            resp = await client.get(f"{YK_API_URL}/payments/{payment_id}")
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError as exc:
        raise PaymentError(str(exc)) from exc
