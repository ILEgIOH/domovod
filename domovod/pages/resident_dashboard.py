"""Кабинет жителя: новости, чат/долги/сборы, профиль."""

from __future__ import annotations

import reflex as rx

from ..state import AuthState
from ..state_chat import ChatState
from ..state_finance import FinanceState
from ..state_news import NewsState
from ..tab_state import TabState
from ..ui import bottom_tabs, empty_state, error_text, phone_shell, progress_bar, section_card, top_bar

RESIDENT_TABS = [
    ("news", "Новости", "newspaper"),
    ("hub", "Дом", "message-circle"),
    ("profile", "Профиль", "user"),
]


def _news_tab() -> rx.Component:
    return rx.cond(
        NewsState.news_items.length() == 0,
        empty_state("Управляющая компания ещё не публиковала новости", "newspaper"),
        rx.foreach(
            NewsState.news_items,
            lambda n: section_card(
                rx.text(n.title, weight="bold", size="3"),
                rx.text(n.created_at, size="1", color="var(--gray-9)", margin_bottom="0.35rem"),
                rx.text(n.body, size="2", color="var(--gray-11)"),
            ),
        ),
    )


def _chat_view() -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.cond(
                ChatState.messages.length() == 0,
                empty_state("Сообщений пока нет. Напишите первым!", "message-circle"),
                rx.vstack(
                    rx.foreach(
                        ChatState.messages,
                        lambda m: rx.box(
                            rx.box(
                                rx.cond(
                                    ~m.is_mine,
                                    rx.text(m.sender_name, size="1", weight="bold", color="var(--accent-9)"),
                                ),
                                rx.text(m.text, size="2"),
                                rx.text(m.created_at, size="1", color="var(--gray-9)", text_align="right"),
                                background=rx.cond(m.is_mine, "var(--accent-4)", "var(--gray-3)"),
                                padding="0.5rem 0.7rem",
                                border_radius="12px",
                                max_width="80%",
                            ),
                            width="100%",
                            display="flex",
                            justify_content=rx.cond(m.is_mine, "flex-end", "flex-start"),
                            margin_bottom="0.4rem",
                        ),
                    ),
                    width="100%",
                ),
            ),
            width="100%",
            min_height="200px",
        ),
        rx.hstack(
            rx.input(
                placeholder="Сообщение соседям по подъезду...",
                value=ChatState.new_message,
                on_change=ChatState.set_new_message,
                on_key_down=ChatState.handle_key,
                width="100%",
            ),
            rx.icon_button(rx.icon("send", size=16), on_click=ChatState.send_message),
            width="100%",
            position="sticky",
            bottom="4.5rem",
            background="var(--gray-2)",
            padding_top="0.5rem",
        ),
        width="100%",
    )


def _debts_view() -> rx.Component:
    return rx.cond(
        FinanceState.my_debts.length() == 0,
        empty_state("Задолженностей нет", "receipt"),
        rx.foreach(
            FinanceState.my_debts,
            lambda d: section_card(
                rx.hstack(
                    rx.vstack(
                        rx.text(d.category, weight="bold", size="2"),
                        rx.text(d.period, size="1", color="var(--gray-9)"),
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
                ),
            ),
        ),
    )


def _collections_view() -> rx.Component:
    return rx.vstack(
        error_text(FinanceState.pay_error),
        rx.cond(
            FinanceState.my_collections.length() == 0,
            empty_state("Активных сборов в вашем подъезде нет", "wallet"),
            rx.foreach(
                FinanceState.my_collections,
                lambda c: section_card(
                    rx.text(c.title, weight="bold", size="3"),
                    rx.cond(
                        c.description != "",
                        rx.text(c.description, size="2", color="var(--gray-11)", margin_top="0.25rem"),
                    ),
                    progress_bar(c.progress_pct),
                    rx.hstack(
                        rx.text(c.collected_fmt, size="2", weight="bold"),
                        rx.text("из " + c.target_fmt, size="2", color="var(--gray-9)"),
                        justify="between",
                        width="100%",
                        margin_top="0.3rem",
                    ),
                    rx.cond(
                        c.my_contribution > 0,
                        rx.text(
                            "Ваш взнос: " + c.my_contribution_fmt,
                            size="1",
                            color="var(--accent-9)",
                            margin_top="0.2rem",
                        ),
                    ),
                    rx.cond(
                        c.my_payment_pending,
                        rx.badge("Платёж обрабатывается...", color_scheme="amber", margin_top="0.4rem"),
                        rx.cond(
                            c.remaining > 0,
                            rx.button(
                                rx.icon("credit-card", size=15),
                                "Внести " + c.remaining_fmt,
                                width="100%",
                                margin_top="0.5rem",
                                on_click=FinanceState.pay_collection(c.id, c.remaining),
                            ),
                            rx.badge("Сбор закрыт", color_scheme="green", margin_top="0.4rem"),
                        ),
                    ),
                ),
            ),
        ),
        width="100%",
    )


def _hub_tab() -> rx.Component:
    return rx.tabs.root(
        rx.tabs.list(
            rx.tabs.trigger("Чат", value="chat"),
            rx.tabs.trigger("Долги", value="debts"),
            rx.tabs.trigger("Сборы", value="collections"),
            width="100%",
        ),
        rx.tabs.content(_chat_view(), value="chat", padding_top="0.75rem"),
        rx.tabs.content(_debts_view(), value="debts", padding_top="0.75rem"),
        rx.tabs.content(_collections_view(), value="collections", padding_top="0.75rem"),
        value=TabState.resident_sub_tab,
        on_change=TabState.set_resident_sub_tab,
        width="100%",
    )


def _profile_tab() -> rx.Component:
    return rx.vstack(
        section_card(
            rx.vstack(
                rx.heading(AuthState.display_name, size="4"),
                rx.text(f"Квартира {AuthState.apartment}", size="2", color="var(--gray-9)"),
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
        width="100%",
    )


def resident_dashboard() -> rx.Component:
    body = rx.match(
        TabState.resident_tab,
        ("hub", _hub_tab()),
        ("profile", _profile_tab()),
        _news_tab(),
    )
    return phone_shell(
        body,
        bottom_tabs(RESIDENT_TABS, TabState.resident_tab, TabState.set_resident_tab),
        header=top_bar("Домовод", f"Кв. {AuthState.apartment}"),
    )
