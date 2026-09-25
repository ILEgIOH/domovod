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
from ..state_proposals import ProposalsState
from ..state_uk_admin import UKAdminState
from ..ui import (
    BRAND_ACTION_TEXT,
    BRAND_NEON,
    BRAND_PURPLE,
    BRAND_PURPLE_TINT,
    CARD_BG,
    MAX_WIDTH,
    TEXT_PRIMARY,
    error_text,
    field_label,
    progress_bar,
    section_card,
)

def _icon_bg_color(icon) -> rx.Var:
    """Цвет плашки объявления по иконке. `icon` — реактивный Var (элемент
    foreach), поэтому обычный dict.get() тут не работает: ключом становится
    сам объект Var, а не строка, и всегда попадает в default.
    """
    return rx.match(
        icon,
        ("zap", "var(--amber-9)"),
        ("droplet", "var(--blue-9)"),
        ("wrench", "var(--gray-9)"),
        ("triangle-alert", "var(--red-9)"),
        ("megaphone", "var(--violet-9)"),
        "var(--iris-9)",
    )


# ==================================================================== Дом ===


def _avatar() -> rx.Component:
    return rx.box(
        rx.icon("user-round", size=22, color="var(--gray-11)"),
        width="44px",
        height="44px",
        border_radius="999px",
        background="var(--gray-4)",
        display="flex",
        align_items="center",
        justify_content="center",
        flex_shrink="0",
    )


def _identity_card() -> rx.Component:
    return section_card(
        rx.hstack(
            _avatar(),
            rx.vstack(
                rx.hstack(
                    rx.heading(AuthState.display_name, size="4"),
                    rx.cond(
                        AuthState.is_uk,
                        rx.badge("Админ", color_scheme="iris"),
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.cond(
                    AuthState.is_resident,
                    rx.text(f"Квартира {AuthState.apartment}", size="2", color="var(--gray-9)"),
                ),
                spacing="0",
                align="start",
            ),
            rx.spacer(),
            rx.cond(
                AuthState.is_resident,
                rx.icon_button(
                    rx.icon("clipboard-list", size=16),
                    variant="ghost",
                    color_scheme="gray",
                    size="1",
                    on_click=ProposalsState.open_my_proposals,
                ),
            ),
            rx.icon_button(
                rx.icon("log-out", size=16),
                variant="ghost",
                color_scheme="gray",
                size="1",
                on_click=AuthState.logout,
            ),
            width="100%",
            align="center",
            spacing="3",
        ),
    )


def _home_header() -> rx.Component:
    """Заголовок с адресом/подъездом — у УК кликабелен и открывает переключатель."""
    return rx.cond(
        AuthState.is_uk,
        rx.cond(
            UKAdminState.current_entrance,
            rx.popover.root(
                rx.popover.trigger(
                    rx.vstack(
                        rx.hstack(
                            rx.heading(UKAdminState.current_entrance.building_address, size="5"),
                            rx.icon("chevron-right", size=18, color="var(--gray-9)"),
                            spacing="1",
                            align="center",
                        ),
                        rx.text(
                            "Подъезд " + UKAdminState.current_entrance.number.to_string(),
                            size="2",
                            color="var(--gray-9)",
                        ),
                        spacing="0",
                        align="start",
                        cursor="pointer",
                    ),
                ),
                rx.popover.content(
                    rx.vstack(
                        rx.foreach(
                            UKAdminState.entrances,
                            lambda e: rx.popover.close(
                                rx.hstack(
                                    rx.text(
                                        e.building_address + " · подъезд " + e.number.to_string(),
                                        size="2",
                                    ),
                                    rx.spacer(),
                                    rx.cond(
                                        e.id == AuthState.viewing_entrance_id,
                                        rx.icon("check", size=14, color="var(--accent-9)"),
                                    ),
                                    width="100%",
                                    cursor="pointer",
                                    padding="0.4rem 0.2rem",
                                    on_click=[
                                        AuthState.set_viewing_entrance_id(e.id.to_string()),
                                        CommunityState.load_community,
                                        ContactsState.load_contacts,
                                    ],
                                ),
                            ),
                        ),
                        spacing="1",
                        min_width="220px",
                    ),
                ),
            ),
            rx.text(
                "Добавьте дом и подъезд в «Контактах», чтобы открыть экран «Дом»",
                size="2",
                color="var(--gray-9)",
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
        rx.cond(
            AuthState.is_uk,
            rx.icon_button(
                rx.icon("x", size=11),
                size="1",
                variant="ghost",
                color_scheme="gray",
                on_click=NewsState.delete_news(n.id),
                position="absolute",
                top="0.3rem",
                right="0.3rem",
                background="rgba(255,255,255,0.18)",
                border_radius="999px",
            ),
        ),
        rx.hstack(
            rx.icon(n.icon, size=15, color="white"),
            rx.text(n.title, weight="bold", size="2", color="white"),
            spacing="2",
            align="center",
        ),
        rx.text(n.body, size="1", color="rgba(255,255,255,0.8)", margin_top="0.15rem"),
        background=_icon_bg_color(n.icon),
        border_radius="14px",
        padding="0.6rem 0.9rem",
        white_space="nowrap",
        display="inline-block",
        position="relative",
        margin_right="0.5rem",
        min_width="160px",
    )


def _announcements_row() -> rx.Component:
    return rx.cond(
        NewsState.news_items.length() == 0,
        rx.text("Объявлений пока нет", size="2", color="var(--gray-9)"),
        rx.box(
            rx.foreach(NewsState.news_items, _announcement_pill),
            width="100%",
            overflow_x="auto",
            padding_bottom="0.4rem",
            white_space="nowrap",
        ),
    )


def _announcement_form() -> rx.Component:
    return rx.vstack(
        error_text(NewsState.news_error),
        field_label("Заголовок"),
        rx.input(
            value=NewsState.new_title,
            on_change=NewsState.set_new_title,
            placeholder="Отключение света",
            width="100%",
        ),
        field_label("Детали"),
        rx.input(
            value=NewsState.new_body,
            on_change=NewsState.set_new_body,
            placeholder="6 сен. с 10 до 18",
            width="100%",
        ),
        field_label("Иконка"),
        _icon_picker(NewsState.new_icon, NewsState.set_new_icon),
        rx.button(
            rx.icon("plus", size=15),
            "Добавить объявление",
            width="100%",
            margin_top="0.4rem",
            on_click=NewsState.create_news,
        ),
        width="100%",
        spacing="2",
        align="start",
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
                flex="1",
                on_click=ProposalsState.open_reject("collection", c.id, c.title),
            ),
            rx.button(
                "Опубликовать",
                size="1",
                flex="1",
                on_click=FinanceState.publish_collection(c.id),
            ),
            width="100%",
            margin_top="0.5rem",
        ),
    )


def _published_collection_card(c) -> rx.Component:
    """C01/C02/C05: карточка сбора — статус, крупная сумма, прогресс,
    описание и действие. В нашем продукте оплата настоящая (ЮKassa), в
    отличие от спеки, где это просто отметка намерения — см. решение
    пользователя оставить реальные платежи; поэтому шаг «Как передать
    деньги» (C03) и отмена отметки (C04) здесь не нужны."""
    return rx.vstack(
        rx.heading(c.title, size="6", weight="bold", margin_bottom="0.1rem"),
        rx.cond(
            c.proposed_by_name != "",
            rx.text(c.proposed_by_name + " · инициатор", size="2", color="var(--gray-9)", margin_bottom="0.6rem"),
        ),
        rx.box(
            rx.text(
                rx.cond(c.is_active, "Активный сбор", "Сбор завершён"),
                size="1",
                weight="medium",
                color=BRAND_ACTION_TEXT,
            ),
            background=BRAND_PURPLE_TINT,
            border_radius="999px",
            padding="0.2rem 0.7rem",
            width="fit-content",
            margin_bottom="1rem",
        ),
        rx.text(c.target_fmt, size="8", weight="bold", color=TEXT_PRIMARY),
        rx.text(
            rx.cond(c.amount_mode == "per_apartment", "с квартиры", "общая цель")
            + rx.cond(c.end_date_fmt != "", " · до " + c.end_date_fmt, ""),
            size="2",
            color="var(--gray-9)",
            margin_bottom="0.9rem",
        ),
        progress_bar(c.progress_pct),
        rx.hstack(
            rx.text(c.collected_fmt + " из " + c.target_fmt, size="2", weight="bold"),
            rx.text("собрано", size="2", color="var(--gray-9)"),
            spacing="1",
            margin_top="0.4rem",
            margin_bottom="1rem",
        ),
        rx.cond(c.description != "", rx.text(c.description, size="2", color="var(--gray-11)", margin_bottom="0.8rem")),
        rx.cond(
            c.instructions != "",
            rx.box(
                rx.text("Как передать деньги", size="2", weight="bold", margin_bottom="0.1rem"),
                rx.text(c.instructions, size="2", color="var(--gray-9)"),
                background="white",
                border="1px solid var(--gray-4)",
                border_radius="14px",
                padding="0.8rem 1rem",
                margin_bottom="1.2rem",
                width="100%",
            ),
        ),
        rx.cond(
            AuthState.is_uk,
            rx.button(
                rx.cond(c.is_active, "Остановить сбор", "Возобновить сбор"),
                width="100%",
                size="3",
                radius="full",
                variant="soft",
                on_click=FinanceState.toggle_collection_active(c.id),
            ),
        ),
        rx.cond(
            AuthState.is_resident,
            rx.vstack(
                rx.cond(
                    c.my_contribution > 0,
                    rx.text(
                        "Ваш взнос: " + c.my_contribution_fmt,
                        size="2",
                        color=BRAND_ACTION_TEXT,
                    ),
                ),
                rx.cond(
                    c.my_payment_pending,
                    rx.badge("Платёж обрабатывается...", color_scheme="amber"),
                    rx.cond(
                        c.remaining > 0,
                        rx.button(
                            rx.icon("credit-card", size=16),
                            "Внести " + c.remaining_fmt,
                            width="100%",
                            size="3",
                            radius="full",
                            style={"background": BRAND_PURPLE, "color": BRAND_ACTION_TEXT},
                            on_click=FinanceState.pay_collection(c.id, c.remaining),
                        ),
                        rx.badge("Сбор закрыт", color_scheme="green"),
                    ),
                ),
                width="100%",
                spacing="2",
            ),
        ),
        width="100%",
        align="start",
    )


def _collection_compact_card(c) -> rx.Component:
    subtitle = (
        c.target_fmt
        + " "
        + rx.cond(c.amount_mode == "per_apartment", "с квартиры", "общая цель")
        + rx.cond(c.end_date_fmt != "", " · до " + c.end_date_fmt, "")
    )
    return rx.box(
        rx.text(c.title, weight="bold", size="2"),
        rx.text(subtitle, size="1", color="var(--gray-9)", margin_top="0.15rem"),
        on_click=FinanceState.open_collection(c.id),
        cursor="pointer",
        background=CARD_BG,
        border_radius="14px",
        padding="0.7rem 0.8rem",
        width="100%",
    )


def _collection_form() -> rx.Component:
    return rx.vstack(
        error_text(FinanceState.col_error),
        field_label("Название"),
        rx.input(
            value=FinanceState.new_col_title,
            on_change=FinanceState.set_new_col_title,
            placeholder="Покраска лифта",
            width="100%",
        ),
        rx.text_area(
            placeholder="Описание (необязательно)",
            value=FinanceState.new_col_description,
            on_change=FinanceState.set_new_col_description,
            width="100%",
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
            margin_top="0.4rem",
            on_click=FinanceState.create_collection,
        ),
        width="100%",
        spacing="2",
        align="start",
    )


def _collection_detail_dialog() -> rx.Component:
    """C01/C02/C05 из макета — модалка с шапкой «X Закрыть», как у
    остальных вторичных экранов (A03, H02...)."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Сбор", style={"display": "none"}),
            rx.cond(
                FinanceState.open_collection_item,
                rx.vstack(
                    rx.hstack(
                        rx.icon("x", size=16, color="var(--gray-11)"),
                        rx.text("Закрыть", size="2", weight="medium"),
                        spacing="1",
                        align="center",
                        cursor="pointer",
                        on_click=FinanceState.close_collection,
                        width="fit-content",
                        margin_bottom="1rem",
                    ),
                    _published_collection_card(FinanceState.open_collection_item),
                    width="100%",
                    align="start",
                ),
            ),
            max_width=MAX_WIDTH,
            min_height="480px",
        ),
        open=FinanceState.open_collection_id != 0,
        on_open_change=FinanceState.set_collection_dialog_open,
    )


def _proposed_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Предложенные сборы"),
            rx.foreach(FinanceState.home_proposed_collections, _proposed_collection_card),
            rx.button(
                "Закрыть",
                variant="soft",
                width="100%",
                margin_top="0.2rem",
                on_click=FinanceState.close_proposed_dialog,
            ),
            max_width="360px",
        ),
        open=FinanceState.show_proposed_dialog,
        on_open_change=FinanceState.set_proposed_dialog_open,
    )


def _collections_section() -> rx.Component:
    items = rx.cond(AuthState.is_uk, FinanceState.home_published_collections, FinanceState.my_collections)
    return rx.vstack(
        rx.hstack(
            rx.hstack(
                rx.heading("Сборы", size="4"),
                rx.icon("chevron-right", size=16, color="var(--gray-9)"),
                spacing="1",
                align="center",
                cursor="pointer",
                on_click=FinanceState.open_collections_list,
            ),
            rx.spacer(),
            rx.cond(
                AuthState.is_uk,
                rx.cond(
                    FinanceState.home_proposed_collections.length() > 0,
                    rx.button(
                        rx.badge(
                            FinanceState.home_proposed_collections.length().to_string(),
                            color_scheme="red",
                            variant="solid",
                            radius="full",
                        ),
                        "Предложенных",
                        size="1",
                        variant="ghost",
                        color_scheme="gray",
                        on_click=FinanceState.open_proposed_dialog,
                    ),
                ),
            ),
            width="100%",
            align="center",
        ),
        error_text(FinanceState.pay_error),
        rx.cond(
            items.length() == 0,
            rx.text("Сборов пока нет", size="2", color="var(--gray-9)"),
            rx.grid(
                rx.foreach(items, _collection_compact_card),
                columns="2",
                spacing="2",
                width="100%",
            ),
        ),
        _collection_detail_dialog(),
        rx.cond(AuthState.is_uk, _proposed_dialog()),
        width="100%",
        spacing="2",
    )


def _initiative_card(i) -> rx.Component:
    return section_card(
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
            rx.vstack(
                rx.text(
                    i.votes.to_string() + "/" + i.needed_count.to_string(),
                    size="2",
                    weight="bold",
                ),
                rx.cond(
                    AuthState.is_resident,
                    rx.button(
                        rx.cond(i.i_voted, "Я не за", "Я за!"),
                        size="1",
                        radius="full",
                        variant="solid",
                        color_scheme=rx.cond(i.i_voted, "gray", "lime"),
                        on_click=CommunityState.toggle_initiative_vote(i.id),
                    ),
                ),
                align="end",
                spacing="1",
            ),
            width="100%",
            align="start",
        ),
    )


def _initiative_form() -> rx.Component:
    return rx.vstack(
        error_text(CommunityState.initiative_error),
        rx.input(
            value=CommunityState.new_initiative_title,
            on_change=CommunityState.set_new_initiative_title,
            placeholder="Субботник",
            width="100%",
        ),
        rx.text_area(
            placeholder="Описание",
            value=CommunityState.new_initiative_description,
            on_change=CommunityState.set_new_initiative_description,
            width="100%",
            rows="2",
        ),
        rx.hstack(
            rx.input(
                placeholder="Нужно человек",
                value=CommunityState.new_initiative_needed,
                on_change=CommunityState.set_new_initiative_needed,
            ),
            rx.input(
                placeholder="Дата, напр. 3 октября · 10:00",
                value=CommunityState.new_initiative_event_date,
                on_change=CommunityState.set_new_initiative_event_date,
            ),
            width="100%",
        ),
        rx.button(
            "Создать инициативу",
            width="100%",
            margin_top="0.4rem",
            on_click=CommunityState.create_initiative,
        ),
        width="100%",
        spacing="2",
        align="start",
    )


def _initiative_detail_dialog() -> rx.Component:
    """I01: карточка инициативы — дата, «N из M участвуют», описание и
    кнопка «Я участвую» (Neon, как в макете)."""
    i = CommunityState.open_initiative_item
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Инициатива", style={"display": "none"}),
            rx.cond(
                i,
                rx.vstack(
                    rx.hstack(
                        rx.icon("x", size=16, color="var(--gray-11)"),
                        rx.text("Закрыть", size="2", weight="medium"),
                        spacing="1",
                        align="center",
                        cursor="pointer",
                        on_click=CommunityState.close_initiative,
                        width="fit-content",
                        margin_bottom="1rem",
                    ),
                    rx.heading(i.title, size="6", weight="bold", margin_bottom="0.1rem"),
                    rx.cond(
                        i.author_name != "",
                        rx.text("Идея " + i.author_name, size="2", color="var(--gray-9)", margin_bottom="0.6rem"),
                    ),
                    rx.cond(
                        i.event_date != "",
                        rx.box(
                            rx.text(i.event_date, size="1", weight="medium", color=BRAND_ACTION_TEXT),
                            background=BRAND_PURPLE_TINT,
                            border_radius="999px",
                            padding="0.2rem 0.7rem",
                            width="fit-content",
                            margin_bottom="1rem",
                        ),
                    ),
                    rx.box(
                        rx.text(i.votes.to_string() + " из " + i.needed_count.to_string(), size="7", weight="bold"),
                        rx.text("соседей участвуют", size="2", color="var(--gray-9)", margin_bottom="0.6rem"),
                        progress_bar(i.progress_pct),
                        width="100%",
                        background="white",
                        border="1px solid var(--gray-4)",
                        border_radius="16px",
                        padding="1rem",
                        margin_bottom="1rem",
                    ),
                    rx.cond(i.description != "", rx.text(i.description, size="2", color="var(--gray-11)", margin_bottom="1.2rem")),
                    rx.cond(
                        AuthState.is_resident,
                        rx.button(
                            rx.cond(i.i_voted, "Я не участвую", "Я участвую"),
                            width="100%",
                            size="3",
                            radius="full",
                            style={"background": BRAND_NEON, "color": BRAND_ACTION_TEXT},
                            on_click=CommunityState.toggle_initiative_vote(i.id),
                        ),
                    ),
                    width="100%",
                    align="start",
                ),
            ),
            max_width=MAX_WIDTH,
            min_height="480px",
        ),
        open=CommunityState.open_initiative_id != 0,
        on_open_change=CommunityState.set_initiative_dialog_open,
    )


def _proposed_initiative_card(i) -> rx.Component:
    return section_card(
        rx.hstack(
            rx.badge("Предложено", color_scheme="amber"),
            rx.cond(i.proposed_by_name != "", rx.text(i.proposed_by_name, size="1", color="var(--gray-9)")),
            spacing="2",
            align="center",
        ),
        rx.text(i.title, weight="bold", size="3", margin_top="0.3rem"),
        rx.cond(i.description != "", rx.text(i.description, size="2", color="var(--gray-11)")),
        rx.hstack(
            rx.button(
                "Отклонить",
                variant="soft",
                color_scheme="red",
                size="1",
                flex="1",
                on_click=ProposalsState.open_reject("initiative", i.id, i.title),
            ),
            rx.button("Опубликовать", size="1", flex="1", on_click=CommunityState.publish_initiative(i.id)),
            width="100%",
            margin_top="0.5rem",
        ),
    )


def _proposed_initiatives_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Предложенные инициативы"),
            rx.foreach(CommunityState.proposed_initiatives, _proposed_initiative_card),
            rx.button(
                "Закрыть",
                variant="soft",
                width="100%",
                margin_top="0.2rem",
                on_click=CommunityState.close_proposed_initiatives_dialog,
            ),
            max_width="380px",
        ),
        open=CommunityState.show_proposed_initiatives_dialog,
        on_open_change=CommunityState.set_proposed_initiatives_dialog_open,
    )


def _initiatives_block() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.hstack(
                rx.heading("Инициативы", size="4"),
                rx.icon("chevron-right", size=16, color="var(--gray-9)"),
                spacing="1",
                align="center",
                cursor="pointer",
                on_click=CommunityState.open_initiatives_list,
            ),
            rx.spacer(),
            rx.cond(
                AuthState.is_uk,
                rx.cond(
                    CommunityState.proposed_initiatives.length() > 0,
                    rx.button(
                        rx.badge(
                            CommunityState.proposed_initiatives.length().to_string(),
                            color_scheme="red",
                            variant="solid",
                            radius="full",
                        ),
                        "Предложенных",
                        size="1",
                        variant="ghost",
                        color_scheme="gray",
                        on_click=CommunityState.open_proposed_initiatives_dialog,
                    ),
                ),
            ),
            width="100%",
            align="center",
        ),
        rx.cond(
            CommunityState.initiatives.length() == 0,
            rx.text("Инициатив пока нет", size="2", color="var(--gray-9)"),
            rx.foreach(CommunityState.initiatives, _initiative_card),
        ),
        _proposed_initiatives_dialog(),
        width="100%",
        spacing="2",
    )


def _poll_card(p) -> rx.Component:
    """Компактная карточка на «Дом» — голосование теперь по вариантам,
    поэтому карточка только открывает детальную I01-подобную Q01."""
    return section_card(
        rx.hstack(
            rx.vstack(
                rx.text(p.title, weight="bold", size="2"),
                rx.text(p.total_voters.to_string() + " голосов", size="1", color="var(--gray-9)"),
                align="start",
                spacing="0",
            ),
            rx.spacer(),
            rx.icon("chevron-right", size=16, color="var(--gray-9)"),
            width="100%",
            align="center",
        ),
        cursor="pointer",
        on_click=CommunityState.open_poll(p.id),
    )


def _poll_form() -> rx.Component:
    return rx.vstack(
        error_text(CommunityState.poll_error),
        rx.input(
            value=CommunityState.new_poll_title,
            on_change=CommunityState.set_new_poll_title,
            placeholder="Камера на домофон",
            width="100%",
        ),
        rx.text_area(
            placeholder="Описание",
            value=CommunityState.new_poll_description,
            on_change=CommunityState.set_new_poll_description,
            width="100%",
            rows="2",
        ),
        field_label("Варианты ответа"),
        rx.input(
            value=CommunityState.new_poll_option_1,
            on_change=CommunityState.set_new_poll_option_1,
            placeholder="Да, установить",
            width="100%",
        ),
        rx.input(
            value=CommunityState.new_poll_option_2,
            on_change=CommunityState.set_new_poll_option_2,
            placeholder="Нет, не нужно",
            width="100%",
        ),
        rx.input(
            value=CommunityState.new_poll_option_3,
            on_change=CommunityState.set_new_poll_option_3,
            placeholder="Ещё вариант (необязательно)",
            width="100%",
        ),
        rx.input(
            value=CommunityState.new_poll_option_4,
            on_change=CommunityState.set_new_poll_option_4,
            placeholder="Ещё вариант (необязательно)",
            width="100%",
        ),
        rx.hstack(
            rx.checkbox(
                checked=CommunityState.new_poll_allow_multiple,
                on_change=CommunityState.set_new_poll_allow_multiple,
            ),
            rx.text("Можно выбрать несколько вариантов", size="2"),
            align="center",
            spacing="2",
        ),
        rx.input(
            placeholder="До (дд.мм.гггг)",
            value=CommunityState.new_poll_end_date,
            on_change=CommunityState.set_new_poll_end_date,
            width="100%",
        ),
        rx.button(
            "Создать опрос",
            width="100%",
            margin_top="0.4rem",
            on_click=CommunityState.create_poll,
        ),
        width="100%",
        spacing="2",
        align="start",
    )


def _poll_option_row(o) -> rx.Component:
    """Q01/Q02: строка-вариант в режиме выбора — вся строка кликабельна,
    слева радио/чекбокс (зависит от allow_multiple), выбранный — заливка."""
    selected = CommunityState.poll_selected_option_ids.contains(o.id)
    return rx.hstack(
        rx.box(
            rx.cond(selected, rx.icon("check", size=13, color="white")),
            width="20px",
            height="20px",
            border_radius=rx.cond(CommunityState.open_poll_item.allow_multiple, "6px", "999px"),
            background=rx.cond(selected, BRAND_PURPLE, "transparent"),
            border=rx.cond(selected, "none", "1.5px solid var(--gray-7)"),
            display="flex",
            align_items="center",
            justify_content="center",
            flex_shrink="0",
        ),
        rx.text(o.label, size="3", weight="medium"),
        spacing="3",
        align="center",
        width="100%",
        background=rx.cond(selected, BRAND_PURPLE_TINT, "white"),
        border=rx.cond(selected, f"1.5px solid {BRAND_PURPLE}", "1px solid var(--gray-4)"),
        border_radius="14px",
        padding="0.9rem 1rem",
        cursor="pointer",
        on_click=CommunityState.toggle_poll_option_selection(o.id),
    )


def _poll_result_row(o) -> rx.Component:
    """Q03/Q05: строка-результат — подпись «· ваш голос», процент и число."""
    return rx.box(
        rx.hstack(
            rx.text(
                rx.cond(o.is_mine, o.label + " · ваш голос", o.label),
                size="3",
                weight="medium",
            ),
            width="100%",
        ),
        rx.text(o.pct.to_string() + "% · " + o.votes.to_string(), size="2", color="var(--gray-9)", margin_top="0.1rem"),
        progress_bar(o.pct),
        width="100%",
        background=rx.cond(o.is_mine, BRAND_PURPLE_TINT, "white"),
        border=rx.cond(o.is_mine, f"1.5px solid {BRAND_PURPLE}", "1px solid var(--gray-4)"),
        border_radius="14px",
        padding="0.9rem 1rem",
        margin_bottom="0.6rem",
    )


def _poll_detail_dialog() -> rx.Component:
    """Q01–Q05: карточка опроса — варианты (до голоса) либо результаты
    (после голоса/для завершённых), с переключением через «Изменить голос»."""
    p = CommunityState.open_poll_item
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Опрос", style={"display": "none"}),
            rx.cond(
                p,
                rx.vstack(
                    rx.hstack(
                        rx.icon("x", size=16, color="var(--gray-11)"),
                        rx.text("Закрыть", size="2", weight="medium"),
                        spacing="1",
                        align="center",
                        cursor="pointer",
                        on_click=CommunityState.close_poll,
                        width="fit-content",
                        margin_bottom="1rem",
                    ),
                    rx.heading(p.title, size="6", weight="bold", margin_bottom="0.1rem"),
                    rx.text(
                        rx.cond(p.end_date_fmt != "", "Опрос · до " + p.end_date_fmt, "Опрос"),
                        size="2",
                        color="var(--gray-9)",
                        margin_bottom="0.8rem",
                    ),
                    rx.cond(
                        p.description != "",
                        rx.text(p.description, size="2", color="var(--gray-11)", margin_bottom="1rem"),
                    ),
                    rx.cond(
                        CommunityState.poll_editing,
                        rx.vstack(
                            rx.cond(
                                p.allow_multiple,
                                rx.text("Можно выбрать несколько вариантов.", size="1", color="var(--gray-9)", margin_bottom="0.2rem"),
                            ),
                            rx.foreach(p.options, _poll_option_row),
                            width="100%",
                            spacing="2",
                        ),
                        rx.vstack(
                            rx.foreach(p.options, _poll_result_row),
                            width="100%",
                            spacing="0",
                        ),
                    ),
                    rx.cond(
                        CommunityState.poll_editing,
                        rx.text(
                            p.total_voters.to_string() + " голосов · результаты после ответа",
                            size="2",
                            color="var(--gray-9)",
                            margin_top="0.4rem",
                            margin_bottom="1rem",
                        ),
                        rx.text(
                            p.total_voters.to_string() + " человек проголосовали",
                            size="2",
                            color="var(--gray-9)",
                            margin_top="0.2rem",
                            margin_bottom="1rem",
                        ),
                    ),
                    rx.cond(
                        AuthState.is_resident,
                        rx.cond(
                            p.is_active,
                            rx.cond(
                                CommunityState.poll_editing,
                                rx.button(
                                    "Голосовать",
                                    width="100%",
                                    size="3",
                                    radius="full",
                                    disabled=CommunityState.poll_selected_option_ids.length() == 0,
                                    style=rx.cond(
                                        CommunityState.poll_selected_option_ids.length() == 0,
                                        {"background": "var(--gray-4)", "color": "var(--gray-9)"},
                                        {"background": BRAND_PURPLE, "color": BRAND_ACTION_TEXT},
                                    ),
                                    on_click=CommunityState.submit_poll_vote,
                                ),
                                rx.button(
                                    "Изменить голос",
                                    width="100%",
                                    size="3",
                                    radius="full",
                                    style={"background": BRAND_PURPLE_TINT, "color": BRAND_ACTION_TEXT},
                                    on_click=CommunityState.start_change_vote,
                                ),
                            ),
                            rx.button(
                                "Опрос завершён",
                                width="100%",
                                size="3",
                                radius="full",
                                disabled=True,
                                style={"background": "var(--gray-4)", "color": "var(--gray-9)"},
                            ),
                        ),
                    ),
                    width="100%",
                    align="start",
                ),
            ),
            max_width=MAX_WIDTH,
            min_height="480px",
        ),
        open=CommunityState.open_poll_id != 0,
        on_open_change=CommunityState.set_poll_dialog_open,
    )


def _proposed_poll_card(p) -> rx.Component:
    return section_card(
        rx.hstack(
            rx.badge("Предложено", color_scheme="amber"),
            rx.cond(p.proposed_by_name != "", rx.text(p.proposed_by_name, size="1", color="var(--gray-9)")),
            spacing="2",
            align="center",
        ),
        rx.text(p.title, weight="bold", size="3", margin_top="0.3rem"),
        rx.cond(p.description != "", rx.text(p.description, size="2", color="var(--gray-11)")),
        rx.vstack(
            rx.foreach(p.options, lambda o: rx.text("· " + o.label, size="2", color="var(--gray-9)")),
            spacing="0",
            margin_top="0.3rem",
            align="start",
        ),
        rx.hstack(
            rx.button(
                "Отклонить",
                variant="soft",
                color_scheme="red",
                size="1",
                flex="1",
                on_click=ProposalsState.open_reject("poll", p.id, p.title),
            ),
            rx.button("Опубликовать", size="1", flex="1", on_click=CommunityState.publish_poll(p.id)),
            width="100%",
            margin_top="0.5rem",
        ),
    )


def _proposed_polls_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Предложенные опросы"),
            rx.foreach(CommunityState.proposed_polls, _proposed_poll_card),
            rx.button(
                "Закрыть",
                variant="soft",
                width="100%",
                margin_top="0.2rem",
                on_click=CommunityState.close_proposed_polls_dialog,
            ),
            max_width="380px",
        ),
        open=CommunityState.show_proposed_polls_dialog,
        on_open_change=CommunityState.set_proposed_polls_dialog_open,
    )


def _polls_block() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.hstack(
                rx.heading("Опросы", size="4"),
                rx.icon("chevron-right", size=16, color="var(--gray-9)"),
                spacing="1",
                align="center",
                cursor="pointer",
                on_click=CommunityState.open_polls_list,
            ),
            rx.spacer(),
            rx.cond(
                AuthState.is_uk,
                rx.cond(
                    CommunityState.proposed_polls.length() > 0,
                    rx.button(
                        rx.badge(
                            CommunityState.proposed_polls.length().to_string(),
                            color_scheme="red",
                            variant="solid",
                            radius="full",
                        ),
                        "Предложенных",
                        size="1",
                        variant="ghost",
                        color_scheme="gray",
                        on_click=CommunityState.open_proposed_polls_dialog,
                    ),
                ),
            ),
            width="100%",
            align="center",
        ),
        rx.cond(
            CommunityState.polls.length() == 0,
            rx.text("Опросов пока нет", size="2", color="var(--gray-9)"),
            rx.foreach(CommunityState.polls, _poll_card),
        ),
        _proposed_polls_dialog(),
        width="100%",
        spacing="2",
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


def _debt_form() -> rx.Component:
    return rx.vstack(
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
        ),
        rx.button(
            "Добавить начисление",
            width="100%",
            margin_top="0.4rem",
            on_click=FinanceState.add_debt,
        ),
        width="100%",
        spacing="2",
        align="start",
    )


def _debts_block() -> rx.Component:
    return rx.vstack(
        rx.heading("Долги", size="4", margin_bottom="0.2rem"),
        rx.cond(
            AuthState.is_uk,
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


def _create_dialog_content() -> rx.Component:
    return rx.dialog.content(
        rx.dialog.title("Создать"),
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("Объявление", value="news"),
                rx.tabs.trigger("Сбор", value="col"),
                rx.tabs.trigger("Начисление", value="debt"),
                rx.tabs.trigger("Инициатива", value="init"),
                rx.tabs.trigger("Опрос", value="poll"),
                style={"overflow_x": "auto", "flex_wrap": "nowrap"},
            ),
            rx.tabs.content(_announcement_form(), value="news", padding_top="0.8rem"),
            rx.tabs.content(_collection_form(), value="col", padding_top="0.8rem"),
            rx.tabs.content(_debt_form(), value="debt", padding_top="0.8rem"),
            rx.tabs.content(_initiative_form(), value="init", padding_top="0.8rem"),
            rx.tabs.content(_poll_form(), value="poll", padding_top="0.8rem"),
            default_value="news",
            width="100%",
        ),
        max_width="380px",
    )


def _create_section() -> rx.Component:
    return rx.hstack(
        rx.heading("Создать", size="4"),
        rx.spacer(),
        rx.dialog.root(
            rx.dialog.trigger(
                rx.box(
                    rx.icon("plus", size=18, color="var(--accent-9)"),
                    width="44px",
                    height="44px",
                    border_radius="999px",
                    background="var(--gray-4)",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    cursor="pointer",
                ),
            ),
            _create_dialog_content(),
        ),
        width="100%",
        align="center",
    )


def _create_section_pill() -> rx.Component:
    """H03: полный pill «+ Создать» под пустыми разделами, вместо кружка."""
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.box(
                rx.text("+ Создать", weight="bold", text_align="center", color=BRAND_ACTION_TEXT),
                width="100%",
                background=BRAND_PURPLE_TINT,
                border_radius="999px",
                padding="0.9rem",
                cursor="pointer",
            ),
        ),
        _create_dialog_content(),
        width="100%",
    )


def _create_section_resident() -> rx.Component:
    """F01: у жителя «+Создать» открывает мастер предложения с
    модерацией, а не мгновенное создание, как у УК."""
    return rx.hstack(
        rx.heading("Создать", size="4"),
        rx.spacer(),
        rx.box(
            rx.icon("plus", size=18, color="var(--accent-9)"),
            width="44px",
            height="44px",
            border_radius="999px",
            background="var(--gray-4)",
            display="flex",
            align_items="center",
            justify_content="center",
            cursor="pointer",
            on_click=AuthState.open_create_flow,
        ),
        width="100%",
        align="center",
    )


def _create_section_pill_resident() -> rx.Component:
    return rx.box(
        rx.text("+ Создать", weight="bold", text_align="center", color=BRAND_ACTION_TEXT),
        width="100%",
        background=BRAND_PURPLE_TINT,
        border_radius="999px",
        padding="0.9rem",
        cursor="pointer",
        on_click=AuthState.open_create_flow,
    )


def _empty_home_hero() -> rx.Component:
    """H03: полностью пустой дом — крупная плашка вместо ленты объявлений."""
    return rx.vstack(
        rx.icon("house", size=40, color=BRAND_PURPLE),
        rx.heading("Ваш дом здесь", size="5", weight="bold", margin_top="0.4rem"),
        rx.text(
            "Начните с идеи или найдите нужный контакт.",
            size="2",
            color="var(--gray-9)",
            text_align="center",
        ),
        align="center",
        spacing="1",
        width="100%",
        background=BRAND_PURPLE_TINT,
        border_radius="20px",
        padding="2.2rem 1rem",
    )


def _empty_section_row(title: str, subtitle: str) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text(title, size="3", weight="bold"),
            rx.text(subtitle, size="2", color="var(--gray-9)"),
            spacing="0",
            align="start",
        ),
        rx.spacer(),
        rx.icon("chevron-right", size=18, color="var(--gray-9)"),
        width="100%",
        align="center",
        background="white",
        border_radius="16px",
        padding="0.9rem 1rem",
    )


def _segmented_tabs(value: rx.Var, on_active, on_completed) -> rx.Component:
    """Переключатель «Активные / Завершённые» (L01–L04) — не rx.tabs, а
    пара плашек: выбранная — светло-фиолетовая, остальная — просто текст."""

    def _segment(label: str, tab_value: str, on_click) -> rx.Component:
        selected = value == tab_value
        return rx.box(
            rx.text(label, size="2", weight="medium", color=rx.cond(selected, BRAND_ACTION_TEXT, "var(--gray-9)")),
            on_click=on_click,
            cursor="pointer",
            padding="0.5rem 1rem",
            border_radius="999px",
            background=rx.cond(selected, BRAND_PURPLE_TINT, "transparent"),
        )

    return rx.hstack(
        _segment("Активные", "active", on_active),
        _segment("Завершённые", "completed", on_completed),
        spacing="1",
    )


def _list_row(title, subtitle, completed=False, on_click=None) -> rx.Component:
    """Строка в списках L01–L04 — карточка с заголовком/подзаголовком,
    у завершённых пунктов бейдж «Завершён» вместо шеврона."""
    return rx.hstack(
        rx.vstack(
            rx.text(title, size="3", weight="bold"),
            rx.text(subtitle, size="2", color="var(--gray-9)"),
            rx.cond(
                completed,
                rx.box(
                    rx.text("Завершён", size="1", weight="medium", color=BRAND_ACTION_TEXT),
                    background=BRAND_PURPLE_TINT,
                    border_radius="999px",
                    padding="0.15rem 0.6rem",
                    margin_top="0.3rem",
                    width="fit-content",
                ),
            ),
            spacing="0",
            align="start",
        ),
        rx.spacer(),
        rx.cond(completed, rx.fragment(), rx.icon("chevron-right", size=18, color="var(--gray-9)")),
        width="100%",
        align="center",
        background="white",
        border_radius="16px",
        padding="0.9rem 1rem",
        cursor=rx.cond(completed, "default", "pointer"),
        on_click=on_click or rx.console_log(""),
    )


def _collections_list_dialog() -> rx.Component:
    view = FinanceState.collections_list_view
    active_items = rx.cond(AuthState.is_uk, FinanceState.home_active_collections, FinanceState.my_active_collections)
    archived_items = rx.cond(
        AuthState.is_uk, FinanceState.home_archived_collections, FinanceState.my_archived_collections
    )

    def _row(c, completed: bool):
        subtitle = (
            c.target_fmt
            + " "
            + rx.cond(c.amount_mode == "per_apartment", "с квартиры", "общая цель")
            + rx.cond(c.end_date_fmt != "", " · до " + c.end_date_fmt, "")
        )
        return _list_row(c.title, subtitle, completed=completed, on_click=FinanceState.open_collection(c.id))

    return rx.cond(
        view != "",
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title("Сборы", style={"display": "none"}),
                rx.vstack(
                    rx.hstack(
                        rx.icon("x", size=16, color="var(--gray-11)"),
                        rx.text("Закрыть", size="2", weight="medium"),
                        spacing="1",
                        align="center",
                        cursor="pointer",
                        on_click=FinanceState.close_collections_list,
                        width="fit-content",
                        margin_bottom="1rem",
                    ),
                    rx.heading("Сборы", size="6", weight="bold", margin_bottom="0.9rem"),
                    _segmented_tabs(
                        view,
                        FinanceState.set_collections_list_tab("active"),
                        FinanceState.set_collections_list_tab("completed"),
                    ),
                    rx.box(height="0.9rem"),
                    rx.vstack(
                        rx.cond(
                            view == "active",
                            rx.cond(
                                active_items.length() == 0,
                                rx.text("Активных сборов нет", size="2", color="var(--gray-9)"),
                                rx.foreach(active_items, lambda c: _row(c, False)),
                            ),
                            rx.cond(
                                archived_items.length() == 0,
                                rx.text("Завершённых сборов нет", size="2", color="var(--gray-9)"),
                                rx.foreach(archived_items, lambda c: _row(c, True)),
                            ),
                        ),
                        width="100%",
                        spacing="2",
                        margin_bottom="1rem",
                    ),
                    _create_section_pill(),
                    width="100%",
                    align="start",
                ),
                max_width=MAX_WIDTH,
                min_height="520px",
            ),
            open=view != "",
            on_open_change=FinanceState.set_collections_list_open,
        ),
    )


def _initiatives_list_dialog() -> rx.Component:
    view = CommunityState.initiatives_list_view

    def _row(i, completed: bool):
        return _list_row(
            i.title,
            i.votes.to_string() + " из " + i.needed_count.to_string() + " участников",
            completed=completed,
            on_click=CommunityState.open_initiative(i.id),
        )

    return rx.cond(
        view != "",
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title("Инициативы", style={"display": "none"}),
                rx.vstack(
                    rx.hstack(
                        rx.icon("x", size=16, color="var(--gray-11)"),
                        rx.text("Закрыть", size="2", weight="medium"),
                        spacing="1",
                        align="center",
                        cursor="pointer",
                        on_click=CommunityState.close_initiatives_list,
                        width="fit-content",
                        margin_bottom="1rem",
                    ),
                    rx.heading("Инициативы", size="6", weight="bold", margin_bottom="0.9rem"),
                    _segmented_tabs(
                        view,
                        CommunityState.set_initiatives_list_tab("active"),
                        CommunityState.set_initiatives_list_tab("completed"),
                    ),
                    rx.box(height="0.9rem"),
                    rx.vstack(
                        rx.cond(
                            view == "active",
                            rx.cond(
                                CommunityState.initiatives.length() == 0,
                                rx.text("Активных инициатив нет", size="2", color="var(--gray-9)"),
                                rx.foreach(CommunityState.initiatives, lambda i: _row(i, False)),
                            ),
                            rx.cond(
                                CommunityState.completed_initiatives.length() == 0,
                                rx.text("Завершённых инициатив нет", size="2", color="var(--gray-9)"),
                                rx.foreach(CommunityState.completed_initiatives, lambda i: _row(i, True)),
                            ),
                        ),
                        width="100%",
                        spacing="2",
                        margin_bottom="1rem",
                    ),
                    _create_section_pill(),
                    width="100%",
                    align="start",
                ),
                max_width=MAX_WIDTH,
                min_height="520px",
            ),
            open=view != "",
            on_open_change=CommunityState.set_initiatives_list_open,
        ),
    )


def _polls_list_dialog() -> rx.Component:
    view = CommunityState.polls_list_view

    def _row(p, completed: bool):
        return _list_row(
            p.title,
            p.total_voters.to_string() + " голосов",
            completed=completed,
            on_click=CommunityState.open_poll(p.id),
        )

    return rx.cond(
        view != "",
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title("Опросы", style={"display": "none"}),
                rx.vstack(
                    rx.hstack(
                        rx.icon("x", size=16, color="var(--gray-11)"),
                        rx.text("Закрыть", size="2", weight="medium"),
                        spacing="1",
                        align="center",
                        cursor="pointer",
                        on_click=CommunityState.close_polls_list,
                        width="fit-content",
                        margin_bottom="1rem",
                    ),
                    rx.heading("Опросы", size="6", weight="bold", margin_bottom="0.9rem"),
                    _segmented_tabs(
                        view,
                        CommunityState.set_polls_list_tab("active"),
                        CommunityState.set_polls_list_tab("completed"),
                    ),
                    rx.box(height="0.9rem"),
                    rx.vstack(
                        rx.cond(
                            view == "active",
                            rx.cond(
                                CommunityState.polls.length() == 0,
                                rx.text("Активных опросов нет", size="2", color="var(--gray-9)"),
                                rx.foreach(CommunityState.polls, lambda p: _row(p, False)),
                            ),
                            rx.cond(
                                CommunityState.completed_polls.length() == 0,
                                rx.text("Завершённых опросов нет", size="2", color="var(--gray-9)"),
                                rx.foreach(CommunityState.completed_polls, lambda p: _row(p, True)),
                            ),
                        ),
                        width="100%",
                        spacing="2",
                        margin_bottom="1rem",
                    ),
                    _create_section_pill(),
                    width="100%",
                    align="start",
                ),
                max_width=MAX_WIDTH,
                min_height="520px",
            ),
            open=view != "",
            on_open_change=CommunityState.set_polls_list_open,
        ),
    )


def _invite_footer_buttons() -> rx.Component:
    return rx.vstack(
        rx.button(
            rx.cond(UKAdminState.invite_code_copied, "Скопировано", "Скопировать код"),
            width="100%",
            size="3",
            radius="full",
            style={"background": BRAND_PURPLE_TINT, "color": BRAND_ACTION_TEXT},
            on_click=UKAdminState.copy_invite_code,
        ),
        rx.button(
            "Поделиться",
            width="100%",
            size="3",
            radius="full",
            style={"background": BRAND_PURPLE, "color": BRAND_ACTION_TEXT},
            on_click=UKAdminState.share_invite,
        ),
        width="100%",
        spacing="2",
    )


def _invite_code_view(entrance) -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.vstack(
                rx.text(
                    "Код дома",
                    size="2",
                    color=BRAND_ACTION_TEXT,
                    text_align="center",
                ),
                rx.text(
                    entrance.invite_code_display,
                    size="8",
                    weight="bold",
                    color=BRAND_ACTION_TEXT,
                    text_align="center",
                ),
                spacing="1",
                align="center",
                width="100%",
            ),
            width="100%",
            background=BRAND_PURPLE_TINT,
            border_radius="20px",
            padding="1.4rem 1rem",
            margin_bottom="0.75rem",
        ),
        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.text("Показать QR", size="3", weight="bold"),
                    rx.text("Удобно распечатать у входа", size="2", color="var(--gray-9)"),
                    spacing="0",
                    align="start",
                ),
                rx.spacer(),
                rx.icon("chevron-right", size=18, color="var(--gray-9)"),
                width="100%",
                align="center",
            ),
            width="100%",
            background="white",
            border_radius="16px",
            padding="0.9rem 1rem",
            cursor="pointer",
            on_click=UKAdminState.show_invite_qr,
            margin_bottom="1.25rem",
        ),
        rx.text("По приглашению соседи укажут", size="2", color="var(--gray-9)"),
        rx.text("своё имя и квартиру.", size="2", color="var(--gray-9)", margin_bottom="1.5rem"),
        rx.spacer(),
        _invite_footer_buttons(),
        width="100%",
        align="start",
    )


def _invite_qr_view(entrance) -> rx.Component:
    return rx.vstack(
        rx.center(
            rx.image(
                src=entrance.qr_data_uri,
                width="220px",
                height="220px",
                border_radius="12px",
            ),
            width="100%",
            background="white",
            border_radius="20px",
            padding="1.5rem",
            margin_bottom="1.25rem",
        ),
        rx.text("По приглашению соседи укажут", size="2", color="var(--gray-9)"),
        rx.text("своё имя и квартиру.", size="2", color="var(--gray-9)", margin_bottom="1.5rem"),
        rx.spacer(),
        _invite_footer_buttons(),
        width="100%",
        align="start",
    )


def _invite_after_create_modal() -> rx.Component:
    """A03–A05: «Пригласить соседей», модалкой поверх пустого дома сразу
    после «Создать дом» (H03)."""
    entrance = UKAdminState.invite_entrance
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Пригласить соседей", style={"display": "none"}),
            rx.cond(
                entrance,
                rx.vstack(
                    rx.hstack(
                        rx.icon("x", size=16, color="var(--gray-11)"),
                        rx.text("Закрыть", size="2", weight="medium"),
                        spacing="1",
                        align="center",
                        cursor="pointer",
                        on_click=UKAdminState.close_invite_modal,
                        width="fit-content",
                        margin_bottom="1rem",
                    ),
                    rx.icon(
                        "chevron-left",
                        size=22,
                        color="var(--gray-11)",
                        cursor="pointer",
                        on_click=UKAdminState.back_or_close_invite,
                        margin_bottom="1rem",
                    ),
                    rx.heading("Пригласить соседей", size="6", weight="bold", margin_bottom="0.3rem"),
                    rx.text(
                        entrance.building_address + " · подъезд " + entrance.number.to_string(),
                        size="2",
                        color="var(--gray-9)",
                        margin_bottom="1.5rem",
                    ),
                    rx.cond(
                        UKAdminState.invite_modal_view == "qr",
                        _invite_qr_view(entrance),
                        _invite_code_view(entrance),
                    ),
                    width="100%",
                    align="start",
                ),
            ),
            max_width=MAX_WIDTH,
            min_height="520px",
            display="flex",
            flex_direction="column",
        ),
        open=UKAdminState.invite_modal_view != "",
        on_open_change=UKAdminState.set_invite_modal_open,
    )


# ======================================================== Мастер F01–F16 ===


def _create_type_row(icon: str, title: str, subtitle: str, kind: str) -> rx.Component:
    return rx.hstack(
        rx.icon(icon, size=20, color=BRAND_ACTION_TEXT),
        rx.vstack(
            rx.text(title, size="3", weight="bold"),
            rx.text(subtitle, size="2", color="var(--gray-9)"),
            spacing="0",
            align="start",
        ),
        rx.spacer(),
        rx.icon("chevron-right", size=18, color="var(--gray-9)"),
        width="100%",
        align="center",
        spacing="3",
        background="white",
        border_radius="16px",
        padding="0.9rem 1rem",
        cursor="pointer",
        on_click=AuthState.pick_create_flow_kind(kind),
    )


def _create_type_picker() -> rx.Component:
    """F01: «Что хотите предложить?» — открывается вместо мгновенного
    создания, когда предложение жителя идёт на модерацию УК."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Создать", style={"display": "none"}),
            rx.vstack(
                rx.hstack(
                    rx.heading("Что хотите предложить?", size="5", weight="bold"),
                    rx.spacer(),
                    rx.icon(
                        "x",
                        size=18,
                        color="var(--gray-9)",
                        cursor="pointer",
                        on_click=AuthState.close_create_flow,
                    ),
                    width="100%",
                    align="center",
                    margin_bottom="0.3rem",
                ),
                rx.text(
                    "Администратор проверит предложение перед публикацией.",
                    size="2",
                    color="var(--gray-9)",
                    margin_bottom="1rem",
                ),
                _create_type_row("wallet", "Сбор", "Собрать деньги на общее дело", "collection"),
                _create_type_row("users", "Инициативу", "Сделать что-то вместе", "initiative"),
                _create_type_row("bar-chart-2", "Опрос", "Узнать мнение соседей", "poll"),
                width="100%",
                spacing="2",
                align="start",
            ),
            max_width=MAX_WIDTH,
        ),
        open=AuthState.show_create_type_picker,
        on_open_change=AuthState.set_create_flow_dialog_open,
    )


def _wizard_header(heading: str) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon(
                "chevron-left",
                size=22,
                color="var(--gray-11)",
                cursor="pointer",
                on_click=AuthState.create_flow_prev_step,
            ),
            rx.spacer(),
            rx.hstack(
                rx.icon("x", size=16, color="var(--gray-11)"),
                rx.text("Закрыть", size="2", weight="medium"),
                spacing="1",
                align="center",
                cursor="pointer",
                on_click=AuthState.close_create_flow,
            ),
            width="100%",
            align="center",
        ),
        rx.heading(heading, size="6", weight="bold", margin_top="0.8rem"),
        rx.text("Предложение для администратора", size="2", color="var(--gray-9)", margin_bottom="1rem"),
        width="100%",
        align="start",
        spacing="1",
    )


def _mode_toggle(value: rx.Var, a_key: str, a_label: str, b_key: str, b_label: str, on_change) -> rx.Component:
    def _btn(key: str, label: str) -> rx.Component:
        selected = value == key
        return rx.box(
            rx.text(label, size="2", weight="medium", color=rx.cond(selected, BRAND_ACTION_TEXT, "var(--gray-9)")),
            on_click=on_change(key),
            cursor="pointer",
            flex="1",
            text_align="center",
            padding="0.6rem",
            border_radius="999px",
            background=rx.cond(selected, BRAND_PURPLE_TINT, "var(--gray-3)"),
        )

    return rx.hstack(_btn(a_key, a_label), _btn(b_key, b_label), spacing="2", width="100%", margin_bottom="0.8rem")


def _wizard_next_button(label: str, enabled: rx.Var, on_click) -> rx.Component:
    return rx.button(
        label,
        width="100%",
        size="3",
        radius="full",
        disabled=enabled == False,  # noqa: E712
        style=rx.cond(
            enabled,
            {"background": BRAND_PURPLE, "color": BRAND_ACTION_TEXT},
            {"background": "var(--gray-4)", "color": "var(--gray-9)"},
        ),
        on_click=on_click,
    )


def _collection_step1() -> rx.Component:
    """F02."""
    return rx.vstack(
        _wizard_header("Новый сбор"),
        field_label("Название"),
        rx.input(
            value=FinanceState.propose_col_title,
            on_change=FinanceState.set_propose_col_title,
            placeholder="Покраска лифта",
            width="100%",
            margin_bottom="0.9rem",
            auto_focus=True,
        ),
        field_label("Как считаем сумму"),
        _mode_toggle(
            FinanceState.propose_col_mode,
            "per_apartment", "С квартиры",
            "total", "Общая цель",
            FinanceState.set_propose_col_mode,
        ),
        field_label(rx.cond(FinanceState.propose_col_mode == "per_apartment", "Сумма, ₽", "Общая цель, ₽")),
        rx.input(
            value=FinanceState.propose_col_amount,
            on_change=FinanceState.set_propose_col_amount,
            placeholder="1000",
            width="100%",
            margin_bottom="0.9rem",
        ),
        field_label("Срок сбора"),
        rx.input(
            value=FinanceState.propose_col_end_date,
            on_change=FinanceState.set_propose_col_end_date,
            placeholder="дд.мм.гггг",
            width="100%",
            margin_bottom="1.2rem",
        ),
        rx.spacer(),
        _wizard_next_button("Далее", FinanceState.propose_col_step1_valid, AuthState.create_flow_next_step),
        width="100%",
        min_height="480px",
        align="start",
    )


def _collection_step2() -> rx.Component:
    """F03."""
    return rx.vstack(
        _wizard_header("Новый сбор"),
        error_text(FinanceState.propose_error),
        field_label("Описание"),
        rx.text_area(
            value=FinanceState.propose_col_description,
            on_change=FinanceState.set_propose_col_description,
            placeholder="Обновим стены и двери лифта. Материалы и работу посчитали.",
            width="100%",
            rows="4",
            margin_bottom="0.9rem",
        ),
        field_label("Инструкция · необязательно"),
        rx.text_area(
            value=FinanceState.propose_col_instructions,
            on_change=FinanceState.set_propose_col_instructions,
            placeholder="Свяжитесь с Татьяной, квартира 12",
            width="100%",
            rows="2",
            margin_bottom="0.9rem",
        ),
        rx.text("Сумма не списывается в приложении.", size="2", color="var(--gray-9)"),
        rx.spacer(),
        rx.button(
            "Отправить администратору",
            width="100%",
            size="3",
            radius="full",
            style={"background": BRAND_NEON, "color": BRAND_ACTION_TEXT},
            on_click=FinanceState.propose_collection,
        ),
        rx.text(
            "Предложение увидит администратор дома.",
            size="1",
            color="var(--gray-9)",
            text_align="center",
            width="100%",
            margin_top="0.4rem",
        ),
        width="100%",
        min_height="480px",
        align="start",
    )


def _initiative_step1() -> rx.Component:
    """F05."""
    return rx.vstack(
        _wizard_header("Новая инициатива"),
        field_label("Название"),
        rx.input(
            value=CommunityState.propose_initiative_title,
            on_change=CommunityState.set_propose_initiative_title,
            placeholder="Субботник",
            width="100%",
            margin_bottom="0.9rem",
            auto_focus=True,
        ),
        field_label("Дата и время"),
        rx.input(
            value=CommunityState.propose_initiative_event_date,
            on_change=CommunityState.set_propose_initiative_event_date,
            placeholder="3 октября 2026 · 10:00",
            width="100%",
            margin_bottom="0.9rem",
        ),
        field_label("Сколько нужно участников"),
        rx.input(
            value=CommunityState.propose_initiative_needed,
            on_change=CommunityState.set_propose_initiative_needed,
            placeholder="5",
            width="100%",
            margin_bottom="1.2rem",
        ),
        rx.spacer(),
        _wizard_next_button(
            "Далее", CommunityState.propose_initiative_step1_valid, AuthState.create_flow_next_step
        ),
        width="100%",
        min_height="480px",
        align="start",
    )


def _initiative_step2() -> rx.Component:
    """F06."""
    return rx.vstack(
        _wizard_header("Новая инициатива"),
        error_text(CommunityState.propose_initiative_error),
        field_label("Описание"),
        rx.text_area(
            value=CommunityState.propose_initiative_description,
            on_change=CommunityState.set_propose_initiative_description,
            placeholder="Укажите место встречи, что взять с собой и сколько времени займёт.",
            width="100%",
            rows="5",
            margin_bottom="1.2rem",
        ),
        rx.spacer(),
        rx.button(
            "Отправить администратору",
            width="100%",
            size="3",
            radius="full",
            style={"background": BRAND_NEON, "color": BRAND_ACTION_TEXT},
            on_click=CommunityState.propose_initiative,
        ),
        rx.text(
            "Предложение увидит администратор дома.",
            size="1",
            color="var(--gray-9)",
            text_align="center",
            width="100%",
            margin_top="0.4rem",
        ),
        width="100%",
        min_height="480px",
        align="start",
    )


def _propose_poll_option_input(label, idx) -> rx.Component:
    return rx.hstack(
        rx.input(
            value=label,
            on_change=lambda v: CommunityState.set_propose_poll_option(idx, v),
            placeholder="Вариант",
            width="100%",
        ),
        rx.cond(
            CommunityState.propose_poll_options.length() > 2,
            rx.icon(
                "x",
                size=16,
                color="var(--gray-9)",
                cursor="pointer",
                on_click=CommunityState.remove_propose_poll_option(idx),
            ),
        ),
        align="center",
        spacing="2",
        width="100%",
        margin_bottom="0.6rem",
    )


def _poll_step1() -> rx.Component:
    """F07/F08 объединены — новые варианты появляются сразу на этом же
    шаге, без отдельного экрана «Варианты ответа»."""
    return rx.vstack(
        _wizard_header("Новый опрос"),
        field_label("Вопрос"),
        rx.input(
            value=CommunityState.propose_poll_title,
            on_change=CommunityState.set_propose_poll_title,
            placeholder="Нужна ли камера у входа?",
            width="100%",
            margin_bottom="0.9rem",
            auto_focus=True,
        ),
        field_label("Варианты ответа"),
        rx.foreach(CommunityState.propose_poll_options, _propose_poll_option_input),
        rx.cond(
            CommunityState.propose_poll_options.length() < 10,
            rx.box(
                rx.text("+ Добавить вариант", weight="bold", text_align="center", color=BRAND_ACTION_TEXT, size="2"),
                width="100%",
                background=BRAND_PURPLE_TINT,
                border_radius="999px",
                padding="0.6rem",
                cursor="pointer",
                on_click=CommunityState.add_propose_poll_option,
                margin_bottom="1.2rem",
            ),
        ),
        rx.spacer(),
        _wizard_next_button("Далее", CommunityState.propose_poll_step1_valid, AuthState.create_flow_next_step),
        width="100%",
        min_height="480px",
        align="start",
    )


def _poll_step2() -> rx.Component:
    """F09."""
    return rx.vstack(
        _wizard_header("Новый опрос"),
        error_text(CommunityState.propose_poll_error),
        field_label("Описание"),
        rx.text_area(
            value=CommunityState.propose_poll_description,
            on_change=CommunityState.set_propose_poll_description,
            placeholder="Ориентировочно 20 000 ₽ на весь подъезд.",
            width="100%",
            rows="3",
            margin_bottom="0.9rem",
        ),
        field_label("Опрос до"),
        rx.input(
            value=CommunityState.propose_poll_end_date,
            on_change=CommunityState.set_propose_poll_end_date,
            placeholder="дд.мм.гггг",
            width="100%",
            margin_bottom="0.9rem",
        ),
        rx.hstack(
            rx.text("Несколько ответов", size="2", weight="medium"),
            rx.spacer(),
            rx.switch(
                checked=CommunityState.propose_poll_allow_multiple,
                on_change=CommunityState.set_propose_poll_allow_multiple,
            ),
            width="100%",
            align="center",
            margin_bottom="0.7rem",
        ),
        rx.hstack(
            rx.text("Можно менять голос", size="2", weight="medium"),
            rx.spacer(),
            rx.switch(
                checked=CommunityState.propose_poll_allow_vote_change,
                on_change=CommunityState.set_propose_poll_allow_vote_change,
            ),
            width="100%",
            align="center",
            margin_bottom="1.2rem",
        ),
        rx.spacer(),
        rx.button(
            "Отправить администратору",
            width="100%",
            size="3",
            radius="full",
            style={"background": BRAND_NEON, "color": BRAND_ACTION_TEXT},
            on_click=CommunityState.propose_poll,
        ),
        rx.text(
            "Предложение увидит администратор дома.",
            size="1",
            color="var(--gray-9)",
            text_align="center",
            width="100%",
            margin_top="0.4rem",
        ),
        width="100%",
        min_height="480px",
        align="start",
    )


def _create_flow_success() -> rx.Component:
    """F13."""
    return rx.vstack(
        rx.hstack(
            rx.spacer(),
            rx.hstack(
                rx.icon("x", size=16, color="var(--gray-11)"),
                rx.text("Закрыть", size="2", weight="medium"),
                spacing="1",
                align="center",
                cursor="pointer",
                on_click=AuthState.close_create_flow,
            ),
            width="100%",
        ),
        rx.spacer(),
        rx.center(
            rx.box(
                rx.icon("check", size=32, color=BRAND_PURPLE),
                background=BRAND_PURPLE_TINT,
                border_radius="20px",
                padding="1.4rem",
            ),
            width="100%",
            padding_top="1.5rem",
            padding_bottom="1.5rem",
        ),
        rx.heading("Отправлено администратору", size="6", weight="bold", text_align="center", width="100%"),
        rx.text(
            "Когда предложение проверят, его статус появится в вашем меню.",
            size="2",
            color="var(--gray-9)",
            text_align="center",
            width="100%",
            margin_top="0.4rem",
        ),
        rx.spacer(),
        rx.button(
            "Мои предложения",
            width="100%",
            size="3",
            radius="full",
            style={"background": BRAND_PURPLE, "color": BRAND_ACTION_TEXT},
            on_click=[AuthState.close_create_flow, ProposalsState.open_my_proposals],
        ),
        width="100%",
        min_height="480px",
        align="start",
    )


def _create_flow_dialog() -> rx.Component:
    kind = AuthState.create_flow_kind
    step = AuthState.create_flow_step
    body = rx.cond(
        AuthState.create_flow_done,
        _create_flow_success(),
        rx.match(
            kind,
            ("collection", rx.cond(step == 1, _collection_step1(), _collection_step2())),
            ("initiative", rx.cond(step == 1, _initiative_step1(), _initiative_step2())),
            ("poll", rx.cond(step == 1, _poll_step1(), _poll_step2())),
            rx.fragment(),
        ),
    )
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Предложение", style={"display": "none"}),
            body,
            max_width=MAX_WIDTH,
            min_height="520px",
        ),
        open=kind != "",
        on_open_change=AuthState.set_create_flow_dialog_open,
    )


def _reject_reason_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Отклонить предложение"),
            rx.text(ProposalsState.reject_target_title, size="2", weight="bold", margin_bottom="0.6rem"),
            field_label("Причина"),
            rx.text_area(
                value=ProposalsState.reject_reason_input,
                on_change=ProposalsState.set_reject_reason_input,
                placeholder="Сначала согласуем смету с УК.",
                width="100%",
                rows="3",
                margin_bottom="0.8rem",
            ),
            rx.hstack(
                rx.button(
                    "Отмена",
                    variant="soft",
                    flex="1",
                    on_click=ProposalsState.close_reject,
                ),
                rx.button(
                    "Отклонить",
                    color_scheme="red",
                    flex="1",
                    on_click=ProposalsState.confirm_reject,
                ),
                width="100%",
            ),
            max_width="360px",
        ),
        open=ProposalsState.reject_target_kind != "",
        on_open_change=ProposalsState.set_reject_dialog_open,
    )


def _my_proposal_card(item) -> rx.Component:
    status_badge = rx.match(
        item.status,
        ("proposed", rx.box(
            rx.text("На проверке", size="1", weight="medium", color=BRAND_ACTION_TEXT),
            background=BRAND_PURPLE_TINT, border_radius="999px", padding="0.2rem 0.7rem", width="fit-content",
        )),
        ("rejected", rx.box(
            rx.text("Отклонено", size="1", weight="medium", color="var(--red-11)"),
            background="var(--red-3)", border_radius="999px", padding="0.2rem 0.7rem", width="fit-content",
        )),
        rx.box(
            rx.text("Опубликовано", size="1", weight="medium", color="var(--green-11)"),
            background="var(--green-3)", border_radius="999px", padding="0.2rem 0.7rem", width="fit-content",
        ),
    )
    action = rx.match(
        item.status,
        ("proposed", rx.button(
            "Отозвать предложение",
            width="100%",
            variant="soft",
            color_scheme="gray",
            margin_top="0.6rem",
            on_click=ProposalsState.withdraw_proposal(item.kind, item.id),
        )),
        ("rejected", rx.vstack(
            rx.text(item.rejection_reason, size="2", color="var(--gray-11)", margin_top="0.4rem"),
            rx.button(
                "Исправить и отправить",
                width="100%",
                style={"background": BRAND_PURPLE, "color": BRAND_ACTION_TEXT},
                margin_top="0.4rem",
                on_click=ProposalsState.start_edit_rejected(item.kind, item.id),
            ),
            width="100%",
            spacing="1",
            align="start",
        )),
        rx.fragment(),
    )
    return rx.box(
        rx.text(item.title, weight="bold", size="3"),
        rx.text(item.kind_label + " · отправлено " + item.submitted_fmt, size="2", color="var(--gray-9)", margin_bottom="0.4rem"),
        status_badge,
        action,
        width="100%",
        background="white",
        border="1px solid var(--gray-4)",
        border_radius="16px",
        padding="0.9rem 1rem",
        margin_bottom="0.7rem",
    )


def _my_proposals_dialog() -> rx.Component:
    """F14–F16: «Мои предложения»."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Мои предложения", style={"display": "none"}),
            rx.vstack(
                rx.hstack(
                    rx.icon("x", size=16, color="var(--gray-11)"),
                    rx.text("Закрыть", size="2", weight="medium"),
                    spacing="1",
                    align="center",
                    cursor="pointer",
                    on_click=ProposalsState.close_my_proposals,
                    width="fit-content",
                    margin_bottom="1rem",
                ),
                rx.heading("Мои предложения", size="6", weight="bold", margin_bottom="0.1rem"),
                rx.text("Сохраняем всё, что вы отправили", size="2", color="var(--gray-9)", margin_bottom="1rem"),
                rx.cond(
                    ProposalsState.my_proposals.length() == 0,
                    rx.text("Предложений пока нет", size="2", color="var(--gray-9)"),
                    rx.foreach(ProposalsState.my_proposals, _my_proposal_card),
                ),
                width="100%",
                align="start",
            ),
            max_width=MAX_WIDTH,
            min_height="480px",
        ),
        open=ProposalsState.show_my_proposals,
        on_open_change=ProposalsState.set_my_proposals_open,
    )


def home_tab() -> rx.Component:
    collections_count = rx.cond(
        AuthState.is_uk,
        FinanceState.home_published_collections.length(),
        FinanceState.my_collections.length(),
    )
    debts_count = rx.cond(
        AuthState.is_uk,
        FinanceState.home_active_debts.length() + FinanceState.home_paid_debts.length(),
        FinanceState.active_my_debts.length() + FinanceState.paid_my_debts.length(),
    )
    proposed_count = rx.cond(
        AuthState.is_uk,
        FinanceState.home_proposed_collections.length()
        + CommunityState.proposed_initiatives.length()
        + CommunityState.proposed_polls.length(),
        0,
    )
    # H03: пока в доме вообще ничего нет — крупная плашка-иллюстрация вместо
    # пяти отдельных «пока нет», как в заполненном состоянии (H01). Если
    # есть предложения на модерации, дом не считаем пустым — иначе у УК
    # негде увидеть бейдж «Предложенных» (он живёт в заполненном варианте).
    home_is_empty = (
        (NewsState.news_items.length() == 0)
        & (collections_count == 0)
        & (CommunityState.initiatives.length() == 0)
        & (CommunityState.polls.length() == 0)
        & (debts_count == 0)
        & (proposed_count == 0)
    )
    return rx.vstack(
        rx.cond(AuthState.is_uk, _invite_after_create_modal()),
        _collections_list_dialog(),
        _initiatives_list_dialog(),
        _initiative_detail_dialog(),
        _polls_list_dialog(),
        _poll_detail_dialog(),
        rx.cond(AuthState.is_resident, _create_type_picker()),
        rx.cond(AuthState.is_resident, _create_flow_dialog()),
        rx.cond(AuthState.is_resident, _my_proposals_dialog()),
        rx.cond(AuthState.is_uk, _reject_reason_dialog()),
        _identity_card(),
        _home_header(),
        rx.cond(
            AuthState.viewing_entrance_id != 0,
            rx.cond(
                home_is_empty,
                rx.vstack(
                    _empty_home_hero(),
                    _empty_section_row("Сборов пока нет", "Предложите то, что нужно дому"),
                    _empty_section_row("Инициатив пока нет", "Предложите то, что нужно дому"),
                    _empty_section_row("Опросов пока нет", "Предложите то, что нужно дому"),
                    rx.cond(AuthState.is_uk, _create_section_pill(), _create_section_pill_resident()),
                    width="100%",
                    spacing="3",
                ),
                rx.vstack(
                    _announcements_row(),
                    _collections_section(),
                    _initiatives_block(),
                    _polls_block(),
                    _debts_block(),
                    rx.cond(AuthState.is_uk, _create_section(), _create_section_resident()),
                    width="100%",
                    spacing="4",
                ),
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
            rx.code(entrance.invite_code_display, size="5"),
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
                            "Нет", variant="soft", flex="1", size="1",
                            on_click=UKAdminState.cancel_regenerate_code,
                        ),
                        rx.button(
                            "Да", color_scheme="red", flex="1", size="1",
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


def _management_header() -> rx.Component:
    return rx.vstack(
        rx.heading("Управление", size="6", weight="bold"),
        rx.cond(
            UKAdminState.current_entrance,
            rx.text(
                UKAdminState.current_entrance.building_address
                + " · подъезд "
                + UKAdminState.current_entrance.number.to_string(),
                size="2",
                color="var(--gray-9)",
            ),
        ),
        spacing="0",
        align="start",
        margin_bottom="1rem",
        width="100%",
    )


def _management_menu_item(
    icon: str, title: str, subtitle, on_click=None, badge=None
) -> rx.Component:
    """M02: пункт меню управления. Активные пункты (сейчас — только
    «Предложено жильцами») кликабельны и ведут на свой экран; остальные
    показаны для полноты картины макета, но помечены «Скоро» — реального
    экрана под ними пока нет (следующие партии работы)."""
    return section_card(
        rx.hstack(
            rx.icon(icon, size=20, color=BRAND_PURPLE if on_click else "var(--gray-8)"),
            rx.vstack(
                rx.text(
                    title,
                    size="3",
                    weight="bold",
                    color=TEXT_PRIMARY if on_click else "var(--gray-9)",
                ),
                rx.text(subtitle, size="2", color="var(--gray-9)"),
                spacing="0",
                align="start",
            ),
            rx.spacer(),
            rx.cond(badge, rx.badge(badge, color_scheme="amber")) if badge is not None else rx.fragment(),
            rx.icon("chevron-right", size=16, color="var(--gray-8)")
            if on_click
            else rx.text("Скоро", size="1", color="var(--gray-8)"),
            width="100%",
            align="center",
            spacing="3",
        ),
        cursor="pointer" if on_click else "default",
        on_click=on_click,
        opacity="1" if on_click else "0.55",
    )


def _management_menu() -> rx.Component:
    """M02 — список разделов управления домом."""
    proposals_count = (
        FinanceState.home_proposed_collections.length()
        + CommunityState.proposed_initiatives.length()
        + CommunityState.proposed_polls.length()
    )
    return rx.vstack(
        _management_header(),
        _management_menu_item(
            "inbox",
            "Предложено жильцами",
            rx.cond(
                proposals_count > 0,
                "Ждут решения — посмотрите заявки",
                "Пока нет новых предложений",
            ),
            on_click=UKAdminState.open_management_proposals,
            badge=proposals_count,
        ),
        _management_menu_item("door-open", "Заявки в дом", "Скоро"),
        _management_menu_item("megaphone", "Объявления", "Вода, свет, лифт и другие события"),
        _management_menu_item("users", "Жильцы и контакты", "Список жильцов и администраторов"),
        _management_menu_item("link", "Приглашения", "Код, ссылка и QR"),
        _management_menu_item("settings", "Настройки дома", "Адрес и управление домом"),
        width="100%",
        spacing="2",
        align="start",
    )


def _proposal_filter_chip(key: str, label: str) -> rx.Component:
    selected = UKAdminState.proposal_filter == key
    return rx.box(
        rx.text(label, size="2", weight="medium", color=rx.cond(selected, BRAND_ACTION_TEXT, "var(--gray-9)")),
        on_click=UKAdminState.set_proposal_filter(key),
        cursor="pointer",
        padding="0.45rem 0.9rem",
        border_radius="999px",
        background=rx.cond(selected, BRAND_PURPLE_TINT, "var(--gray-3)"),
        white_space="nowrap",
    )


def _proposals_screen() -> rx.Component:
    """M03 — входящие предложения жильцов (сборы/инициативы/опросы) одним
    списком с фильтром по типу. Карточки — те же, что раньше жили в
    попапах на главной (публикация/отклонение уже работают), просто
    теперь у них есть отдельный полноценный экран, как в макете."""
    show_collections = (UKAdminState.proposal_filter == "all") | (UKAdminState.proposal_filter == "collection")
    show_initiatives = (UKAdminState.proposal_filter == "all") | (UKAdminState.proposal_filter == "initiative")
    show_polls = (UKAdminState.proposal_filter == "all") | (UKAdminState.proposal_filter == "poll")
    total = (
        FinanceState.home_proposed_collections.length()
        + CommunityState.proposed_initiatives.length()
        + CommunityState.proposed_polls.length()
    )
    filtered_total = (
        rx.cond(show_collections, FinanceState.home_proposed_collections.length(), 0)
        + rx.cond(show_initiatives, CommunityState.proposed_initiatives.length(), 0)
        + rx.cond(show_polls, CommunityState.proposed_polls.length(), 0)
    )
    return rx.vstack(
        rx.hstack(
            rx.icon(
                "chevron-left",
                size=22,
                color="var(--gray-11)",
                cursor="pointer",
                on_click=UKAdminState.set_management_view("menu"),
            ),
            rx.heading("Входящие предложения", size="5", weight="bold"),
            spacing="2",
            align="center",
            margin_bottom="0.25rem",
        ),
        rx.text("Заявки от жильцов", size="2", color="var(--gray-9)", margin_bottom="0.75rem"),
        rx.hstack(
            _proposal_filter_chip("all", "Все"),
            _proposal_filter_chip("collection", "Сборы"),
            _proposal_filter_chip("initiative", "Инициативы"),
            _proposal_filter_chip("poll", "Опросы"),
            spacing="2",
            margin_bottom="1rem",
            overflow_x="auto",
        ),
        rx.cond(
            filtered_total == 0,
            rx.text(
                rx.cond(total == 0, "Пока нет предложений на рассмотрении.", "Нет предложений этого типа."),
                size="2",
                color="var(--gray-9)",
            ),
            rx.fragment(
                rx.cond(show_collections, rx.foreach(FinanceState.home_proposed_collections, _proposed_collection_card)),
                rx.cond(show_initiatives, rx.foreach(CommunityState.proposed_initiatives, _proposed_initiative_card)),
                rx.cond(show_polls, rx.foreach(CommunityState.proposed_polls, _proposed_poll_card)),
            ),
        ),
        width="100%",
        align="start",
    )


def management_tab() -> rx.Component:
    return rx.match(
        UKAdminState.management_view,
        ("proposals", _proposals_screen()),
        _management_menu(),
    )
