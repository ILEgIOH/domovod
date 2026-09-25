"""Управление домами, подъездами и жителями со стороны УК."""

from __future__ import annotations

import asyncio
import json
from typing import List, Optional

import reflex as rx
from pydantic import BaseModel
from sqlmodel import select

from .db import get_session
from .models import Building, Entrance, Resident
from .models import gen_invite_code
from .qr import build_join_url, qr_data_uri
from .setters import make_setter
from .state import AuthState
from .state_finance import FinanceState


class BuildingItem(BaseModel):
    id: int
    address: str


class EntranceItem(BaseModel):
    id: int
    building_id: int
    building_address: str
    number: int
    invite_code: str
    invite_code_display: str
    residents_count: int
    join_url: str
    qr_data_uri: str


class ResidentItem(BaseModel):
    id: int
    full_name: str
    apartment: str
    phone: str
    entrance_number: int
    building_address: str


class UKAdminState(AuthState):
    buildings: List[BuildingItem] = []
    entrances: List[EntranceItem] = []
    residents: List[ResidentItem] = []

    new_building_address: str = ""
    new_entrance_building_id: str = ""
    new_entrance_number: str = ""
    admin_error: str = ""
    copied_entrance_id: int = 0
    is_live: bool = False
    selected_building_id: str = ""
    confirm_regenerate_entrance_id: int = 0

    # --- модальное окно «Пригласить соседей» (A03–A05), сразу после
    # создания дома: "" — скрыто, "code" — карточка с кодом, "qr" — QR.
    invite_modal_view: str = ""

    # --- вкладка «Управление» (M02/M03): "menu" — список разделов,
    # "proposals" — входящие предложения жильцов на модерации.
    management_view: str = "menu"
    proposal_filter: str = "all"  # "all" | "collection" | "initiative" | "poll"
    invite_code_copied: bool = False

    set_new_building_address = make_setter("new_building_address")
    set_new_entrance_building_id = make_setter("new_entrance_building_id")
    set_new_entrance_number = make_setter("new_entrance_number")
    set_selected_building_id = make_setter("selected_building_id")
    set_management_view = make_setter("management_view")
    set_proposal_filter = make_setter("proposal_filter")

    @rx.event
    def open_management_proposals(self):
        self.proposal_filter = "all"
        self.management_view = "proposals"

    @rx.var
    def visible_entrances(self) -> List[EntranceItem]:
        if not self.selected_building_id:
            return self.entrances
        try:
            bid = int(self.selected_building_id)
        except ValueError:
            return self.entrances
        return [e for e in self.entrances if e.building_id == bid]

    @rx.var
    def current_entrance(self) -> Optional[EntranceItem]:
        target = int(self.viewing_entrance_id or 0)
        for e in self.entrances:
            if e.id == target:
                return e
        return None

    @rx.var
    def invite_entrance(self) -> Optional[EntranceItem]:
        """Подъезд для модалки «Пригласить соседей» — сразу после
        создания дома он у тенанта ровно один."""
        return self.entrances[0] if self.entrances else None

    @rx.event
    def load_admin_data(self):
        if not self.tenant_id:
            return
        with get_session() as session:
            building_rows = session.exec(
                select(Building).where(Building.tenant_id == self.tenant_id)
            ).all()
            self.buildings = [
                BuildingItem(id=b.id, address=b.address) for b in building_rows
            ]
            entrance_rows = session.exec(
                select(Entrance).where(Entrance.tenant_id == self.tenant_id)
            ).all()
            building_map = {b.id: b.address for b in building_rows}
            origin = self.router.url.origin
            entrance_items = []
            resident_items = []
            for e in entrance_rows:
                count = len(
                    session.exec(
                        select(Resident).where(Resident.entrance_id == e.id)
                    ).all()
                )
                join_url = build_join_url(origin, e.invite_code)
                code = e.invite_code
                code_display = f"{code[:3]} – {code[3:]}" if len(code) == 6 else code
                entrance_items.append(
                    EntranceItem(
                        id=e.id,
                        building_id=e.building_id,
                        building_address=building_map.get(e.building_id, "?"),
                        number=e.number,
                        invite_code=e.invite_code,
                        invite_code_display=code_display,
                        residents_count=count,
                        join_url=join_url,
                        qr_data_uri=qr_data_uri(join_url),
                    )
                )
            self.entrances = entrance_items

            all_residents = session.exec(
                select(Resident).where(Resident.tenant_id == self.tenant_id)
            ).all()
            entrance_lookup = {e.id: e for e in entrance_rows}
            for r in all_residents:
                ent = entrance_lookup.get(r.entrance_id)
                resident_items.append(
                    ResidentItem(
                        id=r.id,
                        full_name=r.full_name,
                        apartment=r.apartment,
                        phone=r.phone or "—",
                        entrance_number=ent.number if ent else 0,
                        building_address=building_map.get(
                            ent.building_id, "?"
                        )
                        if ent
                        else "?",
                    )
                )
            self.residents = resident_items

        if not self.selected_building_id and self.buildings:
            self.selected_building_id = str(self.buildings[0].id)
        valid_entrance_ids = {e.id for e in self.entrances}
        if int(self.viewing_entrance_id or 0) not in valid_entrance_ids:
            self.viewing_entrance_id = self.entrances[0].id if self.entrances else 0

    @rx.event
    def add_building(self):
        self.admin_error = ""
        if not self.new_building_address.strip():
            self.admin_error = "Укажите адрес дома"
            return
        with get_session() as session:
            session.add(
                Building(tenant_id=self.tenant_id, address=self.new_building_address.strip())
            )
            session.commit()
        self.new_building_address = ""
        return UKAdminState.load_admin_data

    @rx.event
    def add_entrance(self):
        self.admin_error = ""
        if not self.new_entrance_building_id or not self.new_entrance_number:
            self.admin_error = "Выберите дом и укажите номер подъезда"
            return
        try:
            building_id = int(self.new_entrance_building_id)
            number = int(self.new_entrance_number)
        except ValueError:
            self.admin_error = "Некорректные данные"
            return
        with get_session() as session:
            session.add(
                Entrance(
                    building_id=building_id,
                    tenant_id=self.tenant_id,
                    number=number,
                )
            )
            session.commit()
        self.new_entrance_number = ""
        # Keep FinanceState.entrance_options (used by the "new collection"
        # form) in sync — it's loaded independently of UKAdminState.
        return [UKAdminState.load_admin_data, FinanceState.load_uk_finance]

    @rx.event
    def open_invite_after_create(self):
        """Once-эффект: сразу после «Создать дом» показывает A03 поверх
        пустого дома (флаг взводит AuthState.create_home_confirm)."""
        if self.show_invite_after_create:
            self.show_invite_after_create = False
            self.invite_modal_view = "code"

    @rx.event
    def close_invite_modal(self):
        self.invite_modal_view = ""

    @rx.event
    def set_invite_modal_open(self, is_open: bool):
        """on_open_change — закрытие по Esc/клику вне модалки."""
        if not is_open:
            self.invite_modal_view = ""

    @rx.event
    def show_invite_qr(self):
        self.invite_modal_view = "qr"

    @rx.event
    def back_or_close_invite(self):
        """Маленький шеврон «‹» вверху модалки: из QR (A05) — назад к коду
        (A03), из кода — закрывает модалку целиком (там уже верхний уровень)."""
        self.invite_modal_view = "code" if self.invite_modal_view == "qr" else ""

    @rx.event
    def copy_invite_code(self):
        entrance = self.invite_entrance
        if not entrance:
            return
        self.invite_code_copied = True
        return [
            rx.set_clipboard(entrance.invite_code_display),
            UKAdminState.reset_invite_copied,
        ]

    @rx.event(background=True)
    async def reset_invite_copied(self):
        """Тост «Код скопирован» гаснет через 3 секунды (A04)."""
        await asyncio.sleep(3)
        async with self:
            self.invite_code_copied = False

    @rx.event
    def share_invite(self):
        entrance = self.invite_entrance
        if not entrance:
            return
        payload = json.dumps(
            {
                "title": "Приглашение в дом",
                "text": f"Код дома: {entrance.invite_code_display}",
                "url": entrance.join_url,
            }
        )
        url_js = json.dumps(entrance.join_url)
        return rx.call_script(
            f"navigator.share ? navigator.share({payload}).catch(() => {{}}) "
            f": navigator.clipboard.writeText({url_js})"
        )

    @rx.event
    def mark_copied(self, entrance_id: int):
        self.copied_entrance_id = entrance_id

    @rx.event
    def ask_regenerate_code(self, entrance_id: int):
        self.confirm_regenerate_entrance_id = entrance_id

    @rx.event
    def cancel_regenerate_code(self):
        self.confirm_regenerate_entrance_id = 0

    @rx.event
    def regenerate_invite_code(self):
        """Перевыпускает код/QR подъезда — старая ссылка перестаёт работать."""
        entrance_id = self.confirm_regenerate_entrance_id
        self.confirm_regenerate_entrance_id = 0
        if not entrance_id:
            return
        with get_session() as session:
            entrance = session.get(Entrance, entrance_id)
            if entrance and entrance.tenant_id == int(self.tenant_id):
                entrance.invite_code = gen_invite_code()
                session.add(entrance)
                session.commit()
        return UKAdminState.load_admin_data

    @rx.event
    def stop_live(self):
        self.is_live = False

    @rx.event(background=True)
    async def start_live(self):
        """Периодически обновляет список жителей/подъездов, чтобы новые
        регистрации по QR/ссылке были видны УК без обновления страницы."""
        async with self:
            if self.is_live or not self.tenant_id:
                return
            self.is_live = True
        try:
            while True:
                await asyncio.sleep(5)
                async with self:
                    if not self.is_live:
                        return
                    yield UKAdminState.load_admin_data
        finally:
            async with self:
                self.is_live = False
