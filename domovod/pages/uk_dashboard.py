"""Кабинет управляющей компании: новости, долги/сборы, профиль."""

from __future__ import annotations

import reflex as rx

from ..state import AuthState
from ..state_finance import FinanceState
from ..state_news import NewsState
from ..state_uk_admin import UKAdminState
from ..tab_state import TabState
from ..ui import bottom_tabs, empty_state, error_text, field_label, phone_shell, progress_bar, section_card, top_bar

UK_TABS = [
    ("news", "Новости", "newspaper"),
    ("finance", "Долги и сборы", "wallet"),
    ("profile", "Профиль", "user"),
]


def _news_tab() -> rx.Component:
    return rx.vstack(
        section_card(
            rx.vstack(
                rx.heading("Новая новость", size="3", margin_bottom="0.4rem"),
                error_text(NewsState.news_error),
                rx.input(
                    placeholder="Заголовок",
                    value=NewsState.new_title,
                    on_change=NewsState.set_new_title,
                    width="100%",
                    margin_bottom="0.5rem",
                ),
                rx.text_area(
                    placeholder="Текст новости для жителей...",
                    value=NewsState.new_body,
                    on_change=NewsState.set_new_body,
                    width="100%",
                    margin_bottom="0.6rem",
                    rows="3",
                ),
                rx.button(
                    rx.icon("send", size=16),
                    "Опубликовать",
                    on_click=NewsState.create_news,
                    width="100%",
                ),
                width="100%",
            )
        ),
        rx.cond(
            NewsState.news_items.length() == 0,
            empty_state("Пока нет опубликованных новостей", "newspaper"),
            rx.foreach(
                NewsState.news_items,
                lambda n: section_card(
                    rx.hstack(
                        rx.vstack(
                            rx.text(n.title, weight="bold", size="3"),
                            rx.text(n.created_at, size="1", color="var(--gray-9)"),
                            align="start",
                            spacing="0",
                        ),
                        rx.spacer(),
                        rx.icon_button(
                            rx.icon("trash-2", size=15),
                            variant="ghost",
                            color_scheme="red",
                            size="1",
                            on_click=NewsState.delete_news(n.id),
                        ),
                        width="100%",
                    ),
                    rx.text(n.body, size="2", color="var(--gray-11)", margin_top="0.4rem"),
                ),
            ),
        ),
        width="100%",
    )


def _debts_section() -> rx.Component:
    return rx.vstack(
        section_card(
            rx.vstack(
                rx.heading("Начислить задолженность", size="3", margin_bottom="0.4rem"),
                error_text(FinanceState.debt_error),
                field_label("Житель"),
                rx.select.root(
                    rx.select.trigger(placeholder="Выберите жителя", width="100%"),
                    rx.select.content(
                        rx.foreach(
                            FinanceState.resident_options,
                            lambda o: rx.select.item(o.label, value=o.id.to_string()),
                        )
                    ),
                    value=FinanceState.new_debt_resident_id,
                    on_change=FinanceState.set_new_debt_resident_id,
                    width="100%",
                ),
                rx.hstack(
                    rx.input(
                        placeholder="Период, напр. Август 2026",
                        value=FinanceState.new_debt_period,
                        on_change=FinanceState.set_new_debt_period,
                        width="100%",
                        margin_top="0.5rem",
                    ),
                    width="100%",
                ),
                rx.hstack(
                    rx.select(
                        ["ЖКХ", "Капремонт", "Домофон", "Другое"],
                        value=FinanceState.new_debt_category,
                        on_change=FinanceState.set_new_debt_category,
                    ),
                    rx.input(
                        placeholder="Сумма, ₽",
                        value=FinanceState.new_debt_amount,
                        on_change=FinanceState.set_new_debt_amount,
                    ),
                    width="100%",
                    margin_top="0.5rem",
                ),
                rx.button(
                    "Добавить начисление",
                    on_click=FinanceState.add_debt,
                    width="100%",
                    margin_top="0.6rem",
                ),
                width="100%",
            )
        ),
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("Активные", value="active"),
                rx.tabs.trigger("История", value="history"),
                width="100%",
            ),
            rx.tabs.content(
                _debt_list(FinanceState.active_debts, "Задолженностей пока нет"),
                value="active",
                padding_top="0.6rem",
            ),
            rx.tabs.content(
                _debt_list(FinanceState.paid_debts, "Оплаченных начислений пока нет"),
                value="history",
                padding_top="0.6rem",
            ),
            default_value="active",
            width="100%",
        ),
        width="100%",
    )


def _debt_list(items, empty_text: str) -> rx.Component:
    return rx.cond(
        items.length() == 0,
        empty_state(empty_text, "receipt"),
        rx.foreach(
            items,
            lambda d: section_card(
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            f"{d.resident_name} · кв. {d.apartment}",
                            weight="bold",
                            size="2",
                        ),
                        rx.text(
                            f"{d.category} · {d.period}",
                            size="1",
                            color="var(--gray-9)",
                        ),
                        align="start",
                        spacing="0",
                    ),
                    rx.spacer(),
                    rx.vstack(
                        rx.text(d.amount_fmt, weight="bold"),
                        rx.badge(
                            rx.cond(d.is_paid, "Оплачено", "Долг"),
                            color_scheme=rx.cond(d.is_paid, "green", "red"),
                        ),
                        align="end",
                        spacing="1",
                    ),
                    width="100%",
                    align="start",
                ),
                rx.button(
                    rx.cond(d.is_paid, "Отметить как долг", "Отметить оплаченным"),
                    size="1",
                    variant="soft",
                    width="100%",
                    margin_top="0.5rem",
                    on_click=FinanceState.toggle_debt_paid(d.id),
                ),
            ),
        ),
    )


def _collections_section() -> rx.Component:
    return rx.vstack(
        section_card(
            rx.vstack(
                rx.heading("Новый сбор", size="3", margin_bottom="0.4rem"),
                error_text(FinanceState.col_error),
                field_label("Подъезд"),
                rx.select.root(
                    rx.select.trigger(placeholder="Выберите подъезд", width="100%"),
                    rx.select.content(
                        rx.foreach(
                            FinanceState.entrance_options,
                            lambda o: rx.select.item(o.label, value=o.id.to_string()),
                        )
                    ),
                    value=FinanceState.new_col_entrance_id,
                    on_change=FinanceState.set_new_col_entrance_id,
                    width="100%",
                ),
                rx.input(
                    placeholder="Название сбора",
                    value=FinanceState.new_col_title,
                    on_change=FinanceState.set_new_col_title,
                    width="100%",
                    margin_top="0.5rem",
                ),
                rx.text_area(
                    placeholder="Описание (необязательно)",
                    value=FinanceState.new_col_description,
                    on_change=FinanceState.set_new_col_description,
                    width="100%",
                    margin_top="0.5rem",
                    rows="2",
                ),
                rx.hstack(
                    rx.select(
                        ["ЖКХ", "Капремонт", "Домофон", "Благоустройство", "Другое"],
                        value=FinanceState.new_col_category,
                        on_change=FinanceState.set_new_col_category,
                    ),
                    rx.input(
                        placeholder="Цель, ₽",
                        value=FinanceState.new_col_amount,
                        on_change=FinanceState.set_new_col_amount,
                    ),
                    width="100%",
                    margin_top="0.5rem",
                ),
                rx.button(
                    "Запустить сбор",
                    on_click=FinanceState.create_collection,
                    width="100%",
                    margin_top="0.6rem",
                ),
                width="100%",
            )
        ),
        rx.cond(
            FinanceState.collections.length() == 0,
            empty_state("Активных сборов пока нет", "wallet"),
            rx.foreach(
                FinanceState.collections,
                lambda c: section_card(
                    rx.hstack(
                        rx.vstack(
                            rx.text(c.title, weight="bold", size="3"),
                            rx.text(
                                f"Подъезд {c.entrance_number} · {c.category}",
                                size="1",
                                color="var(--gray-9)",
                            ),
                            align="start",
                            spacing="0",
                        ),
                        rx.spacer(),
                        rx.badge(
                            rx.cond(c.is_active, "Активен", "Остановлен"),
                            color_scheme=rx.cond(c.is_active, "green", "gray"),
                        ),
                        width="100%",
                        align="start",
                    ),
                    rx.cond(
                        c.description != "",
                        rx.text(c.description, size="2", color="var(--gray-11)", margin_top="0.35rem"),
                    ),
                    progress_bar(c.progress_pct),
                    rx.hstack(
                        rx.text(c.collected_fmt, size="2", weight="bold"),
                        rx.text("из " + c.target_fmt, size="2", color="var(--gray-9)"),
                        justify="between",
                        width="100%",
                        margin_top="0.3rem",
                    ),
                    rx.button(
                        rx.cond(c.is_active, "Остановить сбор", "Возобновить сбор"),
                        size="1",
                        variant="soft",
                        width="100%",
                        margin_top="0.5rem",
                        on_click=FinanceState.toggle_collection_active(c.id),
                    ),
                ),
            ),
        ),
        width="100%",
    )


def _finance_tab() -> rx.Component:
    return rx.vstack(
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("Задолженности", value="debts"),
                rx.tabs.trigger("Сборы", value="collections"),
                width="100%",
            ),
            rx.tabs.content(_debts_section(), value="debts", padding_top="0.75rem"),
            rx.tabs.content(_collections_section(), value="collections", padding_top="0.75rem"),
            default_value="debts",
            width="100%",
        ),
        width="100%",
    )


def _profile_tab() -> rx.Component:
    return rx.vstack(
        section_card(
            rx.vstack(
                rx.heading(AuthState.display_name, size="4"),
                rx.text("Управляющая компания", size="2", color="var(--gray-9)"),
                rx.button(
                    rx.icon("log-out", size=15),
                    "Выйти",
                    variant="soft",
                    color_scheme="red",
                    size="2",
                    margin_top="0.6rem",
                    on_click=AuthState.logout,
                ),
                align="start",
                width="100%",
            )
        ),
        section_card(
            rx.vstack(
                rx.heading("Добавить дом", size="3", margin_bottom="0.4rem"),
                error_text(UKAdminState.admin_error),
                rx.hstack(
                    rx.input(
                        placeholder="Адрес дома",
                        value=UKAdminState.new_building_address,
                        on_change=UKAdminState.set_new_building_address,
                        width="100%",
                    ),
                    rx.button("Добавить", on_click=UKAdminState.add_building),
                    width="100%",
                ),
                width="100%",
            )
        ),
        rx.cond(
            UKAdminState.buildings.length() > 0,
            section_card(
                rx.vstack(
                    rx.heading("Добавить подъезд", size="3", margin_bottom="0.4rem"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Выберите дом", width="100%"),
                        rx.select.content(
                            rx.foreach(
                                UKAdminState.buildings,
                                lambda b: rx.select.item(b.address, value=b.id.to_string()),
                            )
                        ),
                        value=UKAdminState.new_entrance_building_id,
                        on_change=UKAdminState.set_new_entrance_building_id,
                        width="100%",
                    ),
                    rx.hstack(
                        rx.input(
                            placeholder="№ подъезда",
                            value=UKAdminState.new_entrance_number,
                            on_change=UKAdminState.set_new_entrance_number,
                            width="100%",
                            margin_top="0.5rem",
                        ),
                        width="100%",
                    ),
                    rx.button(
                        "Добавить подъезд",
                        on_click=UKAdminState.add_entrance,
                        width="100%",
                        margin_top="0.5rem",
                    ),
                    width="100%",
                )
            ),
        ),
        rx.cond(
            UKAdminState.buildings.length() > 1,
            section_card(
                field_label("Дом"),
                rx.select.root(
                    rx.select.trigger(width="100%"),
                    rx.select.content(
                        rx.foreach(
                            UKAdminState.buildings,
                            lambda b: rx.select.item(b.address, value=b.id.to_string()),
                        )
                    ),
                    value=UKAdminState.selected_building_id,
                    on_change=UKAdminState.set_selected_building_id,
                    width="100%",
                ),
            ),
        ),
        rx.cond(
            UKAdminState.entrances.length() == 0,
            empty_state("Добавьте дом и подъезд, чтобы получить код приглашения для жителей", "building-2"),
            rx.vstack(
                rx.heading("Подъезды и коды приглашения", size="3", margin_bottom="0.2rem"),
                rx.foreach(
                    UKAdminState.visible_entrances,
                    lambda e: section_card(
                        rx.text(f"{e.building_address} · подъезд {e.number}", weight="bold", size="2"),
                        rx.code(e.invite_code, size="4", margin_top="0.35rem"),
                        rx.text(
                            e.join_url,
                            size="1",
                            color="var(--gray-9)",
                            margin_top="0.5rem",
                            style={"word_break": "break-all"},
                        ),
                        rx.hstack(
                            rx.button(
                                rx.cond(
                                    UKAdminState.copied_entrance_id == e.id,
                                    rx.hstack(
                                        rx.icon("check", size=14),
                                        rx.text("Скопировано"),
                                        spacing="1",
                                        align="center",
                                    ),
                                    rx.hstack(
                                        rx.icon("copy", size=14),
                                        rx.text("Скопировать ссылку"),
                                        spacing="1",
                                        align="center",
                                    ),
                                ),
                                size="1",
                                variant="soft",
                                on_click=[
                                    rx.set_clipboard(e.join_url),
                                    UKAdminState.mark_copied(e.id),
                                ],
                            ),
                            width="100%",
                            margin_top="0.5rem",
                        ),
                        rx.center(
                            rx.image(
                                src=e.qr_data_uri,
                                width="140px",
                                height="140px",
                                border_radius="8px",
                                border="1px solid var(--gray-4)",
                            ),
                            width="100%",
                            padding_top="0.6rem",
                        ),
                    ),
                ),
                width="100%",
            ),
        ),
        rx.cond(
            UKAdminState.residents.length() > 0,
            section_card(
                rx.heading("Жители", size="3", margin_bottom="0.4rem"),
                rx.foreach(
                    UKAdminState.residents,
                    lambda r: rx.hstack(
                        rx.text(f"{r.full_name}", size="2"),
                        rx.spacer(),
                        rx.text(
                            f"кв. {r.apartment} · п.{r.entrance_number}",
                            size="1",
                            color="var(--gray-9)",
                        ),
                        width="100%",
                        padding_y="0.25rem",
                    ),
                ),
            ),
        ),
        width="100%",
    )


def uk_dashboard() -> rx.Component:
    body = rx.match(
        TabState.uk_tab,
        ("finance", _finance_tab()),
        ("profile", _profile_tab()),
        _news_tab(),
    )
    return phone_shell(
        body,
        bottom_tabs(UK_TABS, TabState.uk_tab, TabState.set_uk_tab),
        header=top_bar("Домовод", "Кабинет управляющей компании"),
    )
