"""Домовод — мини-приложение для жителей и управляющих компаний."""

import reflex as rx

from .db import init_db
from .pages.join import join_page
from .pages.landing import landing
from .pages.resident_dashboard import resident_dashboard
from .pages.uk_dashboard import uk_dashboard
from .state import AuthState
from .state_community import CommunityState
from .state_contacts import ContactsState
from .state_finance import FinanceState
from .state_news import NewsState
from .state_proposals import ProposalsState
from .state_uk_admin import UKAdminState

init_db()

app = rx.App()

app.add_page(landing, route="/", title="Домовод")

app.add_page(
    join_page,
    route="/join",
    title="Домовод · Вход по ссылке",
    on_load=AuthState.join_via_code,
)

app.add_page(
    uk_dashboard,
    route="/uk",
    title="Домовод · УК",
    on_load=[
        AuthState.require_uk,
        NewsState.load_news,
        NewsState.start_live,
        UKAdminState.load_admin_data,
        UKAdminState.open_invite_after_create,
        UKAdminState.start_live,
        FinanceState.load_uk_finance,
        FinanceState.start_live,
        CommunityState.load_community,
        ContactsState.load_contacts,
    ],
)

app.add_page(
    resident_dashboard,
    route="/app",
    title="Домовод",
    on_load=[
        AuthState.require_resident,
        NewsState.load_news,
        NewsState.start_live,
        FinanceState.load_resident_finance,
        FinanceState.start_live,
        CommunityState.load_community,
        ContactsState.load_contacts,
        ProposalsState.load_my_proposals,
    ],
)
