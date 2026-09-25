"""Инициативы и опросы жителей подъезда (голосование «я за»)."""

from __future__ import annotations

from typing import List

import reflex as rx
from pydantic import BaseModel
from sqlmodel import select

from .db import get_session
from .models import Initiative, InitiativeVote, Poll, PollVote
from .setters import make_setter
from .state import AuthState


class InitiativeItem(BaseModel):
    id: int
    title: str
    description: str
    votes: int
    needed_count: int
    i_voted: bool


class PollItem(BaseModel):
    id: int
    title: str
    description: str
    votes: int
    i_voted: bool


class CommunityState(AuthState):
    initiatives: List[InitiativeItem] = []
    completed_initiatives: List[InitiativeItem] = []
    polls: List[PollItem] = []
    completed_polls: List[PollItem] = []

    # L02/L03: списки «Все инициативы»/«Все опросы» — "" скрыт, иначе вкладка.
    initiatives_list_view: str = ""
    polls_list_view: str = ""

    new_initiative_title: str = ""
    new_initiative_description: str = ""
    new_initiative_needed: str = ""
    initiative_error: str = ""

    new_poll_title: str = ""
    new_poll_description: str = ""
    poll_error: str = ""

    set_new_initiative_title = make_setter("new_initiative_title")
    set_new_initiative_description = make_setter("new_initiative_description")
    set_new_initiative_needed = make_setter("new_initiative_needed")
    set_new_poll_title = make_setter("new_poll_title")
    set_new_poll_description = make_setter("new_poll_description")

    # ---------------- загрузка ----------------

    @rx.event
    def load_community(self):
        if not int(self.viewing_entrance_id or 0):
            self.initiatives = []
            self.completed_initiatives = []
            self.polls = []
            self.completed_polls = []
            return
        with get_session() as session:
            initiative_rows = session.exec(
                select(Initiative)
                .where(Initiative.entrance_id == int(self.viewing_entrance_id))
                .order_by(Initiative.created_at.desc())
            ).all()
            init_items = []
            completed_init_items = []
            for i in initiative_rows:
                votes = session.exec(
                    select(InitiativeVote).where(InitiativeVote.initiative_id == i.id)
                ).all()
                item = InitiativeItem(
                    id=i.id,
                    title=i.title,
                    description=i.description,
                    votes=len(votes),
                    needed_count=i.needed_count,
                    i_voted=any(v.resident_id == int(self.user_id) for v in votes),
                )
                (init_items if i.is_active else completed_init_items).append(item)
            self.initiatives = init_items
            self.completed_initiatives = completed_init_items

            poll_rows = session.exec(
                select(Poll)
                .where(Poll.entrance_id == int(self.viewing_entrance_id))
                .order_by(Poll.created_at.desc())
            ).all()
            poll_items = []
            completed_poll_items = []
            for p in poll_rows:
                votes = session.exec(select(PollVote).where(PollVote.poll_id == p.id)).all()
                item = PollItem(
                    id=p.id,
                    title=p.title,
                    description=p.description,
                    votes=len(votes),
                    i_voted=any(v.resident_id == int(self.user_id) for v in votes),
                )
                (poll_items if p.is_active else completed_poll_items).append(item)
            self.polls = poll_items
            self.completed_polls = completed_poll_items

    @rx.event
    def open_initiatives_list(self):
        self.initiatives_list_view = "active"

    @rx.event
    def close_initiatives_list(self):
        self.initiatives_list_view = ""

    @rx.event
    def set_initiatives_list_tab(self, tab: str):
        self.initiatives_list_view = tab

    @rx.event
    def set_initiatives_list_open(self, is_open: bool):
        if not is_open:
            self.initiatives_list_view = ""

    @rx.event
    def open_polls_list(self):
        self.polls_list_view = "active"

    @rx.event
    def close_polls_list(self):
        self.polls_list_view = ""

    @rx.event
    def set_polls_list_tab(self, tab: str):
        self.polls_list_view = tab

    @rx.event
    def set_polls_list_open(self, is_open: bool):
        if not is_open:
            self.polls_list_view = ""

    # ---------------- инициативы ----------------

    @rx.event
    def create_initiative(self):
        self.initiative_error = ""
        title = self.new_initiative_title.strip()
        if not title:
            self.initiative_error = "Укажите название"
            return
        try:
            needed = int(self.new_initiative_needed or 0)
        except ValueError:
            needed = 0
        with get_session() as session:
            session.add(
                Initiative(
                    entrance_id=int(self.viewing_entrance_id),
                    tenant_id=int(self.tenant_id),
                    title=title,
                    description=self.new_initiative_description.strip(),
                    needed_count=needed,
                    author_name=self.display_name,
                )
            )
            session.commit()
        self.new_initiative_title = ""
        self.new_initiative_description = ""
        self.new_initiative_needed = ""
        return CommunityState.load_community

    @rx.event
    def toggle_initiative_vote(self, initiative_id: int):
        if not self.is_resident:
            return
        with get_session() as session:
            existing = session.exec(
                select(InitiativeVote).where(
                    InitiativeVote.initiative_id == initiative_id,
                    InitiativeVote.resident_id == int(self.user_id),
                )
            ).first()
            if existing:
                session.delete(existing)
            else:
                session.add(InitiativeVote(initiative_id=initiative_id, resident_id=int(self.user_id)))
            session.commit()
        return CommunityState.load_community

    # ---------------- опросы ----------------

    @rx.event
    def create_poll(self):
        self.poll_error = ""
        title = self.new_poll_title.strip()
        if not title:
            self.poll_error = "Укажите название"
            return
        with get_session() as session:
            session.add(
                Poll(
                    entrance_id=int(self.viewing_entrance_id),
                    tenant_id=int(self.tenant_id),
                    title=title,
                    description=self.new_poll_description.strip(),
                    author_name=self.display_name,
                )
            )
            session.commit()
        self.new_poll_title = ""
        self.new_poll_description = ""
        return CommunityState.load_community

    @rx.event
    def toggle_poll_vote(self, poll_id: int):
        if not self.is_resident:
            return
        with get_session() as session:
            existing = session.exec(
                select(PollVote).where(
                    PollVote.poll_id == poll_id,
                    PollVote.resident_id == int(self.user_id),
                )
            ).first()
            if existing:
                session.delete(existing)
            else:
                session.add(PollVote(poll_id=poll_id, resident_id=int(self.user_id)))
            session.commit()
        return CommunityState.load_community
