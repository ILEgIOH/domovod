"""Новости от управляющей компании."""

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


ICON_CHOICES = ["bell", "zap", "droplet", "wrench", "triangle-alert", "megaphone"]


class NewsItem(BaseModel):
    id: int
    title: str
    body: str
    icon: str
    author_name: str
    created_at: str


class NewsState(AuthState):
    news_items: List[NewsItem] = []

    new_title: str = ""
    new_body: str = ""
    new_icon: str = "bell"
    news_error: str = ""
    is_live: bool = False

    set_new_title = make_setter("new_title")
    set_new_body = make_setter("new_body")
    set_new_icon = make_setter("new_icon")

    def _query_news(self) -> List[NewsItem]:
        if not self.tenant_id:
            return []
        with get_session() as session:
            rows = session.exec(
                select(News)
                .where(News.tenant_id == self.tenant_id)
                .order_by(News.created_at.desc())
            ).all()
        return [
            NewsItem(
                id=r.id,
                title=r.title,
                body=r.body,
                icon=r.icon or "bell",
                author_name=r.author_name,
                created_at=r.created_at.strftime("%d.%m.%Y %H:%M"),
            )
            for r in rows
        ]

    @rx.event
    def load_news(self):
        self.news_items = self._query_news()

    @rx.event
    def create_news(self):
        self.news_error = ""
        if not self.new_title.strip() or not self.new_body.strip():
            self.news_error = "Заполните заголовок и текст новости"
            return
        with get_session() as session:
            item = News(
                tenant_id=self.tenant_id,
                title=self.new_title.strip(),
                body=self.new_body.strip(),
                icon=self.new_icon,
                author_name=self.display_name,
            )
            session.add(item)
            session.commit()
        self.new_title = ""
        self.new_body = ""
        self.new_icon = "bell"
        return NewsState.load_news

    @rx.event
    def delete_news(self, news_id: int):
        with get_session() as session:
            item = session.get(News, news_id)
            if item and item.tenant_id == int(self.tenant_id):
                session.delete(item)
                session.commit()
        return NewsState.load_news

    @rx.event
    def stop_live(self):
        self.is_live = False

    @rx.event(background=True)
    async def start_live(self):
        """Периодически подтягивает новости, чтобы изменения от УК были
        видны жителю без обновления страницы (и наоборот, у другой УК —
        не пересекаются, т.к. фильтр по tenant_id)."""
        async with self:
            if self.is_live or not self.tenant_id:
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
