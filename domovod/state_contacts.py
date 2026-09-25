"""Вкладка «Контакты»: личные контакты пользователя, службы дома и
полезные адреса подъезда."""

from __future__ import annotations

from typing import List

import reflex as rx
from pydantic import BaseModel
from sqlmodel import select

from .db import get_session
from .models import PersonalContact, UsefulAddress
from .setters import make_setter
from .state import AuthState


class ContactItem(BaseModel):
    id: int
    name: str
    phone: str


class AddressItem(BaseModel):
    id: int
    category: str
    title: str
    value: str
    phone: str


class ContactsState(AuthState):
    personal_contacts: List[ContactItem] = []
    useful_addresses: List[AddressItem] = []

    new_contact_name: str = ""
    new_contact_phone: str = ""
    contact_error: str = ""

    # --- R01–R04: форма одна на «Службу дома» и «Полезный адрес» —
    # различает их только editor_category ("service" | "address").
    editor_category: str = "address"
    editor_id: int = 0
    new_address_title: str = ""
    new_address_value: str = ""
    new_address_phone: str = ""
    address_error: str = ""
    confirm_delete_address_id: int = 0

    set_new_contact_name = make_setter("new_contact_name")
    set_new_contact_phone = make_setter("new_contact_phone")
    set_new_address_title = make_setter("new_address_title")
    set_new_address_value = make_setter("new_address_value")
    set_new_address_phone = make_setter("new_address_phone")

    @rx.var
    def services(self) -> List[AddressItem]:
        return [a for a in self.useful_addresses if a.category == "service"]

    @rx.var
    def addresses(self) -> List[AddressItem]:
        return [a for a in self.useful_addresses if a.category != "service"]

    @rx.event
    def load_contacts(self):
        if not self.user_id:
            self.personal_contacts = []
            self.useful_addresses = []
            return
        with get_session() as session:
            rows = session.exec(
                select(PersonalContact).where(
                    PersonalContact.owner_role == self.role,
                    PersonalContact.owner_id == self.user_id,
                )
            ).all()
            self.personal_contacts = [
                ContactItem(id=c.id, name=c.name, phone=c.phone) for c in rows
            ]

            if self.viewing_entrance_id:
                addr_rows = session.exec(
                    select(UsefulAddress).where(
                        UsefulAddress.entrance_id == self.viewing_entrance_id
                    )
                ).all()
                self.useful_addresses = [
                    AddressItem(id=a.id, category=a.category, title=a.title, value=a.value, phone=a.phone)
                    for a in addr_rows
                ]
            else:
                self.useful_addresses = []

    @rx.event
    def add_contact(self):
        self.contact_error = ""
        name = self.new_contact_name.strip()
        if not name:
            self.contact_error = "Укажите имя"
            return
        with get_session() as session:
            session.add(
                PersonalContact(
                    owner_role=self.role,
                    owner_id=self.user_id,
                    name=name,
                    phone=self.new_contact_phone.strip(),
                )
            )
            session.commit()
        self.new_contact_name = ""
        self.new_contact_phone = ""
        return ContactsState.load_contacts

    @rx.event
    def delete_contact(self, contact_id: int):
        with get_session() as session:
            c = session.get(PersonalContact, contact_id)
            if c and c.owner_role == self.role and c.owner_id == int(self.user_id or 0):
                session.delete(c)
                session.commit()
        return ContactsState.load_contacts

    # ---------------- R02–R04: службы дома / полезные адреса ----------------

    @rx.event
    def open_address_editor(self, category: str, item_id: int = 0):
        """R02/R03: пустая форма для нового контакта, либо предзаполненная
        для правки существующего (item_id > 0)."""
        if not self.is_uk:
            return
        self.editor_category = category
        self.editor_id = item_id
        self.address_error = ""
        if item_id:
            item = next((a for a in self.useful_addresses if a.id == item_id), None)
            if item:
                self.new_address_title = item.title
                self.new_address_value = item.value
                self.new_address_phone = item.phone
                return
        self.new_address_title = ""
        self.new_address_value = ""
        self.new_address_phone = ""

    @rx.event
    def save_address(self):
        """R02/R03 «Сохранить» — создаёт новый контакт либо обновляет
        существующий (editor_id > 0), в зависимости от того, как открыли форму."""
        self.address_error = ""
        if not self.is_uk:
            return
        title = self.new_address_title.strip()
        value = self.new_address_value.strip()
        if not title or not value:
            self.address_error = "Заполните название и значение"
            return
        if not self.viewing_entrance_id:
            self.address_error = "Выберите подъезд"
            return
        with get_session() as session:
            if self.editor_id:
                row = session.get(UsefulAddress, self.editor_id)
                if not row or row.tenant_id != int(self.tenant_id):
                    return
                row.title = title
                row.value = value
                row.phone = self.new_address_phone.strip()
                session.add(row)
            else:
                session.add(
                    UsefulAddress(
                        entrance_id=self.viewing_entrance_id,
                        tenant_id=self.tenant_id,
                        category=self.editor_category,
                        title=title,
                        value=value,
                        phone=self.new_address_phone.strip(),
                    )
                )
            session.commit()
        self.editor_id = 0
        self.new_address_title = ""
        self.new_address_value = ""
        self.new_address_phone = ""
        return ContactsState.load_contacts

    @rx.event
    def ask_delete_address(self, address_id: int):
        self.confirm_delete_address_id = address_id

    @rx.event
    def cancel_delete_address(self):
        self.confirm_delete_address_id = 0

    @rx.event
    def confirm_delete_address(self):
        """R10 — подтверждённое удаление службы/адреса."""
        if not self.is_uk:
            return
        address_id = self.confirm_delete_address_id
        self.confirm_delete_address_id = 0
        self.editor_id = 0
        with get_session() as session:
            a = session.get(UsefulAddress, address_id)
            if a and a.tenant_id == int(self.tenant_id):
                session.delete(a)
                session.commit()
        return ContactsState.load_contacts
