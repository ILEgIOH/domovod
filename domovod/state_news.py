"""Новости от управляющей компании."""

from __future__ import annotations

from typing import List

import reflex as rx
from pydantic import BaseModel
from sqlmodel import select

from .db import get_session
from .models import News
from .setters import make_setter
from .state import AuthState


class NewsItem(BaseModel):
    id: int
    title: str
    body: str
    author_name: str
    created_at: str


class NewsState(AuthState):
    news_items: List[NewsItem] = []

    new_title: str = ""
    new_body: str = ""
    news_error: str = ""

    set_new_title = make_setter("new_title")
    set_new_body = make_setter("new_body")

    @rx.event
    def load_news(self):
        if not self.tenant_id:
            self.news_items = []
            return
        with get_session() as session:
            rows = session.exec(
                select(News)
                .where(News.tenant_id == self.tenant_id)
                .order_by(News.created_at.desc())
            ).all()
        self.news_items = [
            NewsItem(
                id=r.id,
                title=r.title,
                body=r.body,
                author_name=r.author_name,
                created_at=r.created_at.strftime("%d.%m.%Y %H:%M"),
            )
            for r in rows
        ]

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
                author_name=self.display_name,
            )
            session.add(item)
            session.commit()
        self.new_title = ""
        self.new_body = ""
        return NewsState.load_news

    @rx.event
    def delete_news(self, news_id: int):
        with get_session() as session:
            item = session.get(News, news_id)
            if item and item.tenant_id == int(self.tenant_id):
                session.delete(item)
                session.commit()
        return NewsState.load_news
