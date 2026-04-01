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


class AuthPage(ft.Container):
    def __init__(self, page: ft.Page, on_success):
        super().__init__(expand=True)
        self.page_ref = page
        self.on_success = on_success
        self._mode = 'login'    # 'login' | 'register'
        self._method = 'email'  # 'email' | 'phone'
        self.bgcolor = "transparent"
        self.padding = ft.Padding(24, 60, 24, 24)
        self._error_text = ft.Text("", color="#F44336", size=13)
        self.content = self._build()

    # ─── Построение UI ────────────────────────────────────────────────────────

    def _build(self):
        is_email = self._method == 'email'
        is_register = self._mode == 'register'

        self._contact_field = ft.TextField(
            label="Email" if is_email else "Номер телефона",
            keyboard_type=ft.KeyboardType.EMAIL if is_email else ft.KeyboardType.PHONE,
            prefix_icon=ft.Icons.EMAIL_OUTLINED if is_email else ft.Icons.PHONE_OUTLINED,
            border_color="#6C63FF",
        )
        self._password_field = ft.TextField(
            label="Пароль",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK_OUTLINED,
            border_color="#6C63FF",
        )
        self._confirm_field = ft.TextField(
            label="Подтвердите пароль",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK_OUTLINED,
            border_color="#6C63FF",
        ) if is_register else None

        fields = [self._contact_field, self._password_field]
        if self._confirm_field:
            fields.append(self._confirm_field)

        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            controls=[
                # Лого
                ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET, size=64, color="#6C63FF"),
                ft.Container(height=8),
                ft.Text("FinControl", size=32, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                ft.Text("Управляй своими финансами", size=14, color="#888888"),
                ft.Container(height=32),

                # Карточка формы
                ft.Container(
                    bgcolor="#1A1A24",
                    border_radius=24,
                    padding=24,
                    width=float("inf"),
                    content=ft.Column([
                        ft.Text(
                            "Вход" if self._mode == 'login' else "Регистрация",
                            size=20, weight=ft.FontWeight.BOLD, color="#FFFFFF",
                        ),
                        ft.Container(height=4),
                        # Переключатель email / телефон
                        ft.Row([
                            self._method_btn("Email", "email"),
                            self._method_btn("Телефон", "phone"),
                        ], spacing=8),
                        ft.Container(height=4),
                        *fields,
                        self._error_text,
                        ft.ElevatedButton(
                            "Войти" if self._mode == 'login' else "Зарегистрироваться",
                            style=ft.ButtonStyle(bgcolor="#6C63FF", color="#FFFFFF"),
                            width=float("inf"),
                            on_click=self._on_submit,
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
                            color="#888888", size=13,
                        ),
                        ft.TextButton(
                            "Войти" if is_register else "Зарегистрироваться",
                            style=ft.ButtonStyle(color="#6C63FF"),
                            on_click=lambda e: self._toggle_mode(),
                        ),
                    ],
                ),
            ],
        )

    def _rebuild(self):
        self._error_text = ft.Text("", color="#F44336", size=13)
        self.content = self._build()
        self.page_ref.update()

    def _method_btn(self, label, value):
        active = self._method == value
        return ft.ElevatedButton(
            label,
            style=ft.ButtonStyle(
                bgcolor="#6C63FF" if active else "#2A2A35",
                color="#FFFFFF",
            ),
            on_click=lambda e, v=value: self._set_method(v),
        )

    # ─── Обработчики ──────────────────────────────────────────────────────────

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
        contact = (self._contact_field.value or "").strip()
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
            field = "email" if is_email else "phone"
            existing = conn.execute(
                f"SELECT id FROM users WHERE {field}=?", (contact,)
            ).fetchone()

            if existing:
                self._show_error("Пользователь с такими данными уже существует")
                return

            pwd_hash = hash_password(password)
            cursor = conn.execute(
                f"INSERT INTO users ({field}, password_hash) VALUES (?, ?)",
                (contact, pwd_hash)
            )
            user_id = cursor.lastrowid

        self.on_success(user_id, is_new=True)

    def _login(self, contact, password):
        is_email = self._method == 'email'
        field = "email" if is_email else "phone"
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
