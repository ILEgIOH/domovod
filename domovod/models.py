"""Модели базы данных приложения «Домовод» (прямой SQLModel, без rx.Model)."""

from __future__ import annotations

import secrets
import string
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def gen_invite_code() -> str:
    """Код приглашения в формате БУК-ВЫ+ЦИФ (3 буквы + 3 цифры, без дефиса
    в хранении — дефис только для отображения/ввода)."""
    letters = "".join(secrets.choice(string.ascii_uppercase) for _ in range(3))
    digits = "".join(secrets.choice(string.digits) for _ in range(3))
    return letters + digits


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
    # R06: когда квартиру уже занял другой житель, новый заявитель ждёт
    # подтверждения администратора вместо мгновенного входа. "active" —
    # обычный житель, "pending" — заявка на рассмотрении.
    status: str = "active"
    created_at: datetime = Field(default_factory=now_utc)


class News(SQLModel, table=True):
    """Объявление от управляющей компании (короткая «таблетка» на главном экране,
    полный список — B01–B05)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    entrance_id: int = Field(index=True)
    tenant_id: int = Field(index=True)
    title: str
    body: str
    period_text: str = ""
    category: str = "general"  # "water" | "power" | "elevator" | "general"
    urgency: str = "normal"  # "normal" | "urgent"
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
    """Сбор денег с жителей подъезда (ЖКХ, ремонт и т.д.).

    Может быть создан напрямую УК (status="published") или предложен
    жителем (status="proposed") — тогда он ждёт, пока УК его отредактирует
    и опубликует (см. FinanceState.propose_collection/publish_collection).
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    entrance_id: int = Field(index=True)
    tenant_id: int = Field(index=True)
    title: str
    description: str = ""
    instructions: str = ""
    category: str = "ЖКХ"
    amount_mode: str = "per_apartment"  # "per_apartment" | "total" (F02/F04)
    target_amount: float = 0
    end_date: Optional[datetime] = None
    status: str = "published"  # "proposed" | "published" | "rejected"
    proposed_by_resident_id: Optional[int] = None
    rejection_reason: str = ""
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


class Initiative(SQLModel, table=True):
    """Инициатива жителей подъезда (субботник и т.п.) с голосованием «я за»."""

    id: Optional[int] = Field(default=None, primary_key=True)
    entrance_id: int = Field(index=True)
    tenant_id: int = Field(index=True)
    title: str
    description: str = ""
    needed_count: int = 0
    author_name: str = ""
    event_date: str = ""
    status: str = "published"  # "proposed" | "published" | "rejected"
    proposed_by_resident_id: Optional[int] = None
    rejection_reason: str = ""
    is_active: bool = True
    created_at: datetime = Field(default_factory=now_utc)


class InitiativeVote(SQLModel, table=True):
    """Голос «я за» жителя по инициативе."""

    id: Optional[int] = Field(default=None, primary_key=True)
    initiative_id: int = Field(foreign_key="initiative.id", index=True)
    resident_id: int = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc)


class Poll(SQLModel, table=True):
    """Опрос среди жителей подъезда с вариантами ответа (макет Q01–Q06):
    один голос на жителя по умолчанию, либо несколько — если allow_multiple."""

    id: Optional[int] = Field(default=None, primary_key=True)
    entrance_id: int = Field(index=True)
    tenant_id: int = Field(index=True)
    title: str
    description: str = ""
    author_name: str = ""
    end_date: Optional[datetime] = None
    allow_multiple: bool = False
    allow_vote_change: bool = True
    status: str = "published"  # "proposed" | "published" | "rejected"
    proposed_by_resident_id: Optional[int] = None
    rejection_reason: str = ""
    is_active: bool = True
    created_at: datetime = Field(default_factory=now_utc)


class PollOption(SQLModel, table=True):
    """Вариант ответа опроса («Да, установить» / «Нет, не нужно»)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    poll_id: int = Field(foreign_key="poll.id", index=True)
    label: str
    order: int = 0


class PollVote(SQLModel, table=True):
    """Голос жителя за конкретный вариант опроса. При allow_multiple=False
    у жителя может быть только одна такая запись на poll_id."""

    id: Optional[int] = Field(default=None, primary_key=True)
    poll_id: int = Field(foreign_key="poll.id", index=True)
    option_id: int = Field(foreign_key="polloption.id", index=True)
    resident_id: int = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc)


class UsefulAddress(SQLModel, table=True):
    """Служба дома или полезный адрес подъезда — задаёт УК, видят все
    жители. category различает два раздела R01 в одной таблице:
    "service" — служба дома (R02, value = имя), "address" — полезный
    адрес (R03, value = адрес)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    entrance_id: int = Field(index=True)
    tenant_id: int = Field(index=True)
    category: str = "address"  # "service" | "address"
    title: str
    value: str
    phone: str = ""
    created_at: datetime = Field(default_factory=now_utc)


class PersonalContact(SQLModel, table=True):
    """Личный контакт пользователя (свой для УК и для каждого жителя)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_role: str  # "uk" | "resident"
    owner_id: int  # tenant_id или resident_id, в зависимости от owner_role
    name: str
    phone: str = ""
    created_at: datetime = Field(default_factory=now_utc)
