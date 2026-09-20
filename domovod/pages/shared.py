"""Общие экраны «Дом» и «Контакты» — одинаковая структура для УК и жителя,
разница только в правах (создавать/редактировать может УК, житель — предлагать и голосовать).
"""

from __future__ import annotations

import reflex as rx

from ..state import AuthState
from ..state_community import CommunityState
from ..state_contacts import ContactsState
from ..state_finance import FinanceState
from ..state_news import ICON_CHOICES, NewsState
from ..state_uk_admin import UKAdminState
from ..ui import CARD_BG, error_text, field_label, progress_bar, section_card

ICON_COLORS = {
    "zap": "amber",
    "droplet": "blue",
    "wrench": "gray",
    "triangle-alert": "red",
    "megaphone": "violet",
    "bell": "teal",
}


# ==================================================================== Дом ===


def _identity_card() -> rx.Component:
    return section_card(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.heading(AuthState.display_name, size="4"),
                    rx.cond(
                        AuthState.is_uk,
                        rx.badge("Админ", color_scheme="teal"),
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.cond(
                    AuthState.is_resident,
                    rx.text(f"Квартира {AuthState.apartment}", size="2", color="var(--gray-9)"),
                ),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            rx.icon_button(
                rx.icon("log-out", size=16),
                variant="ghost",
                color_scheme="red",
                on_click=AuthState.logout,
            ),
            width="100%",
            align="center",
        ),
    )


def _entrance_picker() -> rx.Component:
    return rx.cond(
        AuthState.is_uk,
        rx.cond(
            UKAdminState.entrances.length() == 0,
            rx.text(
                "Добавьте дом и подъезд в «Контактах», чтобы открыть экран «Дом»",
                size="2",
                color="var(--gray-9)",
            ),
            rx.vstack(
                rx.cond(
                    UKAdminState.buildings.length() > 1,
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
                rx.select.root(
                    rx.select.trigger(placeholder="Выберите подъезд", width="100%"),
                    rx.select.content(
                        rx.foreach(
                            UKAdminState.visible_entrances,
                            lambda e: rx.select.item(
                                e.building_address + " · подъезд " + e.number.to_string(),
                                value=e.id.to_string(),
                            ),
                        )
                    ),
                    value=AuthState.viewing_entrance_id.to_string(),
                    on_change=[
                        AuthState.set_viewing_entrance_id,
                        CommunityState.load_community,
                        ContactsState.load_contacts,
                    ],
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
        ),
        rx.text(
            AuthState.home_label,
            size="2",
            weight="medium",
            color="var(--gray-10)",
        ),
    )


def _icon_picker(value, on_change) -> rx.Component:
    return rx.select.root(
        rx.select.trigger(width="100%"),
        rx.select.content(rx.foreach(ICON_CHOICES, lambda i: rx.select.item(i, value=i))),
        value=value,
        on_change=on_change,
        width="100%",
    )


def _announcement_pill(n) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.icon(n.icon, size=15),
            rx.text(n.title, weight="bold", size="2"),
            rx.cond(
                AuthState.is_uk,
                rx.icon_button(
                    rx.icon("x", size=12),
                    size="1",
                    variant="ghost",
                    on_click=NewsState.delete_news(n.id),
                ),
            ),
            spacing="2",
            align="center",
        ),
        rx.text(n.body, size="1", margin_top="0.15rem"),
        background=f"var(--{ICON_COLORS.get(n.icon, 'teal')}-4)",
        border_radius="999px",
        padding="0.5rem 0.9rem",
        white_space="nowrap",
        display="inline-block",
        margin_right="0.5rem",
    )


def _announcements_row() -> rx.Component:
    return rx.vstack(
        rx.cond(
            NewsState.news_items.length() == 0,
            rx.text("Объявлений пока нет", size="2", color="var(--gray-9)"),
            rx.box(
                rx.foreach(NewsState.news_items, _announcement_pill),
                width="100%",
                overflow_x="auto",
                padding_bottom="0.4rem",
                white_space="nowrap",
            ),
        ),
        rx.cond(
            AuthState.is_uk,
            section_card(
                error_text(NewsState.news_error),
                field_label("Заголовок"),
                rx.input(
                    value=NewsState.new_title,
                    on_change=NewsState.set_new_title,
                    placeholder="Отключение света",
                    width="100%",
                    margin_bottom="0.5rem",
                ),
                field_label("Детали"),
                rx.input(
                    value=NewsState.new_body,
                    on_change=NewsState.set_new_body,
                    placeholder="6 сен. с 10 до 18",
                    width="100%",
                    margin_bottom="0.5rem",
                ),
                field_label("Иконка"),
                _icon_picker(NewsState.new_icon, NewsState.set_new_icon),
                rx.button(
                    rx.icon("plus", size=15),
                    "Добавить объявление",
                    width="100%",
                    margin_top="0.6rem",
                    on_click=NewsState.create_news,
                ),
            ),
        ),
        width="100%",
        spacing="2",
    )


def _proposed_collection_card(c) -> rx.Component:
    return section_card(
        rx.hstack(
            rx.badge("Предложено", color_scheme="amber"),
            rx.cond(
                c.proposed_by_name != "",
                rx.text(c.proposed_by_name, size="1", color="var(--gray-9)"),
            ),
            spacing="2",
            align="center",
        ),
        rx.text(c.title, weight="bold", size="3", margin_top="0.3rem"),
        rx.cond(c.description != "", rx.text(c.description, size="2", color="var(--gray-11)")),
        rx.hstack(
            rx.text(c.target_fmt, size="2", weight="bold"),
            rx.cond(
                c.end_date_fmt != "",
                rx.text("до " + c.end_date_fmt, size="2", color="var(--gray-9)"),
            ),
            justify="between",
            width="100%",
            margin_top="0.3rem",
        ),
        rx.hstack(
            rx.button(
                "Отклонить",
                variant="soft",
                color_scheme="red",
                size="1",
                width="100%",
                on_click=FinanceState.reject_collection(c.id),
            ),
            rx.button(
                "Опубликовать",
                size="1",
                width="100%",
                on_click=FinanceState.publish_collection(c.id),
            ),
            width="100%",
            margin_top="0.5rem",
        ),
    )


def _published_collection_card(c) -> rx.Component:
    return section_card(
        rx.text(c.title, weight="bold", size="3"),
        rx.cond(c.description != "", rx.text(c.description, size="2", color="var(--gray-11)", margin_top="0.2rem")),
        progress_bar(c.progress_pct),
        rx.hstack(
            rx.text(c.collected_fmt, size="2", weight="bold"),
            rx.text("из " + c.target_fmt, size="2", color="var(--gray-9)"),
            justify="between",
            width="100%",
            margin_top="0.3rem",
        ),
        rx.cond(
            AuthState.is_uk,
            rx.button(
                rx.cond(c.is_active, "Остановить сбор", "Возобновить сбор"),
                size="1",
                variant="soft",
                width="100%",
                margin_top="0.5rem",
                on_click=FinanceState.toggle_collection_active(c.id),
            ),
        ),
        rx.cond(
            AuthState.is_resident,
            rx.fragment(
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
    )


def _debt_row(d, clickable: bool = False) -> rx.Component:
    badge = rx.badge(
        rx.cond(d.is_paid, "Оплачено", "Долг"),
        color_scheme=rx.cond(d.is_paid, "green", "red"),
        **(
            {"cursor": "pointer", "on_click": FinanceState.toggle_debt_paid(d.id)}
            if clickable
            else {}
        ),
    )
    return rx.hstack(
        rx.vstack(
            rx.text(d.resident_name + " · кв. " + d.apartment, weight="bold", size="2"),
            rx.text(d.category + " · " + d.period, size="1", color="var(--gray-9)"),
            align="start",
            spacing="0",
        ),
        rx.spacer(),
        rx.vstack(
            rx.text(d.amount_fmt, weight="bold"),
            badge,
            align="end",
            spacing="1",
        ),
        width="100%",
        align="start",
    )


def _debts_block() -> rx.Component:
    return rx.vstack(
        rx.heading("Долги", size="4", margin_bottom="0.2rem"),
        rx.cond(
            AuthState.is_uk,
            rx.fragment(
                section_card(
                    error_text(FinanceState.debt_error),
                    field_label("Житель"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Выберите жителя", width="100%"),
                        rx.select.content(
                            rx.foreach(
                                FinanceState.home_resident_options,
                                lambda o: rx.select.item(o.label, value=o.id.to_string()),
                            )
                        ),
                        value=FinanceState.new_debt_resident_id,
                        on_change=FinanceState.set_new_debt_resident_id,
                        width="100%",
                    ),
                    rx.input(
                        placeholder="Период, напр. Август 2026",
                        value=FinanceState.new_debt_period,
                        on_change=FinanceState.set_new_debt_period,
                        width="100%",
                        margin_top="0.5rem",
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
                        width="100%",
                        margin_top="0.6rem",
                        on_click=FinanceState.add_debt,
                    ),
                ),
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("Активные", value="active"),
                        rx.tabs.trigger("История", value="history"),
                        width="100%",
                    ),
                    rx.tabs.content(
                        rx.cond(
                            FinanceState.home_active_debts.length() == 0,
                            rx.text("Задолженностей нет", size="2", color="var(--gray-9)", padding_top="0.5rem"),
                            rx.foreach(FinanceState.home_active_debts, lambda d: section_card(_debt_row(d, clickable=True))),
                        ),
                        value="active",
                        padding_top="0.6rem",
                    ),
                    rx.tabs.content(
                        rx.cond(
                            FinanceState.home_paid_debts.length() == 0,
                            rx.text("Пока пусто", size="2", color="var(--gray-9)", padding_top="0.5rem"),
                            rx.foreach(FinanceState.home_paid_debts, lambda d: section_card(_debt_row(d, clickable=True))),
                        ),
                        value="history",
                        padding_top="0.6rem",
                    ),
                    default_value="active",
                    width="100%",
                ),
            ),
            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger("Активные", value="active"),
                    rx.tabs.trigger("История", value="history"),
                    width="100%",
                ),
                rx.tabs.content(
                    rx.cond(
                        FinanceState.active_my_debts.length() == 0,
                        rx.text("Задолженностей нет", size="2", color="var(--gray-9)", padding_top="0.5rem"),
                        rx.foreach(FinanceState.active_my_debts, lambda d: section_card(_debt_row(d))),
                    ),
                    value="active",
                    padding_top="0.6rem",
                ),
                rx.tabs.content(
                    rx.cond(
                        FinanceState.paid_my_debts.length() == 0,
                        rx.text("Пока пусто", size="2", color="var(--gray-9)", padding_top="0.5rem"),
                        rx.foreach(FinanceState.paid_my_debts, lambda d: section_card(_debt_row(d))),
                    ),
                    value="history",
                    padding_top="0.6rem",
                ),
                default_value="active",
                width="100%",
            ),
        ),
        width="100%",
        spacing="2",
    )


def _collections_block() -> rx.Component:
    return rx.vstack(
        rx.heading("Сборы", size="4", margin_bottom="0.2rem"),
        error_text(FinanceState.pay_error),
        rx.cond(
            AuthState.is_uk,
            rx.fragment(
                rx.cond(
                    FinanceState.home_proposed_collections.length() > 0,
                    rx.vstack(
                        rx.hstack(
                            rx.text("Предложенные", weight="bold", size="2"),
                            rx.badge(FinanceState.home_proposed_collections.length().to_string()),
                            spacing="2",
                        ),
                        rx.foreach(FinanceState.home_proposed_collections, _proposed_collection_card),
                        width="100%",
                    ),
                ),
                section_card(
                    error_text(FinanceState.col_error),
                    field_label("Название"),
                    rx.input(
                        value=FinanceState.new_col_title,
                        on_change=FinanceState.set_new_col_title,
                        placeholder="Покраска лифта",
                        width="100%",
                        margin_bottom="0.5rem",
                    ),
                    rx.text_area(
                        placeholder="Описание (необязательно)",
                        value=FinanceState.new_col_description,
                        on_change=FinanceState.set_new_col_description,
                        width="100%",
                        margin_bottom="0.5rem",
                        rows="2",
                    ),
                    rx.hstack(
                        rx.input(
                            placeholder="Сумма, ₽",
                            value=FinanceState.new_col_amount,
                            on_change=FinanceState.set_new_col_amount,
                        ),
                        rx.input(
                            placeholder="До (дд.мм.гггг)",
                            value=FinanceState.new_col_end_date,
                            on_change=FinanceState.set_new_col_end_date,
                        ),
                        width="100%",
                    ),
                    rx.button(
                        "Запустить сбор",
                        width="100%",
                        margin_top="0.6rem",
                        on_click=FinanceState.create_collection,
                    ),
                ),
            ),
        ),
        rx.cond(
            AuthState.is_resident,
            section_card(
                error_text(FinanceState.propose_error),
                rx.text("Предложить сбор", weight="bold", size="2", margin_bottom="0.4rem"),
                rx.input(
                    value=FinanceState.propose_col_title,
                    on_change=FinanceState.set_propose_col_title,
                    placeholder="Название",
                    width="100%",
                    margin_bottom="0.5rem",
                ),
                rx.text_area(
                    placeholder="Описание",
                    value=FinanceState.propose_col_description,
                    on_change=FinanceState.set_propose_col_description,
                    width="100%",
                    margin_bottom="0.5rem",
                    rows="2",
                ),
                rx.hstack(
                    rx.input(
                        placeholder="Сумма, ₽",
                        value=FinanceState.propose_col_amount,
                        on_change=FinanceState.set_propose_col_amount,
                    ),
                    rx.input(
                        placeholder="До (дд.мм.гггг)",
                        value=FinanceState.propose_col_end_date,
                        on_change=FinanceState.set_propose_col_end_date,
                    ),
                    width="100%",
                ),
                rx.button(
                    "Предложить",
                    width="100%",
                    margin_top="0.6rem",
                    variant="soft",
                    on_click=FinanceState.propose_collection,
                ),
            ),
        ),
        rx.cond(
            AuthState.is_uk,
            rx.foreach(FinanceState.home_published_collections, _published_collection_card),
            rx.foreach(FinanceState.my_collections, _published_collection_card),
        ),
        width="100%",
        spacing="2",
    )


def _initiatives_block() -> rx.Component:
    return rx.vstack(
        rx.heading("Инициативы", size="4", margin_bottom="0.2rem"),
        rx.cond(
            CommunityState.initiatives.length() == 0,
            rx.text("Инициатив пока нет", size="2", color="var(--gray-9)"),
            rx.foreach(
                CommunityState.initiatives,
                lambda i: section_card(
                    rx.hstack(
                        rx.vstack(
                            rx.text(i.title, weight="bold", size="2"),
                            rx.cond(
                                i.description != "",
                                rx.text(i.description, size="1", color="var(--gray-9)"),
                            ),
                            align="start",
                            spacing="0",
                        ),
                        rx.spacer(),
                        rx.text(
                            i.votes.to_string() + "/" + i.needed_count.to_string(),
                            size="2",
                            weight="bold",
                        ),
                        width="100%",
                        align="start",
                    ),
                    rx.cond(
                        AuthState.is_resident,
                        rx.button(
                            rx.cond(i.i_voted, "Я не за", "Я за!"),
                            size="1",
                            width="100%",
                            margin_top="0.4rem",
                            variant=rx.cond(i.i_voted, "soft", "solid"),
                            on_click=CommunityState.toggle_initiative_vote(i.id),
                        ),
                    ),
                ),
            ),
        ),
        rx.cond(
            AuthState.is_uk,
            section_card(
                error_text(CommunityState.initiative_error),
                rx.input(
                    value=CommunityState.new_initiative_title,
                    on_change=CommunityState.set_new_initiative_title,
                    placeholder="Субботник",
                    width="100%",
                    margin_bottom="0.5rem",
                ),
                rx.text_area(
                    placeholder="Описание",
                    value=CommunityState.new_initiative_description,
                    on_change=CommunityState.set_new_initiative_description,
                    width="100%",
                    margin_bottom="0.5rem",
                    rows="2",
                ),
                rx.input(
                    placeholder="Нужно человек",
                    value=CommunityState.new_initiative_needed,
                    on_change=CommunityState.set_new_initiative_needed,
                    width="100%",
                ),
                rx.button(
                    "Создать инициативу",
                    width="100%",
                    margin_top="0.6rem",
                    on_click=CommunityState.create_initiative,
                ),
            ),
        ),
        width="100%",
        spacing="2",
    )


def _polls_block() -> rx.Component:
    return rx.vstack(
        rx.heading("Опросы", size="4", margin_bottom="0.2rem"),
        rx.cond(
            CommunityState.polls.length() == 0,
            rx.text("Опросов пока нет", size="2", color="var(--gray-9)"),
            rx.foreach(
                CommunityState.polls,
                lambda p: section_card(
                    rx.hstack(
                        rx.vstack(
                            rx.text(p.title, weight="bold", size="2"),
                            rx.cond(
                                p.description != "",
                                rx.text(p.description, size="1", color="var(--gray-9)"),
                            ),
                            align="start",
                            spacing="0",
                        ),
                        rx.spacer(),
                        rx.text(p.votes.to_string() + " чел. одобрили", size="1", color="var(--gray-9)"),
                        width="100%",
                        align="start",
                    ),
                    rx.cond(
                        AuthState.is_resident,
                        rx.button(
                            rx.cond(p.i_voted, "Я не за", "Я за!"),
                            size="1",
                            width="100%",
                            margin_top="0.4rem",
                            variant=rx.cond(p.i_voted, "soft", "solid"),
                            on_click=CommunityState.toggle_poll_vote(p.id),
                        ),
                    ),
                ),
            ),
        ),
        rx.cond(
            AuthState.is_uk,
            section_card(
                error_text(CommunityState.poll_error),
                rx.input(
                    value=CommunityState.new_poll_title,
                    on_change=CommunityState.set_new_poll_title,
                    placeholder="Камера на домофон",
                    width="100%",
                    margin_bottom="0.5rem",
                ),
                rx.text_area(
                    placeholder="Описание",
                    value=CommunityState.new_poll_description,
                    on_change=CommunityState.set_new_poll_description,
                    width="100%",
                    margin_bottom="0.5rem",
                    rows="2",
                ),
                rx.button(
                    "Создать опрос",
                    width="100%",
                    on_click=CommunityState.create_poll,
                ),
            ),
        ),
        width="100%",
        spacing="2",
    )


def home_tab() -> rx.Component:
    return rx.vstack(
        _identity_card(),
        _entrance_picker(),
        rx.cond(
            AuthState.viewing_entrance_id != 0,
            rx.vstack(
                _announcements_row(),
                _debts_block(),
                _collections_block(),
                _initiatives_block(),
                _polls_block(),
                width="100%",
                spacing="4",
            ),
        ),
        width="100%",
        spacing="3",
    )


# ============================================================== Контакты ===


def _personal_contacts_block() -> rx.Component:
    return section_card(
        rx.heading("Контакты", size="4", margin_bottom="0.4rem"),
        error_text(ContactsState.contact_error),
        rx.cond(
            ContactsState.personal_contacts.length() == 0,
            rx.text("Пока пусто", size="2", color="var(--gray-9)"),
            rx.foreach(
                ContactsState.personal_contacts,
                lambda c: rx.hstack(
                    rx.vstack(
                        rx.text(c.name, weight="bold", size="2"),
                        rx.cond(c.phone != "", rx.text(c.phone, size="1", color="var(--gray-9)")),
                        align="start",
                        spacing="0",
                    ),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon("x", size=13),
                        variant="ghost",
                        size="1",
                        on_click=ContactsState.delete_contact(c.id),
                    ),
                    width="100%",
                    padding_y="0.25rem",
                ),
            ),
        ),
        rx.hstack(
            rx.input(
                placeholder="Имя",
                value=ContactsState.new_contact_name,
                on_change=ContactsState.set_new_contact_name,
                width="100%",
            ),
            rx.input(
                placeholder="Телефон",
                value=ContactsState.new_contact_phone,
                on_change=ContactsState.set_new_contact_phone,
                width="100%",
            ),
            width="100%",
            margin_top="0.5rem",
        ),
        rx.button(
            rx.icon("plus", size=14),
            "Добавить контакт",
            size="2",
            variant="soft",
            width="100%",
            margin_top="0.5rem",
            on_click=ContactsState.add_contact,
        ),
    )


def _useful_addresses_block() -> rx.Component:
    return section_card(
        rx.heading("Полезные адреса", size="4", margin_bottom="0.4rem"),
        rx.cond(
            ContactsState.useful_addresses.length() == 0,
            rx.text("Пока не добавлены", size="2", color="var(--gray-9)"),
            rx.foreach(
                ContactsState.useful_addresses,
                lambda a: rx.hstack(
                    rx.vstack(
                        rx.text(a.title, weight="bold", size="2"),
                        rx.text(a.value, size="1", color="var(--gray-9)"),
                        align="start",
                        spacing="0",
                    ),
                    rx.spacer(),
                    rx.cond(
                        AuthState.is_uk,
                        rx.icon_button(
                            rx.icon("x", size=13),
                            variant="ghost",
                            size="1",
                            on_click=ContactsState.delete_address(a.id),
                        ),
                    ),
                    width="100%",
                    padding_y="0.25rem",
                ),
            ),
        ),
        rx.cond(
            AuthState.is_uk,
            rx.fragment(
                error_text(ContactsState.address_error),
                rx.hstack(
                    rx.input(
                        placeholder="Название",
                        value=ContactsState.new_address_title,
                        on_change=ContactsState.set_new_address_title,
                        width="100%",
                    ),
                    rx.input(
                        placeholder="Адрес/телефон",
                        value=ContactsState.new_address_value,
                        on_change=ContactsState.set_new_address_value,
                        width="100%",
                    ),
                    width="100%",
                    margin_top="0.5rem",
                ),
                rx.button(
                    rx.icon("plus", size=14),
                    "Добавить адрес",
                    size="2",
                    variant="soft",
                    width="100%",
                    margin_top="0.5rem",
                    on_click=ContactsState.add_address,
                ),
            ),
        ),
    )


def _buildings_block() -> rx.Component:
    return rx.vstack(
        section_card(
            rx.heading("Добавить дом", size="4", margin_bottom="0.4rem"),
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
        ),
        rx.cond(
            UKAdminState.buildings.length() > 0,
            section_card(
                rx.heading("Добавить подъезд", size="4", margin_bottom="0.4rem"),
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
                rx.input(
                    placeholder="№ подъезда",
                    value=UKAdminState.new_entrance_number,
                    on_change=UKAdminState.set_new_entrance_number,
                    width="100%",
                    margin_top="0.5rem",
                ),
                rx.button(
                    "Добавить подъезд",
                    width="100%",
                    margin_top="0.5rem",
                    on_click=UKAdminState.add_entrance,
                ),
            ),
        ),
        width="100%",
        spacing="3",
    )


def _invite_block() -> rx.Component:
    entrance = UKAdminState.current_entrance
    return rx.cond(
        entrance,
        section_card(
            rx.heading("Пригласить жителя", size="4", margin_bottom="0.4rem"),
            rx.text(
                entrance.building_address + " · подъезд " + entrance.number.to_string(),
                size="2",
                weight="medium",
                margin_bottom="0.5rem",
            ),
            rx.code(entrance.invite_code, size="5"),
            rx.text(
                entrance.join_url,
                size="1",
                color="var(--gray-9)",
                margin_top="0.5rem",
                style={"word_break": "break-all"},
            ),
            rx.hstack(
                rx.button(
                    rx.cond(
                        UKAdminState.copied_entrance_id == entrance.id,
                        rx.hstack(rx.icon("check", size=14), rx.text("Скопировано"), spacing="1"),
                        rx.hstack(rx.icon("copy", size=14), rx.text("Скопировать ссылку"), spacing="1"),
                    ),
                    size="1",
                    variant="soft",
                    width="100%",
                    on_click=[rx.set_clipboard(entrance.join_url), UKAdminState.mark_copied(entrance.id)],
                ),
                width="100%",
                margin_top="0.5rem",
            ),
            rx.center(
                rx.image(src=entrance.qr_data_uri, width="140px", height="140px", border_radius="8px"),
                width="100%",
                padding_top="0.6rem",
            ),
            rx.cond(
                UKAdminState.confirm_regenerate_entrance_id == entrance.id,
                rx.vstack(
                    rx.text(
                        "Точно? Старые код и ссылка перестанут действовать, "
                        "создадутся новые.",
                        size="1",
                        color="var(--red-10)",
                        margin_top="0.5rem",
                    ),
                    rx.hstack(
                        rx.button(
                            "Нет", variant="soft", width="100%", size="1",
                            on_click=UKAdminState.cancel_regenerate_code,
                        ),
                        rx.button(
                            "Да", color_scheme="red", width="100%", size="1",
                            on_click=UKAdminState.regenerate_invite_code,
                        ),
                        width="100%",
                    ),
                    width="100%",
                ),
                rx.button(
                    rx.icon("refresh-cw", size=14),
                    "Обновить код",
                    variant="ghost",
                    size="1",
                    width="100%",
                    margin_top="0.5rem",
                    on_click=UKAdminState.ask_regenerate_code(entrance.id),
                ),
            ),
        ),
    )


def _residents_block() -> rx.Component:
    return section_card(
        rx.heading("Жители", size="4", margin_bottom="0.4rem"),
        rx.cond(
            UKAdminState.residents.length() == 0,
            rx.text("Пока никто не присоединился", size="2", color="var(--gray-9)"),
            rx.foreach(
                UKAdminState.residents,
                lambda r: rx.hstack(
                    rx.text(r.full_name, size="2"),
                    rx.spacer(),
                    rx.text(
                        "кв. " + r.apartment + " · п." + r.entrance_number.to_string(),
                        size="1",
                        color="var(--gray-9)",
                    ),
                    width="100%",
                    padding_y="0.25rem",
                ),
            ),
        ),
    )


def contacts_tab() -> rx.Component:
    return rx.vstack(
        rx.cond(
            AuthState.is_uk,
            rx.fragment(_buildings_block(), _invite_block(), _residents_block()),
        ),
        _personal_contacts_block(),
        _useful_addresses_block(),
        width="100%",
        spacing="3",
    )
