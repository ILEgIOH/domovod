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
            rx.image(src="/logo.png", width="96px", height="96px", style={"objectFit": "contain"}),
            rx.heading(
                "Дом – это проще, когда все рядом",
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
                on_click=AuthState.open_create_home_view,
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


def _code_box(index: int, value, placeholder: str) -> rx.Component:
    # Фокус НЕ вешаем через статичный auto_focus (HTML-атрибут) — он бы
    # срабатывал при каждой перерисовке и мог перетягивать фокус обратно
    # на это поле. Вместо этого начальный фокус ставится один раз через
    # AuthState.open_join_code_view, а дальше — через set_join_code_char/
    # join_code_key_down.
    return rx.input(
        value=value,
        on_change=AuthState.set_join_code_char(index),
        on_key_down=AuthState.join_code_key_down(index),
        placeholder=placeholder,
        id=f"join_code_c{index}_input",
        max_length=1,
        text_align="center",
        style={
            "fontSize": "1.75rem",
            "fontWeight": "700",
            "caretColor": "transparent",
            "textTransform": "uppercase",
        },
        background="transparent",
        border="none",
        outline="none",
        box_shadow="none",
        padding="0",
        width="1.3em",
    )


def _create_home_view() -> rx.Component:
    """Экран «Создать дом»: заводит новый дом+подъезд без email/пароля —
    создатель сразу становится админом. ФИО и номер жилища необязательны
    (для случая когда создатель сам там живёт)."""
    home_ready = AuthState.create_home_ready
    return rx.vstack(
        _back_link(),
        rx.heading(
            "Создать дом",
            size="6",
            weight="bold",
            style={"color": BRAND_PURPLE},
            margin_bottom="1.5rem",
        ),
        error_text(AuthState.create_error),
        field_label("Напишите название дома"),
        rx.text(
            "Желательно в виде адреса, оно будет видно жильцам на главной "
            "странице и при приглашении.",
            size="2",
            color="var(--gray-9)",
            margin_bottom="0.75rem",
        ),
        rx.input(
            value=AuthState.create_address,
            on_change=AuthState.set_create_address,
            on_key_down=AuthState.create_address_key_down,
            placeholder="Можайское шоссе 100",
            background="transparent",
            border="none",
            outline="none",
            box_shadow="none",
            padding="0",
            width="100%",
            style={"fontSize": "1.5rem", "fontWeight": "700"},
            auto_focus=True,
        ),
        rx.hstack(
            rx.text("Подъезд", size="3", color="var(--gray-9)"),
            rx.input(
                value=AuthState.create_entrance_number,
                on_change=AuthState.set_create_entrance_number,
                on_key_down=AuthState.create_entrance_number_key_down,
                placeholder="и подъезд, если есть",
                background="transparent",
                border="none",
                outline="none",
                box_shadow="none",
                padding="0",
                flex="1",
                size="2",
                color="var(--gray-9)",
            ),
            align="center",
            spacing="2",
            width="100%",
            margin_bottom="2rem",
        ),
        field_label("Ваше имя:"),
        rx.input(
            value=AuthState.create_full_name,
            on_change=AuthState.set_create_full_name,
            on_key_down=AuthState.create_full_name_key_down,
            width="100%",
            margin_bottom="0.6rem",
        ),
        field_label("Номер жилища (если вы жилец):"),
        rx.input(
            value=AuthState.create_apartment,
            on_change=AuthState.set_create_apartment,
            on_key_down=AuthState.create_apartment_key_down,
            width="100%",
            margin_bottom="1rem",
        ),
        rx.button(
            "Создать!",
            width="100%",
            size="3",
            radius="full",
            margin_top="1rem",
            disabled=home_ready == False,  # noqa: E712
            style=rx.cond(
                home_ready,
                {"background": BRAND_PURPLE, "color": "white"},
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
    """Экран «Введите код»: ручной ввод кода приглашения — 6 отдельных
    полей по одному символу (3 буквы + 3 цифры), как в OTP-вводе, так
    что вставить символ «в середину» или не того типа физически нельзя.
    Белая кнопка, пока код не введён полностью → фиолетовая, когда готов
    к проверке → красная «Дом не найден», если код неверный."""
    return rx.vstack(
        _back_link(),
        rx.heading("Введите код", size="6", weight="bold", margin_bottom="1.5rem"),
        rx.hstack(
            _code_box(1, AuthState.join_code_c1, "X"),
            _code_box(2, AuthState.join_code_c2, "X"),
            _code_box(3, AuthState.join_code_c3, "X"),
            rx.text("–", size="7", weight="bold", color="var(--gray-9)"),
            _code_box(4, AuthState.join_code_c4, "0"),
            _code_box(5, AuthState.join_code_c5, "0"),
            _code_box(6, AuthState.join_code_c6, "0"),
            align="center",
            justify="center",
            spacing="2",
            background="var(--gray-3)",
            border_radius="14px",
            height="4.5rem",
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
