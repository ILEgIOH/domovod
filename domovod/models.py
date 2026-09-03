"""Модели базы данных приложения «Домовод» (прямой SQLModel, без rx.Model)."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def gen_invite_code() -> str:
    return secrets.token_hex(4).upper()


class Tenant(SQLModel, table=True):
    """Управляющая компания (арендатор в мультитенантной модели)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    password_hash: str
    phone: str = ""
    created_at: datetime = Field(default_factory=now_utc)


class Building(SQLModel, table=True):
    """Дом, обслуживаемый управляющей компанией."""

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenant.id", index=True)
    address: str
    created_at: datetime = Field(default_factory=now_utc)


class Entrance(SQLModel, table=True):
    """Подъезд внутри дома. У каждого подъезда свой код приглашения."""

    id: Optional[int] = Field(default=None, primary_key=True)
    building_id: int = Field(foreign_key="building.id", index=True)
    tenant_id: int = Field(index=True)
    number: int
    invite_code: str = Field(default_factory=gen_invite_code, unique=True, index=True)
    created_at: datetime = Field(default_factory=now_utc)


class Resident(SQLModel, table=True):
    """Житель — пользователь приложения, привязанный к подъезду и УК."""

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    entrance_id: int = Field(foreign_key="entrance.id", index=True)
    full_name: str
    apartment: str
    # Общее число жильцов квартиры — заполняет первый, кто зарегистрировал
    # эту квартиру в этом подъезде; остальные видят то же число и не могут
    # его менять (см. AuthState.check_join_apartment / join_confirm).
    household_size: int = 0
    # Житель, зашедший по коду/QR через MAX, не задаёт телефон и пароль —
    # его личность подтверждает MAX (пока — заглушка max_user_id).
    phone: Optional[str] = Field(default=None, unique=True, index=True)
    password_hash: Optional[str] = Field(default=None)
    max_user_id: Optional[str] = Field(default=None, unique=True, index=True)
    created_at: datetime = Field(default_factory=now_utc)


class News(SQLModel, table=True):
    """Новость от управляющей компании."""

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    building_id: Optional[int] = Field(default=None, index=True)
    title: str
    body: str
    author_name: str = ""
    created_at: datetime = Field(default_factory=now_utc)


class Debt(SQLModel, table=True):
    """Задолженность жителя по конкретному периоду/статье начислений."""

    id: Optional[int] = Field(default=None, primary_key=True)
    resident_id: int = Field(index=True)
    tenant_id: int = Field(index=True)
    period: str
    category: str = "ЖКХ"
    amount: float = 0
    is_paid: bool = False
    created_at: datetime = Field(default_factory=now_utc)


class Collection(SQLModel, table=True):
    """Сбор денег с жителей подъезда (ЖКХ, ремонт и т.д.)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    entrance_id: int = Field(index=True)
    tenant_id: int = Field(index=True)
    title: str
    description: str = ""
    category: str = "ЖКХ"
    target_amount: float = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=now_utc)


class CollectionPayment(SQLModel, table=True):
    """Взнос жителя в конкретный сбор, привязанный к платежу ЮKassa."""

    id: Optional[int] = Field(default=None, primary_key=True)
    collection_id: int = Field(foreign_key="collection.id", index=True)
    resident_id: int = Field(index=True)
    resident_name: str = ""
    amount: float = 0
    status: str = "pending"
    yk_payment_id: str = ""
    created_at: datetime = Field(default_factory=now_utc)
