"""Чат жильцов одного подъезда с обновлением в реальном времени (polling)."""

from __future__ import annotations

import asyncio
from typing import List

import reflex as rx
from pydantic import BaseModel
from sqlmodel import select

from .db import get_session
from .models import ChatMessage
from .setters import make_setter
from .state import AuthState

POLL_INTERVAL = 2.5


class ChatBubble(BaseModel):
    id: int
    sender_name: str
    text: str
    created_at: str
    is_mine: bool


class ChatState(AuthState):
    messages: List[ChatBubble] = []
    new_message: str = ""
    is_live: bool = False
    _last_id: int = 0

    set_new_message = make_setter("new_message")

    def _fetch(self) -> list[ChatMessage]:
        with get_session() as session:
            return list(
                session.exec(
                    select(ChatMessage)
                    .where(ChatMessage.entrance_id == self.entrance_id)
                    .order_by(ChatMessage.created_at.asc())
                ).all()
            )

    @rx.event
    def load_chat(self):
        if not self.entrance_id:
            self.messages = []
            return
        rows = self._fetch()
        self.messages = [
            ChatBubble(
                id=r.id,
                sender_name=r.sender_name,
                text=r.text,
                created_at=r.created_at.strftime("%H:%M"),
                is_mine=(r.sender_id == int(self.user_id)),
            )
            for r in rows
        ]
        self._last_id = rows[-1].id if rows else 0

    @rx.event
    def handle_key(self, key: str):
        if key == "Enter":
            return ChatState.send_message

    @rx.event
    def send_message(self):
        text = self.new_message.strip()
        if not text or not self.entrance_id:
            return
        with get_session() as session:
            session.add(
                ChatMessage(
                    entrance_id=self.entrance_id,
                    tenant_id=self.tenant_id,
                    sender_id=self.user_id,
                    sender_name=self.display_name,
                    text=text,
                )
            )
            session.commit()
        self.new_message = ""
        return ChatState.load_chat

    @rx.event
    def stop_live(self):
        self.is_live = False

    @rx.event(background=True)
    async def start_live(self):
        async with self:
            if self.is_live or not self.entrance_id:
                return
            self.is_live = True
        try:
            while True:
                await asyncio.sleep(POLL_INTERVAL)
                async with self:
                    if not self.is_live:
                        return
                    rows = self._fetch()
                    if rows and rows[-1].id != self._last_id:
                        self.messages = [
                            ChatBubble(
                                id=r.id,
                                sender_name=r.sender_name,
                                text=r.text,
                                created_at=r.created_at.strftime("%H:%M"),
                                is_mine=(r.sender_id == int(self.user_id)),
                            )
                            for r in rows
                        ]
                        self._last_id = rows[-1].id
        finally:
            async with self:
                self.is_live = False
