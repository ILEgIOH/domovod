"""Задолженности и сборы: управление со стороны УК, просмотр и оплата со стороны жителя."""

from __future__ import annotations

import asyncio
import os
from typing import List, Optional

import reflex as rx
from pydantic import BaseModel
from sqlmodel import select

from .db import get_session
from .models import Collection, CollectionPayment, Debt, Entrance, Resident
from .payments import PaymentError, create_payment, get_payment_status
from .setters import make_setter
from .state import AuthState

APP_BASE_URL = os.getenv(
    "APP_BASE_URL", os.getenv("RENDER_EXTERNAL_URL", "http://localhost:3000")
)
POLL_INTERVAL = 3.0


def _rub(value: float) -> str:
    return f"{value:,.0f} ₽".replace(",", " ")


class DebtItem(BaseModel):
    id: int
    resident_name: str
    apartment: str
    entrance_number: int
    period: str
    category: str
    amount: float
    amount_fmt: str
    is_paid: bool


class CollectionItem(BaseModel):
    id: int
    entrance_id: int
    entrance_number: int
    title: str
    description: str
    category: str
    target_amount: float
    target_fmt: str
    collected_amount: float
    collected_fmt: str
    remaining: float = 0
    remaining_fmt: str = "0 ₽"
    progress_pct: int
    is_active: bool
    my_contribution: float = 0
    my_contribution_fmt: str = "0 ₽"
    my_payment_pending: bool = False


class ResidentOption(BaseModel):
    id: int
    label: str


class EntranceOption(BaseModel):
    id: int
    label: str


class FinanceState(AuthState):
    debts: List[DebtItem] = []
    my_debts: List[DebtItem] = []
    collections: List[CollectionItem] = []
    my_collections: List[CollectionItem] = []

    resident_options: List[ResidentOption] = []
    entrance_options: List[EntranceOption] = []

    new_debt_resident_id: str = ""
    new_debt_period: str = ""
    new_debt_category: str = "ЖКХ"
    new_debt_amount: str = ""
    debt_error: str = ""

    new_col_entrance_id: str = ""
    new_col_title: str = ""
    new_col_description: str = ""
    new_col_category: str = "ЖКХ"
    new_col_amount: str = ""
    col_error: str = ""

    pay_error: str = ""
    paying_collection_id: int = 0
    is_live: bool = False

    set_new_debt_resident_id = make_setter("new_debt_resident_id")
    set_new_debt_period = make_setter("new_debt_period")
    set_new_debt_category = make_setter("new_debt_category")
    set_new_debt_amount = make_setter("new_debt_amount")
    set_new_col_entrance_id = make_setter("new_col_entrance_id")
    set_new_col_title = make_setter("new_col_title")
    set_new_col_description = make_setter("new_col_description")
    set_new_col_category = make_setter("new_col_category")
    set_new_col_amount = make_setter("new_col_amount")

    # ---------------- УК: загрузка данных ----------------

    @rx.event
    def load_uk_finance(self):
        if not self.tenant_id:
            return
        with get_session() as session:
            residents = session.exec(
                select(Resident).where(Resident.tenant_id == self.tenant_id)
            ).all()
            entrances = session.exec(
                select(Entrance).where(Entrance.tenant_id == self.tenant_id)
            ).all()
            entrance_map = {e.id: e for e in entrances}
            resident_map = {r.id: r for r in residents}

            self.resident_options = [
                ResidentOption(
                    id=r.id,
                    label=f"{r.full_name} — кв. {r.apartment} (подъезд {entrance_map[r.entrance_id].number})"
                    if r.entrance_id in entrance_map
                    else f"{r.full_name} — кв. {r.apartment}",
                )
                for r in residents
            ]
            self.entrance_options = [
                EntranceOption(id=e.id, label=f"Подъезд {e.number}") for e in entrances
            ]

            debt_rows = session.exec(
                select(Debt).where(Debt.tenant_id == self.tenant_id).order_by(Debt.created_at.desc())
            ).all()
            debt_items = []
            for d in debt_rows:
                r = resident_map.get(d.resident_id)
                if not r:
                    continue
                e = entrance_map.get(r.entrance_id)
                debt_items.append(
                    DebtItem(
                        id=d.id,
                        resident_name=r.full_name,
                        apartment=r.apartment,
                        entrance_number=e.number if e else 0,
                        period=d.period,
                        category=d.category,
                        amount=d.amount,
                        amount_fmt=_rub(d.amount),
                        is_paid=d.is_paid,
                    )
                )
            self.debts = debt_items

            col_rows = session.exec(
                select(Collection)
                .where(Collection.tenant_id == self.tenant_id)
                .order_by(Collection.created_at.desc())
            ).all()
            col_items = []
            for c in col_rows:
                collected = self._collected_amount(session, c.id)
                e = entrance_map.get(c.entrance_id)
                col_items.append(
                    CollectionItem(
                        id=c.id,
                        entrance_id=c.entrance_id,
                        entrance_number=e.number if e else 0,
                        title=c.title,
                        description=c.description,
                        category=c.category,
                        target_amount=c.target_amount,
                        target_fmt=_rub(c.target_amount),
                        collected_amount=collected,
                        collected_fmt=_rub(collected),
                        progress_pct=self._pct(collected, c.target_amount),
                        is_active=c.is_active,
                    )
                )
            self.collections = col_items

    @staticmethod
    def _collected_amount(session, collection_id: int) -> float:
        payments = session.exec(
            select(CollectionPayment).where(
                CollectionPayment.collection_id == collection_id,
                CollectionPayment.status == "succeeded",
            )
        ).all()
        return sum(p.amount for p in payments)

    @staticmethod
    def _pct(collected: float, target: float) -> int:
        if target <= 0:
            return 0
        return min(100, int(collected / target * 100))

    @rx.event
    def add_debt(self):
        self.debt_error = ""
        if not self.new_debt_resident_id or not self.new_debt_period.strip() or not self.new_debt_amount:
            self.debt_error = "Заполните все поля"
            return
        try:
            resident_id = int(self.new_debt_resident_id)
            amount = float(self.new_debt_amount.replace(",", "."))
        except ValueError:
            self.debt_error = "Некорректная сумма"
            return
        with get_session() as session:
            session.add(
                Debt(
                    resident_id=resident_id,
                    tenant_id=self.tenant_id,
                    period=self.new_debt_period.strip(),
                    category=self.new_debt_category,
                    amount=amount,
                )
            )
            session.commit()
        self.new_debt_period = ""
        self.new_debt_amount = ""
        return FinanceState.load_uk_finance

    @rx.event
    def toggle_debt_paid(self, debt_id: int):
        with get_session() as session:
            debt = session.get(Debt, debt_id)
            if debt and debt.tenant_id == int(self.tenant_id):
                debt.is_paid = not debt.is_paid
                session.add(debt)
                session.commit()
        return FinanceState.load_uk_finance

    @rx.event
    def create_collection(self):
        self.col_error = ""
        if not self.new_col_entrance_id or not self.new_col_title.strip() or not self.new_col_amount:
            self.col_error = "Заполните все поля"
            return
        try:
            entrance_id = int(self.new_col_entrance_id)
            amount = float(self.new_col_amount.replace(",", "."))
        except ValueError:
            self.col_error = "Некорректная сумма"
            return
        with get_session() as session:
            session.add(
                Collection(
                    entrance_id=entrance_id,
                    tenant_id=self.tenant_id,
                    title=self.new_col_title.strip(),
                    description=self.new_col_description.strip(),
                    category=self.new_col_category,
                    target_amount=amount,
                )
            )
            session.commit()
        self.new_col_title = ""
        self.new_col_description = ""
        self.new_col_amount = ""
        return FinanceState.load_uk_finance

    @rx.event
    def toggle_collection_active(self, collection_id: int):
        with get_session() as session:
            c = session.get(Collection, collection_id)
            if c and c.tenant_id == int(self.tenant_id):
                c.is_active = not c.is_active
                session.add(c)
                session.commit()
        return FinanceState.load_uk_finance

    # ---------------- Житель: просмотр и оплата ----------------

    @rx.event
    def load_resident_finance(self):
        if not self.user_id or not self.entrance_id:
            return
        with get_session() as session:
            debt_rows = session.exec(
                select(Debt)
                .where(Debt.resident_id == self.user_id)
                .order_by(Debt.created_at.desc())
            ).all()
            self.my_debts = [
                DebtItem(
                    id=d.id,
                    resident_name=self.display_name,
                    apartment=self.apartment,
                    entrance_number=0,
                    period=d.period,
                    category=d.category,
                    amount=d.amount,
                    amount_fmt=_rub(d.amount),
                    is_paid=d.is_paid,
                )
                for d in debt_rows
            ]

            col_rows = session.exec(
                select(Collection)
                .where(
                    Collection.entrance_id == self.entrance_id,
                    Collection.is_active == True,  # noqa: E712
                )
                .order_by(Collection.created_at.desc())
            ).all()
            items = []
            for c in col_rows:
                collected = self._collected_amount(session, c.id)
                mine = session.exec(
                    select(CollectionPayment).where(
                        CollectionPayment.collection_id == c.id,
                        CollectionPayment.resident_id == self.user_id,
                    )
                ).all()
                my_total = sum(p.amount for p in mine if p.status == "succeeded")
                pending = any(p.status == "pending" for p in mine)
                remaining = max(c.target_amount - collected, 0)
                items.append(
                    CollectionItem(
                        id=c.id,
                        entrance_id=c.entrance_id,
                        entrance_number=0,
                        title=c.title,
                        description=c.description,
                        category=c.category,
                        target_amount=c.target_amount,
                        target_fmt=_rub(c.target_amount),
                        collected_amount=collected,
                        collected_fmt=_rub(collected),
                        remaining=remaining,
                        remaining_fmt=_rub(remaining),
                        progress_pct=self._pct(collected, c.target_amount),
                        is_active=c.is_active,
                        my_contribution=my_total,
                        my_contribution_fmt=_rub(my_total),
                        my_payment_pending=pending,
                    )
                )
            self.my_collections = items

    @rx.event
    async def pay_collection(self, collection_id: int, amount: float):
        self.pay_error = ""
        if amount <= 0:
            self.pay_error = "Сбор уже закрыт"
            return
        with get_session() as session:
            collection = session.get(Collection, collection_id)
            if not collection or not collection.is_active:
                self.pay_error = "Сбор недоступен"
                return
            payment_row = CollectionPayment(
                collection_id=collection_id,
                resident_id=self.user_id,
                resident_name=self.display_name,
                amount=amount,
                status="pending",
            )
            session.add(payment_row)
            session.commit()
            session.refresh(payment_row)
            payment_row_id = payment_row.id
            title = collection.title

        try:
            result = await create_payment(
                amount=amount,
                description=f"Домовод: {title}",
                return_url=f"{APP_BASE_URL}/app",
            )
        except PaymentError as exc:
            self.pay_error = f"Ошибка платёжного шлюза: {exc}"
            with get_session() as session:
                p = session.get(CollectionPayment, payment_row_id)
                if p:
                    p.status = "canceled"
                    session.add(p)
                    session.commit()
            return

        with get_session() as session:
            p = session.get(CollectionPayment, payment_row_id)
            if p:
                p.yk_payment_id = result.get("id", "")
                session.add(p)
                session.commit()

        confirmation_url: Optional[str] = (
            result.get("confirmation", {}) or {}
        ).get("confirmation_url")
        self.paying_collection_id = payment_row_id
        yield FinanceState.load_resident_finance
        yield FinanceState.poll_payment(payment_row_id)
        if confirmation_url:
            # Same-tab navigation to the payment page. A new-tab redirect
            # (is_external=True) here gets blocked by browser popup blockers
            # because it fires after a server round-trip, not synchronously
            # inside the click handler.
            yield rx.redirect(confirmation_url)

    @rx.event
    def stop_live(self):
        self.is_live = False

    @rx.event(background=True)
    async def start_live(self):
        """Периодически подтягивает долги/сборы, чтобы платежи жителей и
        начисления УК были видны другой стороне без обновления страницы."""
        async with self:
            if self.is_live:
                return
            self.is_live = True
        try:
            while True:
                await asyncio.sleep(POLL_INTERVAL)
                async with self:
                    if not self.is_live:
                        return
                    if self.is_uk:
                        yield FinanceState.load_uk_finance
                    elif self.is_resident:
                        yield FinanceState.load_resident_finance
        finally:
            async with self:
                self.is_live = False

    @rx.event(background=True)
    async def poll_payment(self, payment_row_id: int):
        for _ in range(40):
            await asyncio.sleep(POLL_INTERVAL)
            with get_session() as session:
                p = session.get(CollectionPayment, payment_row_id)
                if not p or not p.yk_payment_id:
                    return
                yk_id = p.yk_payment_id
                done = p.status in ("succeeded", "canceled")
            if done:
                return
            try:
                status = await get_payment_status(yk_id)
            except PaymentError:
                continue
            yk_status = status.get("status")
            if yk_status in ("succeeded", "canceled"):
                with get_session() as session:
                    p = session.get(CollectionPayment, payment_row_id)
                    if p:
                        p.status = yk_status
                        session.add(p)
                        session.commit()
                async with self:
                    yield FinanceState.load_resident_finance
                return
