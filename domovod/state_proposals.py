"""«Мои предложения» (F14–F16) — статус заявок жителя на модерации у УК,
и общий диалог отклонения с причиной для УК (используется всеми тремя
типами: сборы, инициативы, опросы)."""

from __future__ import annotations

from typing import List

import reflex as rx
from pydantic import BaseModel
from sqlmodel import select

from .db import get_session
from .models import Collection, Initiative, Poll
from .setters import make_setter
from .state import AuthState
from .state_community import CommunityState
from .state_finance import FinanceState

_MONTHS = [
    "", "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]


def _fmt_ru_date(value) -> str:
    if not value:
        return ""
    return f"{value.day} {_MONTHS[value.month]}"


class MyProposalItem(BaseModel):
    id: int
    kind: str  # "collection" | "initiative" | "poll"
    kind_label: str
    title: str
    submitted_fmt: str
    status: str  # "proposed" | "published" | "rejected"
    rejection_reason: str = ""


class ProposalsState(AuthState):
    my_proposals: List[MyProposalItem] = []
    show_my_proposals: bool = False

    # УК: общий диалог «Отклонить» с причиной — используется для всех
    # трёх типов, чтобы не дублировать один и тот же попап трижды.
    reject_target_kind: str = ""
    reject_target_id: int = 0
    reject_target_title: str = ""
    reject_reason_input: str = ""

    @rx.event
    def load_my_proposals(self):
        if not self.user_id:
            self.my_proposals = []
            return
        rows = []
        with get_session() as session:
            cols = session.exec(
                select(Collection).where(Collection.proposed_by_resident_id == int(self.user_id))
            ).all()
            for c in cols:
                rows.append((c.created_at, "collection", "Сбор", c.id, c.title, c.status, c.rejection_reason))
            inits = session.exec(
                select(Initiative).where(Initiative.proposed_by_resident_id == int(self.user_id))
            ).all()
            for i in inits:
                rows.append((i.created_at, "initiative", "Инициатива", i.id, i.title, i.status, i.rejection_reason))
            polls = session.exec(
                select(Poll).where(Poll.proposed_by_resident_id == int(self.user_id))
            ).all()
            for p in polls:
                rows.append((p.created_at, "poll", "Опрос", p.id, p.title, p.status, p.rejection_reason))
        rows.sort(key=lambda r: r[0], reverse=True)
        self.my_proposals = [
            MyProposalItem(
                id=row_id,
                kind=kind,
                kind_label=kind_label,
                title=title,
                submitted_fmt=_fmt_ru_date(created_at),
                status=status,
                rejection_reason=reason,
            )
            for created_at, kind, kind_label, row_id, title, status, reason in rows
        ]

    @rx.event
    def open_my_proposals(self):
        self.show_my_proposals = True
        return ProposalsState.load_my_proposals

    @rx.event
    def close_my_proposals(self):
        self.show_my_proposals = False

    @rx.event
    def set_my_proposals_open(self, is_open: bool):
        self.show_my_proposals = is_open

    @rx.event
    def withdraw_proposal(self, kind: str, proposal_id: int):
        """F14 «Отозвать предложение» — убирает заявку из очереди на
        модерацию; повторно предложить можно будет заново через мастер."""
        model = {"collection": Collection, "initiative": Initiative, "poll": Poll}.get(kind)
        if model is None:
            return
        with get_session() as session:
            row = session.get(model, proposal_id)
            if row and row.proposed_by_resident_id == int(self.user_id) and row.status == "proposed":
                session.delete(row)
                session.commit()
        return ProposalsState.load_my_proposals

    @rx.event
    def start_edit_rejected(self, kind: str, proposal_id: int):
        """F15 «Исправить и отправить» — дальше решает нужный мастер."""
        if kind == "collection":
            return FinanceState.start_edit_collection(proposal_id)
        if kind == "initiative":
            return CommunityState.start_edit_initiative(proposal_id)
        if kind == "poll":
            return CommunityState.start_edit_poll(proposal_id)

    # ---------------- УК: отклонить с причиной ----------------

    @rx.event
    def open_reject(self, kind: str, proposal_id: int, title: str):
        self.reject_target_kind = kind
        self.reject_target_id = proposal_id
        self.reject_target_title = title
        self.reject_reason_input = ""

    @rx.event
    def close_reject(self):
        self.reject_target_kind = ""
        self.reject_target_id = 0
        self.reject_target_title = ""
        self.reject_reason_input = ""

    @rx.event
    def set_reject_dialog_open(self, is_open: bool):
        if not is_open:
            self.reject_target_kind = ""
            self.reject_target_id = 0
            self.reject_target_title = ""
            self.reject_reason_input = ""

    set_reject_reason_input = make_setter("reject_reason_input")

    @rx.event
    def confirm_reject(self):
        kind, target_id, reason = self.reject_target_kind, self.reject_target_id, self.reject_reason_input
        self.reject_target_kind = ""
        self.reject_target_id = 0
        self.reject_target_title = ""
        self.reject_reason_input = ""
        self.management_view = "proposals"
        if kind == "collection":
            return FinanceState.reject_collection(target_id, reason)
        if kind == "initiative":
            return CommunityState.reject_initiative(target_id, reason)
        if kind == "poll":
            return CommunityState.reject_poll(target_id, reason)
