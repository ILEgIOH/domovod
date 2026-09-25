"""Объявления от управляющей компании (B01–B05)."""

from __future__ import annotations

import asyncio
from typing import List

import reflex as rx
from pydantic import BaseModel
from sqlmodel import select

from .db import get_session
from .models import News
from .setters import make_setter
from .state import AuthState

POLL_INTERVAL = 4

CATEGORY_META = {
    "water": ("Вода", "droplet"),
    "power": ("Свет", "zap"),
    "elevator": ("Лифт", "grid-2x2"),
    "general": ("Общее", "ellipsis"),
}
CATEGORY_ORDER = ["water", "power", "elevator", "general"]


def _icon_for(category: str) -> str:
    return CATEGORY_META.get(category, CATEGORY_META["general"])[1]


class NewsItem(BaseModel):
    id: int
    title: str
    body: str
    period_text: str
    category: str
    icon: str
    urgency: str
    author_name: str
    created_at: str


class NewsState(AuthState):
    news_items: List[NewsItem] = []

    announcements_view: str = "list"  # "list" | "editor"
    editor_id: int = 0
    new_title: str = ""
    new_body: str = ""
    new_period: str = ""
    new_category: str = "general"
    new_urgency: str = "normal"
    news_error: str = ""
    confirm_delete_id: int = 0
    is_live: bool = False

    set_new_title = make_setter("new_title")
    set_new_body = make_setter("new_body")
    set_new_period = make_setter("new_period")
    set_new_category = make_setter("new_category")
    set_new_urgency = make_setter("new_urgency")

    def _query_news(self) -> List[NewsItem]:
        entrance_id = int(self.viewing_entrance_id or 0)
        if not entrance_id:
            return []
        with get_session() as session:
            rows = session.exec(
                select(News)
                .where(News.entrance_id == entrance_id)
                .order_by(News.created_at.desc())
            ).all()
        return [
            NewsItem(
                id=r.id,
                title=r.title,
                body=r.body,
                period_text=r.period_text,
                category=r.category,
                icon=_icon_for(r.category),
                urgency=r.urgency,
                author_name=r.author_name,
                created_at=r.created_at.strftime("%d.%m.%Y %H:%M"),
            )
            for r in rows
        ]

    @rx.event
    def load_news(self):
        self.news_items = self._query_news()

    @rx.event
    def set_announcements_view(self, view: str):
        self.announcements_view = view

    @rx.event
    def reset_editor(self):
        """Свежая форма — и для B02 из хаба «Объявления», и для M06
        «Создать в доме» (иначе оставшийся editor_id от предыдущей правки
        превратил бы создание нового объявления в правку старого)."""
        self.editor_id = 0
        self.new_title = ""
        self.new_body = ""
        self.new_period = ""
        self.new_category = "general"
        self.new_urgency = "normal"
        self.news_error = ""

    @rx.event
    def open_editor(self, news_id: int = 0):
        """B02/B03 — пустая форма для нового объявления, либо предзаполненная
        для правки существующего (news_id > 0)."""
        self.reset_editor()
        if news_id:
            item = next((n for n in self.news_items if n.id == news_id), None)
            if not item:
                return
            self.editor_id = news_id
            self.new_title = item.title
            self.new_body = item.body
            self.new_period = item.period_text
            self.new_category = item.category
            self.new_urgency = item.urgency
        self.announcements_view = "editor"

    @rx.event
    def create_news(self):
        """B02/B03 «Опубликовать» — создаёт новое объявление либо обновляет
        существующее (editor_id > 0), в зависимости от того, как открыли форму."""
        self.news_error = ""
        title = self.new_title.strip()
        body = self.new_body.strip()
        if not title or not body:
            self.news_error = "Заполните заголовок и текст"
            return
        entrance_id = int(self.viewing_entrance_id or 0)
        if not entrance_id:
            self.news_error = "Выберите подъезд"
            return
        with get_session() as session:
            if self.editor_id:
                row = session.get(News, self.editor_id)
                if not row or row.tenant_id != int(self.tenant_id):
                    return
                row.title = title
                row.body = body
                row.period_text = self.new_period.strip()
                row.category = self.new_category
                row.urgency = self.new_urgency
                session.add(row)
            else:
                session.add(
                    News(
                        entrance_id=entrance_id,
                        tenant_id=self.tenant_id,
                        title=title,
                        body=body,
                        period_text=self.new_period.strip(),
                        category=self.new_category,
                        urgency=self.new_urgency,
                        author_name=self.display_name,
                    )
                )
            session.commit()
        self.reset_editor()
        self.announcements_view = "list"
        return NewsState.load_news

    @rx.event
    def delete_news(self, news_id: int):
        """Мгновенное удаление — используется «крестиком» на плашке
        объявления в «Доме» (H02), без подтверждения, как было и раньше."""
        with get_session() as session:
            item = session.get(News, news_id)
            if item and item.tenant_id == int(self.tenant_id):
                session.delete(item)
                session.commit()
        return NewsState.load_news

    @rx.event
    def ask_delete_news(self, news_id: int):
        self.confirm_delete_id = news_id

    @rx.event
    def cancel_delete_news(self):
        self.confirm_delete_id = 0

    @rx.event
    def confirm_delete_news(self):
        """M10 — подтверждённое удаление публикации из хаба «Объявления»."""
        news_id = self.confirm_delete_id
        self.confirm_delete_id = 0
        self.editor_id = 0
        with get_session() as session:
            item = session.get(News, news_id)
            if item and item.tenant_id == int(self.tenant_id):
                session.delete(item)
                session.commit()
        self.announcements_view = "list"
        return NewsState.load_news

    @rx.event
    def stop_live(self):
        self.is_live = False

    @rx.event(background=True)
    async def start_live(self):
        """Периодически подтягивает новости, чтобы изменения от УК были
        видны жителю без обновления страницы (и наоборот, у другой УК —
        не пересекаются, т.к. фильтр по подъезду)."""
        async with self:
            if self.is_live or not self.viewing_entrance_id:
                return
            self.is_live = True
        try:
            while True:
                await asyncio.sleep(POLL_INTERVAL)
                async with self:
                    if not self.is_live:
                        return
                    self.news_items = self._query_news()
        finally:
            async with self:
                self.is_live = False
