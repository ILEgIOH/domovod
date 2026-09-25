"""Вход жителя по ссылке-приглашению или QR-коду: /join?code=ABC123.

Без пароля: личность подтверждает MAX (пока — заглушка). Нужно только
подтвердить номер квартиры при первом входе — дальше это устройство
будет узнаваться автоматически.
"""

from __future__ import annotations

import reflex as rx

from ..state import AuthState
from ..ui import BRAND_NEON, BRAND_PURPLE, MAX_WIDTH, error_text


def _invite_field(label: str, child: rx.Component) -> rx.Component:
    return rx.hstack(
        rx.text(label, size="3", weight="medium", white_space="nowrap"),
        child,
        align="center",
        spacing="3",
        width="100%",
    )


def _join_form() -> rx.Component:
    apartment_filled = AuthState.res_apartment != ""
    return rx.vstack(
        rx.link(
            rx.icon("chevron-left", size=20, color="var(--gray-9)"),
            href="/",
        ),
        rx.heading(
            "Вас пригласили!",
            size="6",
            weight="bold",
            style={"color": BRAND_PURPLE},
            margin_top="1.25rem",
            margin_bottom="1.5rem",
        ),
        rx.cond(
            AuthState.join_address != "",
            rx.vstack(
                rx.heading(AuthState.join_address, size="5", weight="bold"),
                rx.text(AuthState.join_entrance_subtitle, size="2", color="var(--gray-8)"),
                spacing="0",
                align="start",
                width="100%",
                margin_bottom="2rem",
            ),
        ),
        error_text(AuthState.res_error),
        _invite_field(
            "Ваше имя:",
            rx.input(
                value=AuthState.res_full_name,
                on_change=AuthState.set_res_full_name,
                on_key_down=AuthState.res_full_name_key_down,
                flex="1",
                size="3",
                radius="large",
                background="var(--gray-3)",
                border="none",
            ),
        ),
        rx.box(height="1rem"),
        _invite_field(
            "Номер жилища:",
            rx.input(
                value=AuthState.res_apartment,
                on_change=AuthState.set_res_apartment,
                on_key_down=AuthState.res_apartment_key_down,
                on_blur=AuthState.check_join_apartment,
                placeholder="147",
                flex="1",
                size="3",
                radius="large",
                background="var(--gray-3)",
                border="none",
                weight="bold",
                auto_focus=True,
            ),
        ),
        rx.button(
            rx.cond(apartment_filled, "Присоединиться!", "Присоединиться"),
            width="100%",
            size="3",
            radius="full",
            margin_top="3rem",
            disabled=apartment_filled == False,  # noqa: E712
            style=rx.cond(
                apartment_filled,
                {"background": BRAND_NEON, "color": "black"},
                {"background": "var(--gray-4)", "color": "var(--gray-9)"},
            ),
            on_click=AuthState.join_confirm,
        ),
        rx.text(
            "Напишите ваше имя и номер квартиры или дома",
            size="1",
            color="var(--gray-9)",
            text_align="center",
            padding_top="1rem",
            width="100%",
        ),
        spacing="2",
        align="start",
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


def _pending_view() -> rx.Component:
    """R06: квартиру уже занял другой активный житель — заявка ждёт
    подтверждения администратора вместо мгновенного входа."""
    return rx.vstack(
        rx.icon("clock", size=32, color=BRAND_PURPLE),
        rx.heading("Заявка на рассмотрении", size="5", text_align="center"),
        rx.cond(
            AuthState.join_address != "",
            rx.text(
                AuthState.join_address + " · " + AuthState.join_entrance_subtitle,
                size="2",
                weight="medium",
                text_align="center",
            ),
        ),
        rx.text(
            "В этой квартире уже есть житель. Администратор подтвердит "
            "вашу заявку, и дом откроется автоматически.",
            size="2",
            color="var(--gray-10)",
            text_align="center",
        ),
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
                    AuthState.join_pending,
                    _pending_view(),
                    rx.cond(
                        AuthState.join_error != "",
                        _error_view(),
                        _join_form(),
                    ),
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
