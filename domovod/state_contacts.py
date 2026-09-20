"""Вкладка «Контакты»: личные контакты пользователя и полезные адреса подъезда."""

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
    title: str
    value: str


class ContactsState(AuthState):
    personal_contacts: List[ContactItem] = []
    useful_addresses: List[AddressItem] = []

    new_contact_name: str = ""
    new_contact_phone: str = ""
    contact_error: str = ""

    new_address_title: str = ""
    new_address_value: str = ""
    address_error: str = ""

    set_new_contact_name = make_setter("new_contact_name")
    set_new_contact_phone = make_setter("new_contact_phone")
    set_new_address_title = make_setter("new_address_title")
    set_new_address_value = make_setter("new_address_value")

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
                    AddressItem(id=a.id, title=a.title, value=a.value) for a in addr_rows
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

    @rx.event
    def add_address(self):
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
            session.add(
                UsefulAddress(
                    entrance_id=self.viewing_entrance_id,
                    tenant_id=self.tenant_id,
                    title=title,
                    value=value,
                )
            )
            session.commit()
        self.new_address_title = ""
        self.new_address_value = ""
        return ContactsState.load_contacts

    @rx.event
    def delete_address(self, address_id: int):
        if not self.is_uk:
            return
        with get_session() as session:
            a = session.get(UsefulAddress, address_id)
            if a and a.tenant_id == int(self.tenant_id):
                session.delete(a)
                session.commit()
        return ContactsState.load_contacts
