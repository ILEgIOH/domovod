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
    polls: List[PollItem] = []

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
            self.polls = []
            return
        with get_session() as session:
            initiative_rows = session.exec(
                select(Initiative)
                .where(Initiative.entrance_id == int(self.viewing_entrance_id), Initiative.is_active == True)  # noqa: E712
                .order_by(Initiative.created_at.desc())
            ).all()
            init_items = []
            for i in initiative_rows:
                votes = session.exec(
                    select(InitiativeVote).where(InitiativeVote.initiative_id == i.id)
                ).all()
                init_items.append(
                    InitiativeItem(
                        id=i.id,
                        title=i.title,
                        description=i.description,
                        votes=len(votes),
                        needed_count=i.needed_count,
                        i_voted=any(v.resident_id == int(self.user_id) for v in votes),
                    )
                )
            self.initiatives = init_items

            poll_rows = session.exec(
                select(Poll)
                .where(Poll.entrance_id == int(self.viewing_entrance_id), Poll.is_active == True)  # noqa: E712
                .order_by(Poll.created_at.desc())
            ).all()
            poll_items = []
            for p in poll_rows:
                votes = session.exec(select(PollVote).where(PollVote.poll_id == p.id)).all()
                poll_items.append(
                    PollItem(
                        id=p.id,
                        title=p.title,
                        description=p.description,
                        votes=len(votes),
                        i_voted=any(v.resident_id == int(self.user_id) for v in votes),
                    )
                )
            self.polls = poll_items

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
