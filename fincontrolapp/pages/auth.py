import flet as ft
import hashlib
import os
from database import get_connection


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ':' + key.hex()


def verify_password(stored: str, provided: str) -> bool:
    try:
        salt_hex, key_hex = stored.split(':')
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac('sha256', provided.encode('utf-8'), salt, 100000)
        return key.hex() == key_hex
    except Exception:
        return False


# ── Shared style constants (same as other pages) ─────────────────────────────

_CARD_GRADIENT = ft.LinearGradient(
    colors=["#ffffff", "#88A2FF"],
    begin=ft.Alignment(-2, -1),
    end=ft.Alignment(1, 2),
)

_BTN_GRADIENT = ft.RadialGradient(
    colors=["#ffffff", "#88A2FF"],
    center=ft.Alignment(0, -0.2),
    radius=4.0,
    stops=[0.0, 0.8],
)


class AuthPage(ft.Container):
    def __init__(self, page: ft.Page, on_success):
        super().__init__(expand=True)
        self.page_ref = page
        self.on_success = on_success
        self._mode = 'login'    # 'login' | 'register'
        self._method = 'email'  # 'email' | 'phone'
        self.bgcolor = "transparent"
        self.padding = ft.Padding(24, 60, 24, 24)
        self._error_text = ft.Text(
            "", color=ft.Colors.with_opacity(0.8, "#FF7E1C"),
            size=13, font_family="Montserrat SemiBold",
        )
        self.content = self._build()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self):
        is_email     = self._method == 'email'
        is_register  = self._mode == 'register'

        self._contact_field = self._field(
            label="Email" if is_email else "Номер телефона",
            icon=ft.Icons.EMAIL_OUTLINED if is_email else ft.Icons.PHONE_OUTLINED,
            keyboard=ft.KeyboardType.EMAIL if is_email else ft.KeyboardType.PHONE,
        )
        self._password_field = self._field(
            label="Пароль",
            icon=ft.Icons.LOCK_OUTLINED,
            password=True,
        )
        self._confirm_field = self._field(
            label="Подтвердите пароль",
            icon=ft.Icons.LOCK_OUTLINED,
            password=True,
        ) if is_register else None

        fields = [self._contact_field, self._password_field]
        if self._confirm_field:
            fields.append(self._confirm_field)

        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            controls=[
                # ── Логотип ──────────────────────────────────────────────────
                ft.Container(
                    width=80, 
                    border_radius=22,
                    alignment=ft.Alignment(0, 0),
                    padding=0,
                    margin=0,
                    content=ft.Image(
                             src="logo.svg",   # путь относительно папки assets/
                             width=80,
                             height=80,
                             fit="contain",
                        ),
                
                ),
                ft.Row(
                       spacing=0,
                       tight=True,
                       controls=[
                ft.Text(
                    "Fin",
                    size=32,
                    font_family="Montserrat Extrabold",
                    color="#6976EB",
                    weight=ft.FontWeight.W_800,
                ),
                ft.Text(
                    "Control",
                    size=32,
                    font_family="Montserrat Extrabold",
                    color="#000000",
                    weight=ft.FontWeight.W_800,
                ),
                       ],
                ),
                ft.Text(
                    "Управляй своими финансами",
                    size=14,
                    font_family="Montserrat SemiBold",
                    color=ft.Colors.with_opacity(0.45, "#000000"),
                ),
                ft.Container(height=28),

                # ── Карточка формы ───────────────────────────────────────────
                ft.Container(
                    border_radius=24,
                    padding=20,
                    width=float("inf"),
                    gradient=_CARD_GRADIENT,
                    content=ft.Column([
                        ft.Text(
                            "Вход" if self._mode == 'login' else "Регистрация",
                            size=20,
                            font_family="Montserrat Semibold",
                            color="#000000",
                            weight=ft.FontWeight.W_700,
                        ),
                        ft.Container(height=2),

                        # Переключатель email / телефон
                        ft.Row([
                            self._method_chip("Email",   "email"),
                            self._method_chip("Телефон", "phone"),
                        ], spacing=8),

                        ft.Container(height=2),
                        *fields,
                        self._error_text,

                        # Кнопка submit
                        ft.Container(
                            width=float("inf"),
                            height=48,
                            border_radius=24,
                            border=ft.border.all(1.5, ft.Colors.with_opacity(0.09, "#483EB7")),
                            bgcolor=ft.Colors.with_opacity(0.08, "#483EB7"),
                            alignment=ft.Alignment(0, 0),
                            ink=True,
                            on_click=self._on_submit,
                            content=ft.Text(
                                "Войти" if self._mode == 'login' else "Зарегистрироваться",
                                font_family="Montserrat SemiBold",
                                size=16,
                                color="#000000",
                            ),
                        ),
                    ], spacing=12),
                ),

                ft.Container(height=16),

                # Переключатель login / register
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Text(
                            "Уже есть аккаунт? " if is_register else "Нет аккаунта? ",
                            color=ft.Colors.with_opacity(0.5, "#000000"),
                            size=13,
                            font_family="Montserrat SemiBold",
                        ),
                        ft.GestureDetector(
                            on_tap=lambda e: self._toggle_mode(),
                            content=ft.Text(
                                "Войти" if is_register else "Зарегистрироваться",
                                size=13,
                                font_family="Montserrat SemiBold",
                                color="#6976EB",
                            ),
                        ),
                    ],
                ),
            ],
        )

    # ── Field factory  ───────────────────────────

    def _field(self, label: str, icon=None, password: bool = False,
               keyboard=ft.KeyboardType.TEXT) -> ft.TextField:
        return ft.TextField(
            label=label,
            password=password,
            can_reveal_password=password,
            keyboard_type=keyboard,
            prefix_icon=icon,
            border_color="#6976EB",
            focused_border_color="#5D6BE8",
            border_radius=16,
            bgcolor=ft.Colors.with_opacity(0.3, "#FFFFFF"),
            label_style=ft.TextStyle(
                font_family="Montserrat SemiBold", color="#888888",
            ),
            text_style=ft.TextStyle(
                font_family="Montserrat SemiBold", size=15, color="#000000",
            ),
            error_style=ft.TextStyle(
                font_family="Montserrat Medium", size=10,
                color=ft.Colors.with_opacity(0.8, "#FF7E1C"),
            ),
        )

    # ── Method chip  ────────────

    def _method_chip(self, label: str, value: str) -> ft.Container:
        active = self._method == value
        return ft.Container(
            content=ft.Text(
                label,
                font_family="Montserrat SemiBold",
                size=13,
                color="#000000" if active else ft.Colors.with_opacity(0.6, "#000000"),
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            border_radius=20,
            border=ft.border.all(1.5, ft.Colors.with_opacity(0.09, "#6976EB")),
            bgcolor=ft.Colors.with_opacity(0.4, "#6976EB") if active else None,
            
            on_click=lambda e, v=value: self._set_method(v),
            ink=True,
        )

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _rebuild(self):
        self._error_text = ft.Text(
            "", color=ft.Colors.with_opacity(0.8, "#FF7E1C"),
            size=13, font_family="Montserrat SemiBold",
        )
        self.content = self._build()
        self.page_ref.update()

    def _set_method(self, method):
        self._method = method
        self._rebuild()

    def _toggle_mode(self):
        self._mode = 'register' if self._mode == 'login' else 'login'
        self._rebuild()

    def _show_error(self, msg):
        self._error_text.value = msg
        self.page_ref.update()

    def _on_submit(self, e):
        contact  = (self._contact_field.value or "").strip()
        password = self._password_field.value or ""

        if not contact or not password:
            self._show_error("Заполните все поля")
            return

        if self._mode == 'register':
            confirm = self._confirm_field.value or ""
            if password != confirm:
                self._show_error("Пароли не совпадают")
                return
            if len(password) < 6:
                self._show_error("Пароль минимум 6 символов")
                return
            self._register(contact, password)
        else:
            self._login(contact, password)

    def _register(self, contact, password):
        is_email = self._method == 'email'
        with get_connection() as conn:
            field    = "email" if is_email else "phone"
            existing = conn.execute(
                f"SELECT id FROM users WHERE {field}=?", (contact,)
            ).fetchone()

            if existing:
                self._show_error("Пользователь с такими данными уже существует")
                return

            pwd_hash = hash_password(password)
            cursor   = conn.execute(
                f"INSERT INTO users ({field}, password_hash) VALUES (?, ?)",
                (contact, pwd_hash),
            )
            user_id = cursor.lastrowid

        self.on_success(user_id, is_new=True)

    def _login(self, contact, password):
        is_email = self._method == 'email'
        field    = "email" if is_email else "phone"
        with get_connection() as conn:
            user = conn.execute(
                f"SELECT id, password_hash FROM users WHERE {field}=?", (contact,)
            ).fetchone()

        if not user:
            self._show_error("Пользователь не найден")
            return

        if not verify_password(user['password_hash'], password):
            self._show_error("Неверный пароль")
            return

        self.on_success(user['id'], is_new=False)
