"""Управление домами, подъездами и жителями со стороны УК."""

from __future__ import annotations

from typing import List

import reflex as rx
from pydantic import BaseModel
from sqlmodel import select

from .db import get_session
from .models import Building, Entrance, Resident
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
    residents_count: int


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

    set_new_building_address = make_setter("new_building_address")
    set_new_entrance_building_id = make_setter("new_entrance_building_id")
    set_new_entrance_number = make_setter("new_entrance_number")

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
            entrance_items = []
            resident_items = []
            for e in entrance_rows:
                count = len(
                    session.exec(
                        select(Resident).where(Resident.entrance_id == e.id)
                    ).all()
                )
                entrance_items.append(
                    EntranceItem(
                        id=e.id,
                        building_id=e.building_id,
                        building_address=building_map.get(e.building_id, "?"),
                        number=e.number,
                        invite_code=e.invite_code,
                        residents_count=count,
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
                        phone=r.phone,
                        entrance_number=ent.number if ent else 0,
                        building_address=building_map.get(
                            ent.building_id, "?"
                        )
                        if ent
                        else "?",
                    )
                )
            self.residents = resident_items

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
