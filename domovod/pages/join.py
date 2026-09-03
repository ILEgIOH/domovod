"""Вход жителя по ссылке-приглашению или QR-коду: /join?code=ABC123.

Без пароля: личность подтверждает MAX (пока — заглушка). Нужно только
подтвердить номер квартиры при первом входе — дальше это устройство
будет узнаваться автоматически.
"""

from __future__ import annotations

import reflex as rx

from ..max_stub import STUB_DISPLAY_NAME
from ..state import AuthState
from ..ui import MAX_WIDTH, error_text, field_label


def _join_form() -> rx.Component:
    return rx.vstack(
        rx.icon("badge-check", size=28, color="var(--accent-9)"),
        rx.heading("Вход через MAX", size="5", margin_top="0.5rem", margin_bottom="0.15rem"),
        rx.text(
            f"Вы входите как {STUB_DISPLAY_NAME} — имя и телефон подтянутся из MAX",
            size="2",
            color="var(--gray-10)",
            text_align="center",
        ),
        rx.cond(
            AuthState.join_entrance_label != "",
            rx.text(
                AuthState.join_entrance_label,
                size="2",
                weight="medium",
                margin_top="0.5rem",
                margin_bottom="0.5rem",
            ),
        ),
        error_text(AuthState.res_error),
        field_label("Квартира"),
        rx.input(
            value=AuthState.res_apartment,
            on_change=AuthState.set_res_apartment,
            placeholder="42",
            width="100%",
            margin_bottom="1rem",
            auto_focus=True,
        ),
        rx.button("Присоединиться", width="100%", on_click=AuthState.join_confirm),
        spacing="2",
        align="center",
        width="100%",
    )


def _error_view() -> rx.Component:
    return rx.vstack(
        rx.icon("circle-alert", size=32, color="var(--red-9)"),
        rx.heading("Ссылка недействительна", size="5", text_align="center"),
        rx.text(
            AuthState.join_error,
            size="2",
            color="var(--gray-10)",
            text_align="center",
        ),
        rx.link(rx.button("На главную", margin_top="0.5rem"), href="/"),
        spacing="3",
        align="center",
        padding_top="3rem",
        width="100%",
    )


def _already_signed_in_view() -> rx.Component:
    return rx.vstack(
        rx.icon("circle-check", size=32, color="var(--accent-9)"),
        rx.heading("Вы уже вошли", size="5", text_align="center"),
        rx.text(
            "Вы уже авторизованы как житель. Откройте личный кабинет.",
            size="2",
            color="var(--gray-10)",
            text_align="center",
        ),
        rx.link(rx.button("Перейти в личный кабинет", margin_top="0.5rem"), href="/app"),
        spacing="3",
        align="center",
        padding_top="3rem",
        width="100%",
    )


def join_page() -> rx.Component:
    return rx.box(
        rx.box(
            rx.cond(
                AuthState.is_resident,
                _already_signed_in_view(),
                rx.cond(
                    AuthState.join_error != "",
                    _error_view(),
                    _join_form(),
                ),
            ),
            width="100%",
            max_width=MAX_WIDTH,
            margin="0 auto",
            padding="2.5rem 1.25rem",
            min_height="100vh",
        ),
        width="100%",
        min_height="100vh",
        background="var(--gray-2)",
    )
