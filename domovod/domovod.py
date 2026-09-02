"""Домовод — мини-приложение для жителей и управляющих компаний."""

import reflex as rx

from .db import init_db
from .pages.landing import landing
from .pages.resident_dashboard import resident_dashboard
from .pages.uk_dashboard import uk_dashboard
from .state import AuthState
from .state_chat import ChatState
from .state_finance import FinanceState
from .state_news import NewsState
from .state_uk_admin import UKAdminState

init_db()

app = rx.App()

app.add_page(landing, route="/", title="Домовод")

app.add_page(
    uk_dashboard,
    route="/uk",
    title="Домовод · УК",
    on_load=[
        AuthState.require_uk,
        NewsState.load_news,
        UKAdminState.load_admin_data,
        FinanceState.load_uk_finance,
    ],
)

app.add_page(
    resident_dashboard,
    route="/app",
    title="Домовод",
    on_load=[
        AuthState.require_resident,
        NewsState.load_news,
        ChatState.load_chat,
        ChatState.start_live,
        FinanceState.load_resident_finance,
    ],
)
