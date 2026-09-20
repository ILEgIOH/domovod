"""Базовое состояние: аутентификация и мультитенантная сессия."""

from __future__ import annotations

import secrets

import reflex as rx
from reflex.event import KeyInputInfo
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

    # Подъезд, для которого сейчас показывается общий экран «Дом»
    # (объявления/сборы/инициативы/опросы). У жителя всегда свой — не
    # переключается; у УК выбирается из своих подъездов (по умолчанию первый).
    viewing_entrance_id: int = rx.SessionStorage(0)
    # Человекочитаемый адрес+подъезд жителя (УК берёт его из UKAdminState.current_entrance).
    home_label: str = rx.SessionStorage("")

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
    res_apartment: str = ""
    res_error: str = ""

    # --- экран «Введите код» (ручной ввод, без ссылки/QR): 6 отдельных
    # однобуквенных/одноцифровых полей (как OTP-ввод) — c1..c3 буквы,
    # c4..c6 цифры. Так физически нельзя вставить символ «в середину» или
    # ввести не тот тип символа не в свою позицию; курсор всегда переходит
    # к следующему полю сам, дефис между блоками статичный.
    join_code_c1: str = ""
    join_code_c2: str = ""
    join_code_c3: str = ""
    join_code_c4: str = ""
    join_code_c5: str = ""
    join_code_c6: str = ""
    join_code_error: bool = False

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
    set_res_apartment = make_setter("res_apartment")

    @rx.var
    def is_uk(self) -> bool:
        return self.role == "uk" and self.user_id != 0

    @rx.var
    def is_resident(self) -> bool:
        return self.role == "resident" and self.user_id != 0

    @rx.var
    def join_code_ready(self) -> bool:
        return all(
            [
                self.join_code_c1,
                self.join_code_c2,
                self.join_code_c3,
                self.join_code_c4,
                self.join_code_c5,
                self.join_code_c6,
            ]
        )

    def _reset_session(self) -> None:
        self.role = ""
        self.user_id = 0
        self.tenant_id = 0
        self.entrance_id = 0
        self.building_id = 0
        self.display_name = ""
        self.apartment = ""
        self.viewing_entrance_id = 0
        self.home_label = ""

    @rx.event
    def set_viewing_entrance_id(self, value: str):
        """УК выбирает, какой подъезд сейчас показывать на экране «Дом»."""
        try:
            self.viewing_entrance_id = int(value)
        except (TypeError, ValueError):
            self.viewing_entrance_id = 0

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

    # ---------------- Житель: экран «Введите код» ----------------

    @rx.event
    def set_join_code_char(self, index: int, value: str):
        """index 1-3 — буквы, 4-6 — цифры. Берём последний введённый
        символ (на случай вставки/автозаполнения нескольких), проверяем
        его тип и, если он подходит своей позиции, сразу переводим фокус
        на следующее поле — так ввод идёт строго слева направо.

        Если символ не подходит, очищаем поле — но не просто присваиванием
        (Reflex не шлёт обновление на фронт, если значение var не
        изменилось, а поле и так уже пустое, поэтому браузер оставил бы
        невалидный символ висеть в DOM необработанным), а прямой правкой
        DOM через rx.call_script. Это не трогает фокус, в отличие от
        пересоздания компонента, так что курсор остаётся на месте.
        """
        raw = value.strip().upper()
        ch = raw[-1] if raw else ""
        is_letter_slot = index <= 3
        valid = ch.isalpha() if is_letter_slot else ch.isdigit()
        setattr(self, f"join_code_c{index}", ch if valid else "")
        self.join_code_error = False
        if valid and index < 6:
            return rx.set_focus(f"join_code_c{index + 1}_input")
        if not valid:
            return rx.call_script(
                f"document.getElementById('join_code_c{index}_input').value = ''"
            )

    @rx.event
    def join_code_key_down(self, index: int, key: str, info: KeyInputInfo):
        if key == "Backspace" and not getattr(self, f"join_code_c{index}") and index > 1:
            return rx.set_focus(f"join_code_c{index - 1}_input")

    @rx.event
    def open_join_code_view(self):
        self.join_code_c1 = ""
        self.join_code_c2 = ""
        self.join_code_c3 = ""
        self.join_code_c4 = ""
        self.join_code_c5 = ""
        self.join_code_c6 = ""
        self.join_code_error = False
        self.auth_view = "join_code"
        return rx.set_focus("join_code_c1_input")

    @rx.event
    def lookup_join_code(self):
        if not self.join_code_ready:
            return
        code = (
            self.join_code_c1
            + self.join_code_c2
            + self.join_code_c3
            + self.join_code_c4
            + self.join_code_c5
            + self.join_code_c6
        )
        with get_session() as session:
            entrance = session.exec(
                select(Entrance).where(Entrance.invite_code == code)
            ).first()
        if not entrance:
            self.join_code_error = True
            return
        self.join_code_error = False
        return rx.redirect(f"/join?code={code}")

    # ---------------- Житель: вход по ссылке/QR-коду (через MAX) ----------------

    def _login_resident_record(self, resident: Resident, entrance: Entrance) -> None:
        self.role = "resident"
        self.user_id = resident.id
        self.tenant_id = resident.tenant_id
        self.entrance_id = resident.entrance_id
        self.building_id = entrance.building_id
        self.display_name = resident.full_name
        self.apartment = resident.apartment
        self.viewing_entrance_id = resident.entrance_id
        with get_session() as session:
            building = session.get(Building, entrance.building_id)
        address = building.address if building else "?"
        self.home_label = f"{address} · подъезд {entrance.number}"

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
