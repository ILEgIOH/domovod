"""Общие визуальные компоненты и константы стиля («мобильный» вид мини-приложения)."""

from __future__ import annotations

import reflex as rx

MAX_WIDTH = "460px"
BG = "var(--gray-2)"
CARD_BG = "var(--gray-1)"
BORDER = "1px solid var(--gray-4)"

# Фирменные цвета проекта — точные значения из дизайн-системы спеки
# (страница D03 «Палитра»), используем напрямую, а не приближённые
# оттенки из палитры Radix.
BRAND_PURPLE = "#7885FF"
BRAND_NEON = "#E7F53C"
# Текст на Purple-поверхностях — всегда тёмный (не белый) для читаемости,
# это отдельный фирменный цвет, а не просто "black".
BRAND_ACTION_TEXT = "#343C80"
# Светлый оттенок Purple — фон карточки кода приглашения и кнопки
# «Скопировать код» (A03), сам Purple там был бы слишком ярким.
BRAND_PURPLE_TINT = "#E7E9FE"
TEXT_PRIMARY = "#202126"
TEXT_SECONDARY = "#62656F"


def phone_shell(*children, header: rx.Component | None = None) -> rx.Component:
    """Контейнер, имитирующий экран мини-приложения (мобильная ширина)."""
    return rx.box(
        rx.box(
            header or rx.fragment(),
            rx.box(
                *children,
                width="100%",
                padding="0.85rem 1rem 6rem 1rem",
            ),
            width="100%",
            max_width=MAX_WIDTH,
            min_height="100vh",
            margin="0 auto",
            background=BG,
            box_shadow="0 0 24px rgba(0,0,0,0.06)",
            position="relative",
        ),
        width="100%",
        min_height="100vh",
        background="var(--gray-3)",
    )


def brand_icon(size: int = 32) -> rx.Component:
    """Логотип — мягкая арка-дом (Purple + Neon) из макета дизайнера.
    Пока просто ведёт на главную; в будущем здесь будет переход в
    Telegram-бота для вызова служб дома."""
    return rx.link(
        rx.image(
            src="/logo.png",
            width=f"{size}px",
            height=f"{size}px",
            style={"objectFit": "contain"},
        ),
        href="/",
    )


def top_bar(title: str, subtitle: str = "", right: rx.Component | None = None) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.hstack(
                brand_icon(),
                rx.cond(
                    subtitle != "",
                    rx.text(subtitle, size="2", color="var(--gray-10)"),
                ),
                spacing="2",
                align="center",
            ),
            rx.spacer(),
            right or rx.fragment(),
            width="100%",
            align="center",
        ),
        width="100%",
        max_width=MAX_WIDTH,
        margin="0 auto",
        padding="1.1rem 1rem 0.9rem 1rem",
        position="sticky",
        top="0",
        background=BG,
        z_index="10",
        border_bottom=BORDER,
    )


def bottom_tabs(items: list[tuple[str, str, str]], value: rx.Var, on_change) -> rx.Component:
    """items: list of (tab_value, label, icon_tag)."""
    return rx.box(
        rx.hstack(
            *[
                rx.el.button(
                    rx.vstack(
                        rx.icon(icon, size=20),
                        rx.text(label, size="1"),
                        spacing="1",
                        align="center",
                    ),
                    on_click=on_change(val),
                    style={
                        "flex": "1",
                        "background": "transparent",
                        "border": "none",
                        "cursor": "pointer",
                        "padding": "0.5rem 0",
                        "color": rx.cond(
                            value == val, "var(--accent-9)", "var(--gray-9)"
                        ),
                    },
                )
                for val, label, icon in items
            ],
            width="100%",
            spacing="0",
        ),
        width="100%",
        max_width=MAX_WIDTH,
        position="fixed",
        bottom="0",
        left="50%",
        transform="translateX(-50%)",
        background=CARD_BG,
        border_top=BORDER,
        padding="0.25rem 0.5rem calc(0.25rem + env(safe-area-inset-bottom)) 0.5rem",
        z_index="20",
    )


def section_card(*children, **props) -> rx.Component:
    return rx.box(
        *children,
        width="100%",
        background=CARD_BG,
        border=BORDER,
        border_radius="14px",
        padding="1rem",
        margin_bottom="0.75rem",
        **props,
    )


def empty_state(text: str, icon: str = "inbox") -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.icon(icon, size=32, color="var(--gray-8)"),
            rx.text(text, color="var(--gray-9)", size="2"),
            spacing="2",
            align="center",
        ),
        padding="2.5rem 0",
        width="100%",
    )


def progress_bar(pct) -> rx.Component:
    return rx.box(
        rx.box(
            width=rx.cond(pct > 100, "100%", f"{pct}%"),
            height="100%",
            background="var(--accent-9)",
            border_radius="999px",
            transition="width 0.4s ease",
        ),
        width="100%",
        height="8px",
        background="var(--gray-4)",
        border_radius="999px",
        overflow="hidden",
    )


def field_label(text: str) -> rx.Component:
    return rx.text(text, size="2", weight="medium", color="var(--gray-11)", margin_bottom="0.2rem")


def error_text(message: rx.Var) -> rx.Component:
    return rx.cond(
        message != "",
        rx.callout(message, color_scheme="red", size="1", margin_bottom="0.5rem"),
        rx.fragment(),
    )
