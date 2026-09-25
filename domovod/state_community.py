"""Инициативы (голосование «я за») и опросы с вариантами ответа подъезда."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import reflex as rx
from pydantic import BaseModel
from sqlmodel import select

from .db import get_session
from .models import Initiative, InitiativeVote, Poll, PollOption, PollVote, Resident
from .setters import make_setter
from .state import AuthState


def _fmt_date(value) -> str:
    return value.strftime("%d.%m.%Y") if value else ""


def _parse_date(value: str):
    value = value.strip()
    if not value:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


class InitiativeItem(BaseModel):
    id: int
    title: str
    description: str
    votes: int
    needed_count: int
    i_voted: bool
    author_name: str = ""
    event_date: str = ""
    progress_pct: int = 0
    proposed_by_name: str = ""
    rejection_reason: str = ""


class PollOptionItem(BaseModel):
    id: int
    label: str
    votes: int
    pct: int
    is_mine: bool


class PollItem(BaseModel):
    id: int
    title: str
    description: str
    author_name: str = ""
    end_date_fmt: str = ""
    allow_multiple: bool = False
    allow_vote_change: bool = True
    is_active: bool = True
    options: List[PollOptionItem] = []
    total_voters: int = 0
    i_voted: bool = False
    proposed_by_name: str = ""
    rejection_reason: str = ""


class CommunityState(AuthState):
    initiatives: List[InitiativeItem] = []
    completed_initiatives: List[InitiativeItem] = []
    proposed_initiatives: List[InitiativeItem] = []
    polls: List[PollItem] = []
    completed_polls: List[PollItem] = []
    proposed_polls: List[PollItem] = []

    # L02/L03: списки «Все инициативы»/«Все опросы» — "" скрыт, иначе вкладка.
    initiatives_list_view: str = ""
    polls_list_view: str = ""
    show_proposed_initiatives_dialog: bool = False
    show_proposed_polls_dialog: bool = False

    new_initiative_title: str = ""
    new_initiative_description: str = ""
    new_initiative_needed: str = ""
    new_initiative_event_date: str = ""
    initiative_error: str = ""

    new_poll_title: str = ""
    new_poll_description: str = ""
    new_poll_option_1: str = ""
    new_poll_option_2: str = ""
    new_poll_option_3: str = ""
    new_poll_option_4: str = ""
    new_poll_allow_multiple: bool = False
    new_poll_end_date: str = ""
    poll_error: str = ""

    # --- F05/F06: мастер предложения инициативы жителем ---
    propose_initiative_title: str = ""
    propose_initiative_description: str = ""
    propose_initiative_needed: str = ""
    propose_initiative_event_date: str = ""
    propose_initiative_error: str = ""

    # --- F07–F09: мастер предложения опроса жителем (до 10 вариантов) ---
    propose_poll_title: str = ""
    propose_poll_description: str = ""
    propose_poll_options: List[str] = ["", ""]
    propose_poll_allow_multiple: bool = False
    propose_poll_allow_vote_change: bool = True
    propose_poll_end_date: str = ""
    propose_poll_error: str = ""

    # I01: инициатива, открытая в детальной карточке.
    open_initiative_id: int = 0

    # Q01–Q05: опрос, открытый в детальной карточке. poll_editing — режим
    # выбора варианта (до отправки), иначе показываются результаты.
    open_poll_id: int = 0
    poll_editing: bool = False
    poll_selected_option_ids: List[int] = []

    set_new_initiative_title = make_setter("new_initiative_title")
    set_new_initiative_description = make_setter("new_initiative_description")
    set_new_initiative_needed = make_setter("new_initiative_needed")
    set_new_initiative_event_date = make_setter("new_initiative_event_date")
    set_new_poll_title = make_setter("new_poll_title")
    set_new_poll_description = make_setter("new_poll_description")
    set_new_poll_option_1 = make_setter("new_poll_option_1")
    set_new_poll_option_2 = make_setter("new_poll_option_2")
    set_new_poll_option_3 = make_setter("new_poll_option_3")
    set_new_poll_option_4 = make_setter("new_poll_option_4")
    set_new_poll_allow_multiple = make_setter("new_poll_allow_multiple")
    set_new_poll_end_date = make_setter("new_poll_end_date")

    set_propose_initiative_title = make_setter("propose_initiative_title")
    set_propose_initiative_description = make_setter("propose_initiative_description")
    set_propose_initiative_needed = make_setter("propose_initiative_needed")
    set_propose_initiative_event_date = make_setter("propose_initiative_event_date")

    set_propose_poll_title = make_setter("propose_poll_title")
    set_propose_poll_description = make_setter("propose_poll_description")
    set_propose_poll_allow_multiple = make_setter("propose_poll_allow_multiple")
    set_propose_poll_allow_vote_change = make_setter("propose_poll_allow_vote_change")
    set_propose_poll_end_date = make_setter("propose_poll_end_date")

    # ---------------- загрузка ----------------

    @rx.event
    def load_community(self):
        if not int(self.viewing_entrance_id or 0):
            self.initiatives = []
            self.completed_initiatives = []
            self.proposed_initiatives = []
            self.polls = []
            self.completed_polls = []
            self.proposed_polls = []
            return
        with get_session() as session:
            resident_rows = session.exec(
                select(Resident).where(Resident.entrance_id == int(self.viewing_entrance_id))
            ).all()
            resident_map = {r.id: r for r in resident_rows}

            initiative_rows = session.exec(
                select(Initiative)
                .where(Initiative.entrance_id == int(self.viewing_entrance_id))
                .order_by(Initiative.created_at.desc())
            ).all()
            init_items, completed_init_items, proposed_init_items = [], [], []
            for i in initiative_rows:
                votes = session.exec(
                    select(InitiativeVote).where(InitiativeVote.initiative_id == i.id)
                ).all()
                needed = i.needed_count
                pct = min(100, int(len(votes) / needed * 100)) if needed > 0 else 0
                proposer = resident_map.get(i.proposed_by_resident_id or 0)
                item = InitiativeItem(
                    id=i.id,
                    title=i.title,
                    description=i.description,
                    votes=len(votes),
                    needed_count=needed,
                    i_voted=any(v.resident_id == int(self.user_id) for v in votes),
                    author_name=i.author_name,
                    event_date=i.event_date,
                    progress_pct=pct,
                    proposed_by_name=proposer.full_name if proposer else "",
                    rejection_reason=i.rejection_reason,
                )
                if i.status == "proposed":
                    proposed_init_items.append(item)
                elif i.status == "published":
                    (init_items if i.is_active else completed_init_items).append(item)
            self.initiatives = init_items
            self.completed_initiatives = completed_init_items
            self.proposed_initiatives = proposed_init_items

            poll_rows = session.exec(
                select(Poll)
                .where(Poll.entrance_id == int(self.viewing_entrance_id))
                .order_by(Poll.created_at.desc())
            ).all()
            poll_items, completed_poll_items, proposed_poll_items = [], [], []
            for p in poll_rows:
                option_rows = session.exec(
                    select(PollOption).where(PollOption.poll_id == p.id).order_by(PollOption.order)
                ).all()
                vote_rows = session.exec(select(PollVote).where(PollVote.poll_id == p.id)).all()
                total_voters = len({v.resident_id for v in vote_rows})
                my_option_ids = {
                    v.option_id for v in vote_rows if v.resident_id == int(self.user_id)
                }
                option_items = []
                for o in option_rows:
                    o_votes = sum(1 for v in vote_rows if v.option_id == o.id)
                    pct = int(o_votes / total_voters * 100) if total_voters > 0 else 0
                    option_items.append(
                        PollOptionItem(
                            id=o.id,
                            label=o.label,
                            votes=o_votes,
                            pct=pct,
                            is_mine=o.id in my_option_ids,
                        )
                    )
                proposer = resident_map.get(p.proposed_by_resident_id or 0)
                item = PollItem(
                    id=p.id,
                    title=p.title,
                    description=p.description,
                    author_name=p.author_name,
                    end_date_fmt=_fmt_date(p.end_date),
                    allow_multiple=p.allow_multiple,
                    allow_vote_change=p.allow_vote_change,
                    is_active=p.is_active,
                    options=option_items,
                    total_voters=total_voters,
                    i_voted=bool(my_option_ids),
                    proposed_by_name=proposer.full_name if proposer else "",
                    rejection_reason=p.rejection_reason,
                )
                if p.status == "proposed":
                    proposed_poll_items.append(item)
                elif p.status == "published":
                    (poll_items if p.is_active else completed_poll_items).append(item)
            self.polls = poll_items
            self.completed_polls = completed_poll_items
            self.proposed_polls = proposed_poll_items

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

    @rx.var
    def open_initiative_item(self) -> Optional[InitiativeItem]:
        target = int(self.open_initiative_id or 0)
        if not target:
            return None
        for i in self.initiatives:
            if i.id == target:
                return i
        for i in self.completed_initiatives:
            if i.id == target:
                return i
        return None

    @rx.event
    def open_initiative(self, initiative_id: int):
        self.open_initiative_id = initiative_id

    @rx.event
    def close_initiative(self):
        self.open_initiative_id = 0

    @rx.event
    def set_initiative_dialog_open(self, is_open: bool):
        if not is_open:
            self.open_initiative_id = 0

    @rx.var
    def open_poll_item(self) -> Optional[PollItem]:
        target = int(self.open_poll_id or 0)
        if not target:
            return None
        for p in self.polls:
            if p.id == target:
                return p
        for p in self.completed_polls:
            if p.id == target:
                return p
        return None

    @rx.event
    def open_poll(self, poll_id: int):
        self.open_poll_id = poll_id
        poll = self.open_poll_item
        self.poll_editing = not (poll and poll.i_voted)
        self.poll_selected_option_ids = [o.id for o in poll.options if o.is_mine] if poll else []

    @rx.event
    def close_poll(self):
        self.open_poll_id = 0
        self.poll_editing = False
        self.poll_selected_option_ids = []

    @rx.event
    def set_poll_dialog_open(self, is_open: bool):
        if not is_open:
            self.open_poll_id = 0
            self.poll_editing = False
            self.poll_selected_option_ids = []

    @rx.event
    def start_change_vote(self):
        self.poll_editing = True

    @rx.event
    def toggle_poll_option_selection(self, option_id: int):
        poll = self.open_poll_item
        if not poll:
            return
        if poll.allow_multiple:
            if option_id in self.poll_selected_option_ids:
                self.poll_selected_option_ids = [
                    i for i in self.poll_selected_option_ids if i != option_id
                ]
            else:
                self.poll_selected_option_ids = self.poll_selected_option_ids + [option_id]
        else:
            self.poll_selected_option_ids = [option_id]

    @rx.event
    def submit_poll_vote(self):
        if not self.is_resident or not self.poll_selected_option_ids:
            return
        poll_id = self.open_poll_id
        with get_session() as session:
            existing = session.exec(
                select(PollVote).where(
                    PollVote.poll_id == poll_id,
                    PollVote.resident_id == int(self.user_id),
                )
            ).all()
            for v in existing:
                session.delete(v)
            for option_id in self.poll_selected_option_ids:
                session.add(
                    PollVote(poll_id=poll_id, option_id=option_id, resident_id=int(self.user_id))
                )
            session.commit()
        self.poll_editing = False
        return CommunityState.load_community

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
                    event_date=self.new_initiative_event_date.strip(),
                )
            )
            session.commit()
        self.new_initiative_title = ""
        self.new_initiative_description = ""
        self.new_initiative_needed = ""
        self.new_initiative_event_date = ""
        return CommunityState.load_community

    @rx.var
    def propose_initiative_step1_valid(self) -> bool:
        return bool(self.propose_initiative_title.strip())

    @rx.event
    def propose_initiative(self):
        """F06 «Отправить администратору» — заявка уходит УК на модерацию."""
        self.propose_initiative_error = ""
        title = self.propose_initiative_title.strip()
        description = self.propose_initiative_description.strip()
        if not title:
            self.propose_initiative_error = "Укажите название"
            return
        if not description:
            self.propose_initiative_error = "Укажите место, что взять, длительность"
            return
        try:
            needed = int(self.propose_initiative_needed or 0)
        except ValueError:
            needed = 0
        with get_session() as session:
            session.add(
                Initiative(
                    entrance_id=int(self.viewing_entrance_id),
                    tenant_id=int(self.tenant_id),
                    title=title,
                    description=description,
                    needed_count=needed,
                    author_name=self.display_name,
                    event_date=self.propose_initiative_event_date.strip(),
                    status="proposed",
                    is_active=False,
                    proposed_by_resident_id=int(self.user_id),
                )
            )
            session.commit()
        self.propose_initiative_title = ""
        self.propose_initiative_description = ""
        self.propose_initiative_needed = ""
        self.propose_initiative_event_date = ""
        self.create_flow_done = True
        return CommunityState.load_community

    @rx.event
    def start_edit_initiative(self, initiative_id: int):
        """F15 «Исправить и отправить» — переносит поля отклонённой
        инициативы обратно в мастер (F05)."""
        with get_session() as session:
            i = session.get(Initiative, initiative_id)
            if not i or i.proposed_by_resident_id != int(self.user_id) or i.status != "rejected":
                return
            self.propose_initiative_title = i.title
            self.propose_initiative_description = i.description
            self.propose_initiative_needed = str(i.needed_count) if i.needed_count else ""
            self.propose_initiative_event_date = i.event_date
        self.pick_create_flow_kind("initiative")

    @rx.event
    def open_proposed_initiatives_dialog(self):
        self.show_proposed_initiatives_dialog = True

    @rx.event
    def close_proposed_initiatives_dialog(self):
        self.show_proposed_initiatives_dialog = False

    @rx.event
    def set_proposed_initiatives_dialog_open(self, is_open: bool):
        self.show_proposed_initiatives_dialog = is_open

    @rx.event
    def publish_initiative(self, initiative_id: int):
        with get_session() as session:
            i = session.get(Initiative, initiative_id)
            if i and i.tenant_id == int(self.tenant_id) and i.status == "proposed":
                i.status = "published"
                i.is_active = True
                session.add(i)
                session.commit()
        return CommunityState.load_community

    @rx.event
    def reject_initiative(self, initiative_id: int, reason: str):
        with get_session() as session:
            i = session.get(Initiative, initiative_id)
            if i and i.tenant_id == int(self.tenant_id) and i.status == "proposed":
                i.status = "rejected"
                i.rejection_reason = reason.strip() or "Причина не указана"
                i.is_active = False
                session.add(i)
                session.commit()
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
        options = [
            o.strip()
            for o in (
                self.new_poll_option_1,
                self.new_poll_option_2,
                self.new_poll_option_3,
                self.new_poll_option_4,
            )
            if o.strip()
        ]
        if len(options) < 2:
            self.poll_error = "Добавьте минимум два варианта ответа"
            return
        with get_session() as session:
            poll = Poll(
                entrance_id=int(self.viewing_entrance_id),
                tenant_id=int(self.tenant_id),
                title=title,
                description=self.new_poll_description.strip(),
                author_name=self.display_name,
                end_date=_parse_date(self.new_poll_end_date),
                allow_multiple=self.new_poll_allow_multiple,
            )
            session.add(poll)
            session.commit()
            session.refresh(poll)
            for idx, label in enumerate(options):
                session.add(PollOption(poll_id=poll.id, label=label, order=idx))
            session.commit()
        self.new_poll_title = ""
        self.new_poll_description = ""
        self.new_poll_option_1 = ""
        self.new_poll_option_2 = ""
        self.new_poll_option_3 = ""
        self.new_poll_option_4 = ""
        self.new_poll_allow_multiple = False
        self.new_poll_end_date = ""
        return CommunityState.load_community

    # --- F07–F09: мастер предложения опроса жителем ---

    @rx.event
    def add_propose_poll_option(self):
        if len(self.propose_poll_options) < 10:
            self.propose_poll_options = self.propose_poll_options + [""]

    @rx.event
    def remove_propose_poll_option(self, index: int):
        if len(self.propose_poll_options) > 2:
            self.propose_poll_options = [
                o for idx, o in enumerate(self.propose_poll_options) if idx != index
            ]

    @rx.event
    def set_propose_poll_option(self, index: int, value: str):
        options = list(self.propose_poll_options)
        if 0 <= index < len(options):
            options[index] = value
            self.propose_poll_options = options

    @rx.var
    def propose_poll_step1_valid(self) -> bool:
        title_ok = bool(self.propose_poll_title.strip())
        filled = [o.strip() for o in self.propose_poll_options if o.strip()]
        return title_ok and len(filled) >= 2 and len(filled) == len(set(filled))

    @rx.event
    def propose_poll(self):
        """F09 «Отправить администратору» — заявка уходит УК на модерацию."""
        self.propose_poll_error = ""
        title = self.propose_poll_title.strip()
        options = [o.strip() for o in self.propose_poll_options if o.strip()]
        if not title:
            self.propose_poll_error = "Укажите вопрос"
            return
        if len(options) < 2:
            self.propose_poll_error = "Добавьте минимум два варианта ответа"
            return
        if len(options) != len(set(options)):
            self.propose_poll_error = "Варианты не должны повторяться"
            return
        with get_session() as session:
            poll = Poll(
                entrance_id=int(self.viewing_entrance_id),
                tenant_id=int(self.tenant_id),
                title=title,
                description=self.propose_poll_description.strip(),
                author_name=self.display_name,
                end_date=_parse_date(self.propose_poll_end_date),
                allow_multiple=self.propose_poll_allow_multiple,
                allow_vote_change=self.propose_poll_allow_vote_change,
                status="proposed",
                is_active=False,
                proposed_by_resident_id=int(self.user_id),
            )
            session.add(poll)
            session.commit()
            session.refresh(poll)
            for idx, label in enumerate(options):
                session.add(PollOption(poll_id=poll.id, label=label, order=idx))
            session.commit()
        self.propose_poll_title = ""
        self.propose_poll_description = ""
        self.propose_poll_options = ["", ""]
        self.propose_poll_allow_multiple = False
        self.propose_poll_allow_vote_change = True
        self.propose_poll_end_date = ""
        self.create_flow_done = True
        return CommunityState.load_community

    @rx.event
    def open_proposed_polls_dialog(self):
        self.show_proposed_polls_dialog = True

    @rx.event
    def close_proposed_polls_dialog(self):
        self.show_proposed_polls_dialog = False

    @rx.event
    def set_proposed_polls_dialog_open(self, is_open: bool):
        self.show_proposed_polls_dialog = is_open

    @rx.event
    def publish_poll(self, poll_id: int):
        with get_session() as session:
            p = session.get(Poll, poll_id)
            if p and p.tenant_id == int(self.tenant_id) and p.status == "proposed":
                p.status = "published"
                p.is_active = True
                session.add(p)
                session.commit()
        return CommunityState.load_community

    @rx.event
    def reject_poll(self, poll_id: int, reason: str):
        with get_session() as session:
            p = session.get(Poll, poll_id)
            if p and p.tenant_id == int(self.tenant_id) and p.status == "proposed":
                p.status = "rejected"
                p.rejection_reason = reason.strip() or "Причина не указана"
                p.is_active = False
                session.add(p)
                session.commit()
        return CommunityState.load_community

    @rx.event
    def start_edit_poll(self, poll_id: int):
        """F15 «Исправить и отправить» — переносит поля отклонённого
        опроса обратно в мастер (F07)."""
        with get_session() as session:
            p = session.get(Poll, poll_id)
            if not p or p.proposed_by_resident_id != int(self.user_id) or p.status != "rejected":
                return
            option_rows = session.exec(
                select(PollOption).where(PollOption.poll_id == poll_id).order_by(PollOption.order)
            ).all()
            self.propose_poll_title = p.title
            self.propose_poll_description = p.description
            self.propose_poll_options = [o.label for o in option_rows] or ["", ""]
            self.propose_poll_allow_multiple = p.allow_multiple
            self.propose_poll_allow_vote_change = p.allow_vote_change
            self.propose_poll_end_date = _fmt_date(p.end_date)
        self.pick_create_flow_kind("poll")
