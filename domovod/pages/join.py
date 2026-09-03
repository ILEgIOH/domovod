"""Вход жителя по ссылке-приглашению или QR-коду: /join?code=ABC123."""

from __future__ import annotations

import reflex as rx

from ..state import AuthState
from ..ui import MAX_WIDTH, error_text, field_label


def _register_form() -> rx.Component:
    return rx.vstack(
        rx.heading("Регистрация жителя", size="5", margin_bottom="0.15rem"),
        rx.cond(
            AuthState.join_entrance_label != "",
            rx.text(
                AuthState.join_entrance_label,
                size="2",
                color="var(--gray-10)",
                margin_bottom="0.75rem",
            ),
        ),
        error_text(AuthState.res_error),
        field_label("ФИО"),
        rx.input(
            value=AuthState.res_full_name,
            on_change=AuthState.set_res_full_name,
            placeholder="Иванов Иван Иванович",
            width="100%",
            margin_bottom="0.6rem",
        ),
        field_label("Квартира"),
        rx.input(
            value=AuthState.res_apartment,
            on_change=AuthState.set_res_apartment,
            placeholder="42",
            width="100%",
            margin_bottom="0.6rem",
        ),
        field_label("Телефон"),
        rx.input(
            value=AuthState.res_phone,
            on_change=AuthState.set_res_phone,
            placeholder="+7 900 000-00-00",
            width="100%",
            margin_bottom="0.6rem",
        ),
        field_label("Пароль"),
        rx.input(
            value=AuthState.res_password,
            on_change=AuthState.set_res_password,
            type="password",
            placeholder="от 4 символов",
            width="100%",
            margin_bottom="1rem",
        ),
        rx.button("Зарегистрироваться", width="100%", on_click=AuthState.resident_register),
        rx.center(
            rx.button(
                "Уже зарегистрированы? Войти",
                variant="ghost",
                size="2",
                on_click=AuthState.set_auth_view("resident_login"),
            ),
            width="100%",
            padding_top="0.75rem",
        ),
        width="100%",
    )


def _login_form() -> rx.Component:
    return rx.vstack(
        rx.heading("Вход для жителей", size="5", margin_bottom="0.75rem"),
        error_text(AuthState.res_login_error),
        field_label("Телефон"),
        rx.input(
            value=AuthState.res_login_phone,
            on_change=AuthState.set_res_login_phone,
            placeholder="+7 900 000-00-00",
            width="100%",
            margin_bottom="0.6rem",
        ),
        field_label("Пароль"),
        rx.input(
            value=AuthState.res_login_password,
            on_change=AuthState.set_res_login_password,
            type="password",
            placeholder="••••••",
            width="100%",
            margin_bottom="1rem",
        ),
        rx.button("Войти", width="100%", on_click=AuthState.resident_login),
        rx.center(
            rx.button(
                "Первый раз здесь? Регистрация",
                variant="ghost",
                size="2",
                on_click=AuthState.set_auth_view("resident_register"),
            ),
            width="100%",
            padding_top="0.75rem",
        ),
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
                    rx.match(
                        AuthState.auth_view,
                        ("resident_login", _login_form()),
                        _register_form(),
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
