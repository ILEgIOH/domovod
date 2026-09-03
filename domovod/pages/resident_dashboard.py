"""Кабинет жителя: новости, долги/сборы, профиль."""

from __future__ import annotations

import reflex as rx

from ..state import AuthState
from ..state_finance import FinanceState
from ..state_news import NewsState
from ..tab_state import TabState
from ..ui import bottom_tabs, empty_state, error_text, phone_shell, progress_bar, section_card, top_bar

RESIDENT_TABS = [
    ("news", "Новости", "newspaper"),
    ("finance", "Долги и сборы", "wallet"),
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


def _my_debt_list(items, empty_text: str) -> rx.Component:
    return rx.cond(
        items.length() == 0,
        empty_state(empty_text, "receipt"),
        rx.foreach(
            items,
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


def _debts_view() -> rx.Component:
    return rx.tabs.root(
        rx.tabs.list(
            rx.tabs.trigger("Активные", value="active"),
            rx.tabs.trigger("История", value="history"),
            width="100%",
        ),
        rx.tabs.content(
            _my_debt_list(FinanceState.active_my_debts, "Задолженностей нет"),
            value="active",
            padding_top="0.6rem",
        ),
        rx.tabs.content(
            _my_debt_list(FinanceState.paid_my_debts, "Оплаченных начислений пока нет"),
            value="history",
            padding_top="0.6rem",
        ),
        default_value="active",
        width="100%",
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


def _finance_tab() -> rx.Component:
    return rx.tabs.root(
        rx.tabs.list(
            rx.tabs.trigger("Долги", value="debts"),
            rx.tabs.trigger("Сборы", value="collections"),
            width="100%",
        ),
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
        ("finance", _finance_tab()),
        ("profile", _profile_tab()),
        _news_tab(),
    )
    return phone_shell(
        body,
        bottom_tabs(RESIDENT_TABS, TabState.resident_tab, TabState.set_resident_tab),
        header=top_bar("Домовод", f"Кв. {AuthState.apartment}"),
    )
