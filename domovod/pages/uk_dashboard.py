"""Кабинет управляющей компании — «Дом» и «Контакты» (тот же экран, что у жителя)."""

from __future__ import annotations

import reflex as rx

from ..tab_state import TabState
from ..ui import bottom_tabs, phone_shell, top_bar
from . import shared

UK_TABS = [
    ("home", "Дом", "house"),
    ("contacts", "Контакты", "users"),
    ("management", "Управление", "settings"),
]


def uk_dashboard() -> rx.Component:
    body = rx.match(
        TabState.uk_tab,
        ("contacts", shared.contacts_tab()),
        ("management", shared.management_tab()),
        shared.home_tab(),
    )
    return phone_shell(
        body,
        bottom_tabs(UK_TABS, TabState.uk_tab, TabState.set_uk_tab),
        header=top_bar("Домовод"),
    )
