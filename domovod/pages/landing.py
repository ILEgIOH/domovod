"""Стартовый экран: выбор роли, вход и регистрация."""

from __future__ import annotations

import reflex as rx

from ..state import AuthState
from ..ui import (
    BRAND_ACTION_TEXT,
    BRAND_NEON,
    BRAND_PURPLE,
    MAX_WIDTH,
    TEXT_PRIMARY,
    error_text,
    field_label,
)


def _splash_view() -> rx.Component:
    """Заставка — первое, что видит пользователь. Ведёт либо к жителю
    (регистрация по коду приглашения), либо к УК (регистрация компании).
    Точно по макету V01: без разделителя «или» между кнопками."""
    return rx.vstack(
        rx.spacer(),
        rx.vstack(
            rx.image(src="/logo.png", width="96px", height="96px", style={"objectFit": "contain"}),
            rx.heading(
                "Дом — это проще, когда все рядом",
                size="7",
                weight="bold",
                text_align="center",
                line_height="1.3",
                margin_top="1rem",
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
                style={"background": BRAND_NEON, "color": BRAND_ACTION_TEXT},
                on_click=AuthState.open_join_code_view,
            ),
            rx.button(
                "Создать дом",
                width="100%",
                size="3",
                radius="full",
                style={"background": BRAND_PURPLE, "color": BRAND_ACTION_TEXT},
                on_click=AuthState.open_create_home_view,
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        rx.vstack(
            rx.text(
                "Есть ссылка или QR? Дом откроется",
                size="1",
                color="var(--gray-9)",
                text_align="center",
            ),
            rx.text(
                "автоматически после перехода.",
                size="1",
                color="var(--gray-9)",
                text_align="center",
            ),
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
    """Голая стрелка назад без подписи — как в макете (J01/A01 и т.д.),
    без текста «Назад» и без кружка-подложки под иконкой."""
    return rx.box(
        rx.icon("chevron-left", size=24, color="var(--gray-11)"),
        on_click=AuthState.set_auth_view("choose"),
        cursor="pointer",
        margin_bottom="1.5rem",
        display="inline-flex",
    )


def _create_home_view() -> rx.Component:
    """Экран «Создать дом»: заводит новый дом+подъезд без email/пароля —
    создатель сразу становится админом. ФИО и номер жилища необязательны
    (для случая когда создатель сам там живёт)."""
    home_ready = AuthState.create_home_ready
    return rx.vstack(
        rx.box(
            rx.icon(
                "chevron-left",
                size=24,
                color="var(--gray-11)",
                cursor="pointer",
                on_click=AuthState.set_auth_view("choose"),
                style={"position": "absolute", "left": "0"},
            ),
            rx.heading(
                "Создать дом",
                size="6",
                weight="bold",
                style={"color": BRAND_ACTION_TEXT},
                text_align="center",
                width="100%",
            ),
            position="relative",
            display="flex",
            align_items="center",
            width="100%",
            margin_bottom="1.5rem",
        ),
        error_text(AuthState.create_error),
        field_label("Напишите адрес дома"),
        rx.text(
            "Так соседи узнают свой дом на главной и в приглашении.",
            size="2",
            color="var(--gray-9)",
            margin_bottom="0.9rem",
        ),
        rx.input(
            value=AuthState.create_address,
            on_change=AuthState.set_create_address,
            on_key_down=AuthState.create_address_key_down,
            placeholder="Улица и номер дома",
            background="transparent",
            border="none",
            border_bottom=f"1.5px solid {BRAND_PURPLE}",
            outline="none",
            box_shadow="none",
            padding="0 0 0.4rem 0",
            width="100%",
            style={"fontSize": "1.4rem", "fontWeight": "700", "color": TEXT_PRIMARY},
            auto_focus=True,
        ),
        rx.input(
            value=AuthState.create_entrance_number,
            on_change=AuthState.set_create_entrance_number,
            on_key_down=AuthState.create_entrance_number_key_down,
            placeholder="Подъезд, корпус — если есть",
            background="transparent",
            border="none",
            outline="none",
            box_shadow="none",
            padding="0.4rem 0 0 0",
            width="100%",
            size="2",
            color="var(--gray-9)",
            margin_bottom="2rem",
        ),
        field_label("Ваше имя"),
        rx.input(
            value=AuthState.create_full_name,
            on_change=AuthState.set_create_full_name,
            on_key_down=AuthState.create_full_name_key_down,
            placeholder="Например, Татьяна",
            width="100%",
            margin_bottom="0.6rem",
        ),
        field_label("Квартира · необязательно"),
        rx.input(
            value=AuthState.create_apartment,
            on_change=AuthState.set_create_apartment,
            on_key_down=AuthState.create_apartment_key_down,
            placeholder="Если вы живёте в этом доме",
            width="100%",
            margin_bottom="1rem",
        ),
        rx.button(
            "Создать дом",
            width="100%",
            size="3",
            radius="full",
            margin_top="1rem",
            disabled=home_ready == False,  # noqa: E712
            style=rx.cond(
                home_ready,
                {"background": BRAND_PURPLE, "color": BRAND_ACTION_TEXT},
                {"background": "var(--gray-4)", "color": "var(--gray-9)"},
            ),
            on_click=AuthState.create_home_confirm,
        ),
        rx.cond(
            home_ready == False,  # noqa: E712
            rx.text(
                "Сначала заполните данные",
                size="1",
                color="var(--gray-9)",
                text_align="center",
                padding_top="1rem",
                width="100%",
            ),
        ),
        width="100%",
        align="start",
    )


def _join_code_view() -> rx.Component:
    """Экран «Присоединиться» — J01/J02/J03 из макета: одно поле «Код
    дома», кнопка «Продолжить» серая → фиолетовая при готовности; при
    ошибке — красная рамка поля, текст ошибки под ним и вторая кнопка
    «Ввести другой код»."""
    return rx.vstack(
        _back_link(),
        rx.heading("Присоединиться", size="7", weight="bold", margin_bottom="0.4rem"),
        rx.text(
            "Введите код из приглашения",
            size="3",
            color="var(--gray-9)",
            margin_bottom="2rem",
        ),
        field_label("Код дома"),
        rx.input(
            value=AuthState.join_code_display,
            on_change=AuthState.set_join_code_input,
            on_key_down=AuthState.join_code_input_key_down,
            id="join_code_input_field",
            placeholder="Например, DOM246",
            auto_focus=True,
            radius="full",
            background="white",
            style={
                "fontSize": "1.1rem",
                "border": rx.cond(AuthState.join_code_error, "1.5px solid var(--red-9)", "none"),
            },
            width="100%",
            height="3.25rem",
        ),
        rx.cond(
            AuthState.join_code_error,
            rx.text(
                "Код не найден. Проверьте 6 символов.",
                size="2",
                color="var(--red-9)",
                margin_top="0.5rem",
            ),
        ),
        rx.text(
            "Код можно получить у администратора",
            size="2",
            color="var(--gray-9)",
            margin_top="1.5rem",
        ),
        rx.text("или соседей в чате дома.", size="2", color="var(--gray-9)"),
        rx.spacer(),
        rx.cond(
            AuthState.join_code_error,
            rx.button(
                "Ввести другой код",
                width="100%",
                size="3",
                radius="full",
                variant="soft",
                color_scheme="gray",
                margin_bottom="0.75rem",
                on_click=AuthState.clear_join_code,
            ),
        ),
        rx.button(
            "Продолжить",
            width="100%",
            size="3",
            radius="full",
            disabled=AuthState.join_code_ready == False,  # noqa: E712
            style=rx.cond(
                AuthState.join_code_ready,
                {"background": BRAND_PURPLE, "color": BRAND_ACTION_TEXT},
                {"background": "var(--gray-4)", "color": "var(--gray-9)"},
            ),
            on_click=AuthState.lookup_join_code,
        ),
        width="100%",
        min_height="100vh",
        align="start",
    )


def landing() -> rx.Component:
    return rx.box(
        rx.box(
            rx.match(
                AuthState.auth_view,
                ("join_code", _join_code_view()),
                ("create_home", _create_home_view()),
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
