"""Состояние переключения вкладок интерфейса (без смены route)."""

import reflex as rx

from .setters import make_setter


class TabState(rx.State):
    uk_tab: str = "home"
    resident_tab: str = "home"

    set_uk_tab = make_setter("uk_tab")
    set_resident_tab = make_setter("resident_tab")
