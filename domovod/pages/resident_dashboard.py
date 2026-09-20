"""Кабинет жителя — «Дом» и «Контакты»."""

from __future__ import annotations

import reflex as rx

from ..tab_state import TabState
from ..ui import bottom_tabs, phone_shell, top_bar
from . import shared

RESIDENT_TABS = [
    ("home", "Дом", "house"),
    ("contacts", "Контакты", "users"),
]


def resident_dashboard() -> rx.Component:
    body = rx.match(
        TabState.resident_tab,
        ("contacts", shared.contacts_tab()),
        shared.home_tab(),
    )
    return phone_shell(
        body,
        bottom_tabs(RESIDENT_TABS, TabState.resident_tab, TabState.set_resident_tab),
        header=top_bar("Домовод"),
    )
