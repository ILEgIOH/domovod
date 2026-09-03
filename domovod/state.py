"""Базовое состояние: аутентификация и мультитенантная сессия."""

from __future__ import annotations

import secrets

import reflex as rx
from sqlmodel import select

from .db import get_session
from .max_stub import STUB_DISPLAY_NAME, generate_device_id
from .models import Building, Entrance, Resident, Tenant
from .security import hash_password, verify_password
from .setters import make_setter

# --- фиксированный демо-стенд для проверки в один клик, без ввода данных ---
DEMO_UK_EMAIL = "demo-uk@domovod.test"
DEMO_UK_NAME = "Демо УК"
DEMO_BUILDING_ADDRESS = "ул. Демо, д. 1"
DEMO_APARTMENT = "1"


class AuthState(rx.State):
    """Хранит текущую сессию пользователя (УК или житель).

    Значения сохраняются в sessionStorage браузера: сессия переживает
    перезагрузку страницы, но не «расшаривается» между вкладками — иначе
    вход как УК в одной вкладке и как житель в другой перезаписывали бы
    друг друга (sessionStorage, в отличие от localStorage, свой у каждой
    вкладки).
    """

    auth_view: str = "choose"

    role: str = rx.SessionStorage("")
    user_id: int = rx.SessionStorage(0)
    tenant_id: int = rx.SessionStorage(0)
    entrance_id: int = rx.SessionStorage(0)
    building_id: int = rx.SessionStorage(0)
    display_name: str = rx.SessionStorage("")
    apartment: str = rx.SessionStorage("")

    # Заглушка "идентификации через MAX" — стабильный id на браузер/устройство,
    # пока не подключён настоящий MAX Bridge.
    max_device_id: str = rx.LocalStorage("")

    # --- поля форм входа/регистрации ---
    login_email: str = ""
    login_password: str = ""
    login_error: str = ""

    reg_company_name: str = ""
    reg_email: str = ""
    reg_password: str = ""
    reg_phone: str = ""
    reg_error: str = ""

    res_invite_code: str = ""
    res_full_name: str = ""
    res_apartment: str = ""
    res_phone: str = ""
    res_password: str = ""
    res_error: str = ""

    res_login_phone: str = ""
    res_login_password: str = ""
    res_login_error: str = ""

    # --- вход по ссылке/QR-коду (/join?code=...) ---
    join_error: str = ""
    join_entrance_label: str = ""
    join_entrance_id: int = 0
    res_household_size: str = ""
    # Квартира уже занята другим жителем — сколько там живёт человек
    # определяет только тот, кто зарегистрировал её первым.
    join_apartment_taken: bool = False
    join_apartment_household: int = 0

    set_auth_view = make_setter("auth_view")
    set_res_household_size = make_setter("res_household_size")
    set_login_email = make_setter("login_email")
    set_login_password = make_setter("login_password")
    set_reg_company_name = make_setter("reg_company_name")
    set_reg_email = make_setter("reg_email")
    set_reg_password = make_setter("reg_password")
    set_reg_phone = make_setter("reg_phone")
    set_res_invite_code = make_setter("res_invite_code")
    set_res_full_name = make_setter("res_full_name")
    set_res_apartment = make_setter("res_apartment")
    set_res_phone = make_setter("res_phone")
    set_res_password = make_setter("res_password")
    set_res_login_phone = make_setter("res_login_phone")
    set_res_login_password = make_setter("res_login_password")

    @rx.var
    def is_uk(self) -> bool:
        return self.role == "uk" and self.user_id != 0

    @rx.var
    def is_resident(self) -> bool:
        return self.role == "resident" and self.user_id != 0

    def _reset_session(self) -> None:
        self.role = ""
        self.user_id = 0
        self.tenant_id = 0
        self.entrance_id = 0
        self.building_id = 0
        self.display_name = ""
        self.apartment = ""

    @rx.event
    def logout(self):
        self._reset_session()
        return rx.redirect("/")

    @rx.event
    def require_uk(self):
        # On a hard refresh, on_load can fire before the role/user_id
        # LocalStorage values finish syncing from the browser. Only bounce
        # to the landing page once hydration has actually completed, so a
        # refresh doesn't spuriously log the user out.
        if self.is_hydrated and not self.is_uk:
            return rx.redirect("/")

    @rx.event
    def require_resident(self):
        if self.is_hydrated and not self.is_resident:
            return rx.redirect("/")

    # ---------------- УК: вход/регистрация ----------------

    @rx.event
    def uk_login(self):
        self.login_error = ""
        email = self.login_email.strip().lower()
        if not email or not self.login_password:
            self.login_error = "Введите email и пароль"
            return
        with get_session() as session:
            tenant = session.exec(select(Tenant).where(Tenant.email == email)).first()
        if not tenant or not verify_password(self.login_password, tenant.password_hash):
            self.login_error = "Неверный email или пароль"
            return
        self.role = "uk"
        self.user_id = tenant.id
        self.tenant_id = tenant.id
        self.display_name = tenant.name
        self.login_password = ""
        return rx.redirect("/uk")

    @rx.event
    def uk_register(self):
        self.reg_error = ""
        name = self.reg_company_name.strip()
        email = self.reg_email.strip().lower()
        if not name or not email:
            self.reg_error = "Укажите название компании и email"
            return
        if len(self.reg_password) < 4:
            self.reg_error = "Пароль должен быть не короче 4 символов"
            return
        with get_session() as session:
            existing = session.exec(select(Tenant).where(Tenant.email == email)).first()
            if existing:
                self.reg_error = "Компания с таким email уже зарегистрирована"
                return
            tenant = Tenant(
                name=name,
                email=email,
                password_hash=hash_password(self.reg_password),
                phone=self.reg_phone.strip(),
            )
            session.add(tenant)
            session.commit()
            session.refresh(tenant)
            tenant_id = tenant.id
            tenant_name = tenant.name
        self.role = "uk"
        self.user_id = tenant_id
        self.tenant_id = tenant_id
        self.display_name = tenant_name
        self.reg_password = ""
        return rx.redirect("/uk")

    # ---------------- Житель: вход/регистрация ----------------

    @rx.event
    def resident_register(self):
        self.res_error = ""
        code = self.res_invite_code.strip().upper()
        name = self.res_full_name.strip()
        apt = self.res_apartment.strip()
        phone = self.res_phone.strip()
        if not code or not name or not apt or not phone:
            self.res_error = "Заполните все поля"
            return
        if len(self.res_password) < 4:
            self.res_error = "Пароль должен быть не короче 4 символов"
            return
        with get_session() as session:
            entrance = session.exec(
                select(Entrance).where(Entrance.invite_code == code)
            ).first()
            if not entrance:
                self.res_error = "Код приглашения не найден. Уточните его в УК"
                return
            existing = session.exec(
                select(Resident).where(Resident.phone == phone)
            ).first()
            if existing:
                self.res_error = "Житель с таким телефоном уже зарегистрирован"
                return
            resident = Resident(
                tenant_id=entrance.tenant_id,
                entrance_id=entrance.id,
                full_name=name,
                apartment=apt,
                phone=phone,
                password_hash=hash_password(self.res_password),
            )
            session.add(resident)
            session.commit()
            session.refresh(resident)
            r_id, t_id, e_id, b_id, r_name, r_apt = (
                resident.id,
                resident.tenant_id,
                resident.entrance_id,
                entrance.building_id,
                resident.full_name,
                resident.apartment,
            )
        self.role = "resident"
        self.user_id = r_id
        self.tenant_id = t_id
        self.entrance_id = e_id
        self.building_id = b_id
        self.display_name = r_name
        self.apartment = r_apt
        self.res_password = ""
        return rx.redirect("/app")

    @rx.event
    def resident_login(self):
        self.res_login_error = ""
        phone = self.res_login_phone.strip()
        if not phone or not self.res_login_password:
            self.res_login_error = "Введите телефон и пароль"
            return
        with get_session() as session:
            resident = session.exec(
                select(Resident).where(Resident.phone == phone)
            ).first()
            if (
                not resident
                or not resident.password_hash
                or not verify_password(self.res_login_password, resident.password_hash)
            ):
                self.res_login_error = "Неверный телефон или пароль"
                return
            entrance = session.get(Entrance, resident.entrance_id)
            r_id, t_id, e_id, b_id, r_name, r_apt = (
                resident.id,
                resident.tenant_id,
                resident.entrance_id,
                entrance.building_id if entrance else 0,
                resident.full_name,
                resident.apartment,
            )
        self.role = "resident"
        self.user_id = r_id
        self.tenant_id = t_id
        self.entrance_id = e_id
        self.building_id = b_id
        self.display_name = r_name
        self.apartment = r_apt
        self.res_login_password = ""
        return rx.redirect("/app")

    # ---------------- Житель: вход по ссылке/QR-коду (через MAX) ----------------

    def _login_resident_record(self, resident: Resident, entrance: Entrance) -> None:
        self.role = "resident"
        self.user_id = resident.id
        self.tenant_id = resident.tenant_id
        self.entrance_id = resident.entrance_id
        self.building_id = entrance.building_id
        self.display_name = resident.full_name
        self.apartment = resident.apartment

    @rx.event
    def join_via_code(self):
        """Обрабатывает /join?code=...: если это устройство уже заходило
        по этому приглашению — сразу авторизует (как в реальном MAX, где
        личность приходит автоматически при каждом открытии мини-аппа).
        Иначе просит только квартиру — имя и id подставляет заглушка MAX.
        """
        self.join_error = ""
        self.join_entrance_label = ""
        if self.is_resident:
            return rx.redirect("/app")
        code = self.router.url.query_parameters.get("code", "").strip().upper()
        if not code:
            self.join_error = "В ссылке не указан код приглашения. Уточните её в управляющей компании."
            return
        if not self.max_device_id:
            self.max_device_id = generate_device_id()
        with get_session() as session:
            entrance = session.exec(
                select(Entrance).where(Entrance.invite_code == code)
            ).first()
            if not entrance:
                self.join_error = "Код приглашения недействителен. Уточните ссылку в управляющей компании."
                return

            existing = session.exec(
                select(Resident).where(Resident.max_user_id == self.max_device_id)
            ).first()
            if existing:
                self._login_resident_record(existing, entrance)
                return rx.redirect("/app")

            building = session.get(Building, entrance.building_id)
            label = f"{building.address if building else '?'} · подъезд {entrance.number}"
            entrance_id = entrance.id
        self.res_invite_code = code
        self.res_apartment = ""
        self.res_household_size = ""
        self.res_error = ""
        self.join_entrance_label = label
        self.join_entrance_id = entrance_id
        self.join_apartment_taken = False
        self.join_apartment_household = 0

    @rx.event
    def check_join_apartment(self):
        """Смотрит, не зарегистрирована ли уже эта квартира в подъезде —
        если да, число жильцов подставляется существующее и не редактируется."""
        apt = self.res_apartment.strip()
        if not apt or not self.join_entrance_id:
            self.join_apartment_taken = False
            self.join_apartment_household = 0
            return
        with get_session() as session:
            existing = session.exec(
                select(Resident).where(
                    Resident.entrance_id == self.join_entrance_id,
                    Resident.apartment == apt,
                )
            ).first()
        if existing:
            self.join_apartment_taken = True
            self.join_apartment_household = existing.household_size
        else:
            self.join_apartment_taken = False
            self.join_apartment_household = 0

    @rx.event
    def join_confirm(self):
        """Довершает вход по ссылке/QR: создаёт жителя с данными-заглушкой
        MAX (без пароля) и сразу авторизует."""
        self.res_error = ""
        apt = self.res_apartment.strip()
        if not apt:
            self.res_error = "Укажите номер квартиры"
            return
        code = self.res_invite_code.strip().upper()
        if not code or not self.max_device_id:
            self.join_error = "Ссылка устарела. Откройте её заново."
            return
        with get_session() as session:
            entrance = session.exec(
                select(Entrance).where(Entrance.invite_code == code)
            ).first()
            if not entrance:
                self.join_error = "Код приглашения недействителен. Уточните ссылку в управляющей компании."
                return

            # Квартиру мог уже зарегистрировать другой член семьи по этому
            # же коду — тогда число жильцов берём у него, а не у нового.
            existing_in_apartment = session.exec(
                select(Resident).where(
                    Resident.entrance_id == entrance.id,
                    Resident.apartment == apt,
                )
            ).first()
            if existing_in_apartment:
                household = existing_in_apartment.household_size
            else:
                try:
                    household = max(int(self.res_household_size or 0), 0)
                except ValueError:
                    household = 0

            resident = Resident(
                tenant_id=entrance.tenant_id,
                entrance_id=entrance.id,
                full_name=STUB_DISPLAY_NAME,
                apartment=apt,
                household_size=household,
                max_user_id=self.max_device_id,
            )
            session.add(resident)
            session.commit()
            session.refresh(resident)
            self._login_resident_record(resident, entrance)
        return rx.redirect("/app")

    # ---------------- Демо-вход в один клик (для проверки без ввода данных) ----------------

    @staticmethod
    def _ensure_demo_tenant(session) -> Tenant:
        tenant = session.exec(select(Tenant).where(Tenant.email == DEMO_UK_EMAIL)).first()
        if not tenant:
            tenant = Tenant(
                name=DEMO_UK_NAME,
                email=DEMO_UK_EMAIL,
                password_hash=hash_password(secrets.token_hex(16)),
            )
            session.add(tenant)
            session.commit()
            session.refresh(tenant)
        return tenant

    @staticmethod
    def _ensure_demo_entrance(session, tenant: Tenant) -> Entrance:
        building = session.exec(
            select(Building).where(Building.tenant_id == tenant.id)
        ).first()
        if not building:
            building = Building(tenant_id=tenant.id, address=DEMO_BUILDING_ADDRESS)
            session.add(building)
            session.commit()
            session.refresh(building)
        entrance = session.exec(
            select(Entrance).where(Entrance.building_id == building.id)
        ).first()
        if not entrance:
            entrance = Entrance(building_id=building.id, tenant_id=tenant.id, number=1)
            session.add(entrance)
            session.commit()
            session.refresh(entrance)
        return entrance

    @rx.event
    def demo_login_uk(self):
        """Мгновенный вход в демо-кабинет УК — без email/пароля."""
        with get_session() as session:
            tenant = self._ensure_demo_tenant(session)
            tenant_id, tenant_name = tenant.id, tenant.name
        self.role = "uk"
        self.user_id = tenant_id
        self.tenant_id = tenant_id
        self.display_name = tenant_name
        return rx.redirect("/uk")

    @rx.event
    def demo_login_resident(self):
        """Мгновенный вход в демо-кабинет жителя — без формы.

        Использует тот же max_device_id, что и вход по QR/ссылке, поэтому
        у каждого браузера свой демо-житель и повторные клики не плодят
        дубликаты.
        """
        if not self.max_device_id:
            self.max_device_id = generate_device_id()
        with get_session() as session:
            tenant = self._ensure_demo_tenant(session)
            entrance = self._ensure_demo_entrance(session, tenant)
            resident = session.exec(
                select(Resident).where(Resident.max_user_id == self.max_device_id)
            ).first()
            if not resident:
                resident = Resident(
                    tenant_id=tenant.id,
                    entrance_id=entrance.id,
                    full_name=STUB_DISPLAY_NAME,
                    apartment=DEMO_APARTMENT,
                    max_user_id=self.max_device_id,
                )
                session.add(resident)
                session.commit()
                session.refresh(resident)
            self._login_resident_record(resident, entrance)
        return rx.redirect("/app")
