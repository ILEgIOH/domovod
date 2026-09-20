"""Стартовый экран: выбор роли, вход и регистрация."""

from __future__ import annotations

import reflex as rx

from ..state import AuthState
from ..ui import BRAND_NEON, BRAND_PURPLE, MAX_WIDTH, error_text, field_label


def _splash_view() -> rx.Component:
    """Заставка — первое, что видит пользователь. Ведёт либо к жителю
    (регистрация по коду приглашения), либо к УК (регистрация компании)."""
    return rx.vstack(
        rx.spacer(),
        rx.vstack(
            rx.heading(
                "Дом – это проще, когда все рядом",
                size="7",
                weight="bold",
                text_align="center",
                line_height="1.3",
            ),
            rx.text(
                "Сборы, инициативы, опросы и контакты — в одном месте",
                size="2",
                color="var(--gray-10)",
                text_align="center",
            ),
            spacing="3",
            align="center",
            padding_bottom="2.5rem",
            width="100%",
        ),
        rx.vstack(
            rx.button(
                "Присоединиться к дому",
                width="100%",
                size="3",
                radius="full",
                style={"background": BRAND_NEON, "color": "black"},
                on_click=AuthState.open_join_code_view,
            ),
            rx.text("или", size="2", color="var(--gray-9)"),
            rx.button(
                "Создать дом",
                width="100%",
                size="3",
                radius="full",
                style={"background": BRAND_PURPLE, "color": "white"},
                on_click=AuthState.set_auth_view("uk_register"),
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        rx.vstack(
            rx.text("Есть ссылка или QR?", size="1", color="var(--gray-9)", text_align="center"),
            rx.text("Дом откроется автоматически", size="1", color="var(--gray-9)", text_align="center"),
            spacing="0",
            align="center",
            padding_top="2.5rem",
            width="100%",
        ),
        rx.spacer(),
        rx.vstack(
            rx.text("Проверить без ввода данных", size="1", color="var(--gray-8)"),
            rx.hstack(
                rx.button(
                    "Демо: житель",
                    variant="outline",
                    size="2",
                    flex="1",
                    on_click=AuthState.demo_login_resident,
                ),
                rx.button(
                    "Демо: УК",
                    variant="outline",
                    size="2",
                    flex="1",
                    on_click=AuthState.demo_login_uk,
                ),
                width="100%",
                spacing="2",
            ),
            spacing="2",
            align="center",
            width="100%",
            padding_top="1.5rem",
        ),
        width="100%",
        min_height="100vh",
        align="center",
        spacing="0",
    )


def _back_link() -> rx.Component:
    return rx.button(
        rx.icon("arrow-left", size=16),
        "Назад",
        variant="ghost",
        size="2",
        on_click=AuthState.set_auth_view("choose"),
        margin_bottom="0.75rem",
    )


def _uk_login_view() -> rx.Component:
    return rx.vstack(
        _back_link(),
        rx.heading("Вход для УК", size="5", margin_bottom="0.75rem"),
        error_text(AuthState.login_error),
        field_label("Email"),
        rx.input(
            value=AuthState.login_email,
            on_change=AuthState.set_login_email,
            placeholder="company@example.com",
            width="100%",
            margin_bottom="0.6rem",
        ),
        field_label("Пароль"),
        rx.input(
            value=AuthState.login_password,
            on_change=AuthState.set_login_password,
            type="password",
            placeholder="••••••",
            width="100%",
            margin_bottom="1rem",
        ),
        rx.button("Войти", width="100%", on_click=AuthState.uk_login),
        rx.center(
            rx.button(
                "Нет аккаунта? Зарегистрировать УК",
                variant="ghost",
                size="2",
                on_click=AuthState.set_auth_view("uk_register"),
            ),
            width="100%",
            padding_top="0.75rem",
        ),
        width="100%",
    )


def _uk_register_view() -> rx.Component:
    return rx.vstack(
        _back_link(),
        rx.heading("Регистрация УК", size="5", margin_bottom="0.75rem"),
        error_text(AuthState.reg_error),
        field_label("Название компании"),
        rx.input(
            value=AuthState.reg_company_name,
            on_change=AuthState.set_reg_company_name,
            placeholder="ООО «УК Уютный дом»",
            width="100%",
            margin_bottom="0.6rem",
        ),
        field_label("Email"),
        rx.input(
            value=AuthState.reg_email,
            on_change=AuthState.set_reg_email,
            placeholder="company@example.com",
            width="100%",
            margin_bottom="0.6rem",
        ),
        field_label("Телефон (необязательно)"),
        rx.input(
            value=AuthState.reg_phone,
            on_change=AuthState.set_reg_phone,
            placeholder="+7 900 000-00-00",
            width="100%",
            margin_bottom="0.6rem",
        ),
        field_label("Пароль"),
        rx.input(
            value=AuthState.reg_password,
            on_change=AuthState.set_reg_password,
            type="password",
            placeholder="от 4 символов",
            width="100%",
            margin_bottom="1rem",
        ),
        rx.button("Зарегистрировать компанию", width="100%", on_click=AuthState.uk_register),
        rx.center(
            rx.button(
                "Уже зарегистрированы? Войти",
                variant="ghost",
                size="2",
                on_click=AuthState.set_auth_view("uk_login"),
            ),
            width="100%",
            padding_top="0.75rem",
        ),
        width="100%",
    )


def _join_code_view() -> rx.Component:
    """Экран «Введите код»: ручной ввод кода приглашения (3 буквы + 3
    цифры). Белая кнопка, пока код не введён полностью → фиолетовая,
    когда готов к проверке → красная «Дом не найден», если код неверный."""
    return rx.vstack(
        _back_link(),
        rx.heading("Введите код", size="6", weight="bold", margin_bottom="1.5rem"),
        rx.center(
            rx.input(
                value=AuthState.join_code_display,
                on_change=AuthState.set_join_code_input,
                placeholder="XXX – 000",
                text_align="center",
                size="3",
                style={
                    "fontSize": "1.75rem",
                    "fontWeight": "700",
                    "letterSpacing": "0.05em",
                },
                background="var(--gray-3)",
                border="none",
                border_radius="14px",
                height="4.5rem",
                width="100%",
            ),
            width="100%",
        ),
        rx.text(
            "Код обычно присылает администратор дома",
            size="2",
            color="var(--gray-9)",
            text_align="center",
            padding_top="0.75rem",
            width="100%",
        ),
        rx.button(
            rx.cond(AuthState.join_code_error, "Дом не найден", "Найти дом"),
            width="100%",
            size="3",
            radius="full",
            margin_top="3rem",
            disabled=AuthState.join_code_ready == False,  # noqa: E712
            style=rx.cond(
                AuthState.join_code_error,
                {"background": "var(--red-9)", "color": "white"},
                rx.cond(
                    AuthState.join_code_ready,
                    {"background": BRAND_PURPLE, "color": "white"},
                    {"background": "var(--gray-4)", "color": "var(--gray-9)"},
                ),
            ),
            on_click=AuthState.lookup_join_code,
        ),
        rx.cond(
            AuthState.join_code_ready == False,  # noqa: E712
            rx.text(
                "Сначала введите код или запросите его у вашего ответственного по дому.",
                size="1",
                color="var(--gray-9)",
                text_align="center",
                padding_top="1rem",
            ),
            rx.cond(
                AuthState.join_code_error,
                rx.text(
                    "Проверьте правильно ли написали код. Также мог обновить админ.",
                    size="1",
                    color="var(--gray-9)",
                    text_align="center",
                    padding_top="1rem",
                ),
            ),
        ),
        width="100%",
        align="center",
    )


def landing() -> rx.Component:
    return rx.box(
        rx.box(
            rx.match(
                AuthState.auth_view,
                ("uk_login", _uk_login_view()),
                ("uk_register", _uk_register_view()),
                ("join_code", _join_code_view()),
                _splash_view(),
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
