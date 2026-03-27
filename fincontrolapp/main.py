import json
import os
import flet as ft
from pages import HomePage, TransactionsPage, GoalsPage, SettingsPage, SubscriptionsPage, IncomePage, ExpensesPage
from pages.auth import AuthPage
from components import AppTheme
from database import create_tables, get_connection

_SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session.json")


def _save_session(user_id: int):
    try:
        with open(_SESSION_FILE, "w") as f:
            json.dump({"user_id": user_id}, f)
    except Exception:
        pass


def _load_session() -> int | None:
    try:
        with open(_SESSION_FILE) as f:
            val = json.load(f).get("user_id")
            return int(val) if val else None
    except Exception:
        return None


def _clear_session():
    try:
        os.remove(_SESSION_FILE)
    except Exception:
        pass


def _show_dialog(page, dlg):
    page.show_dialog(dlg)


def _close_dialog(page, dlg):
    page.pop_dialog()


def main(page: ft.Page):
    create_tables()

    page.fonts = {
        "Montserrat": "fonts/Montserrat-Regular.ttf",
        "Montserrat Bold": "fonts/Montserrat-Bold.ttf",
        "Montserrat Semibold": "fonts/Montserrat-SemiBold.ttf",
        "Montserrat Medium": "fonts/Montserrat-Medium.ttf",
        "Montserrat Extrabold": "fonts/Montserrat-ExtraBold.ttf",
    }

    page.title = "FinControl"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 390
    page.window.height = 844
    page.bgcolor = AppTheme.BG_PAGE
    page.padding = 0
    page.data = {}

    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary="#6C63FF",
            secondary="#03DAC6",
            surface="#1A1A24",
            on_primary="#FFFFFF",
        )
    )

    inner = ft.Container(expand=True)
    page.add(
        ft.Stack(
            expand=True,
            controls=[
                ft.Image(src="bg.svg", fit="fill", expand=True),
                inner,
            ],
        )
    )

    # ─── AUTH ─────────────────────────────────────────────────────────────────

    def on_auth_success(user_id: int, is_new: bool = False):
        page.data["user_id"] = user_id
        _save_session(user_id)
        show_main_app()
        if is_new:
            _show_initial_balance_dialog(user_id)

    def _show_initial_balance_dialog(user_id: int):
        from datetime import date
        
        amount_field = ft.TextField(
            label="Сумма на счёте",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_icon=ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED,
            border_color="#6C63FF",
        )

        dlg = ft.AlertDialog(modal=True, title=ft.Text("Начальный баланс"))

        def on_skip(e):
            _close_dialog(page, dlg)

        def on_submit(e):
            try:
                if not user_id:
                    return

                raw = (amount_field.value or "").replace(" ", "").strip()
                if not raw:
                    return

                amount = float(raw.replace(",", "."))
                if amount <= 0:
                    return

                with get_connection() as conn:
                    cat = conn.execute(
                        "SELECT id FROM categories WHERE name='Начальный баланс'"
                    ).fetchone()
                    if not cat:
                        return 
                    
                    # LIMIT 1 нужен, чтобы не создавать дубликаты при повторном открытии диалога
                    existing = conn.execute(
                        """
                        SELECT id FROM transactions
                        WHERE user_id=? 
                            AND category_id=? 
                        LIMIT 1 
                        """, 
                        (user_id, cat['id']),
                    ).fetchone()
                    if existing:
                        conn.execute(
                            """UPDATE transactions 
                            SET amount=?, date=? 
                            WHERE id=?
                            """,
                            (amount, str(date.today()), existing['id']),
                        )
                    else:
                        conn.execute(
                            """
                            INSERT INTO transactions (user_id, type, amount, category_id, description, date)
                            VALUES (?, 'income', ?, ?, 'Начальный баланс', ?)
                            """,
                            (user_id, amount, cat['id'], str(date.today())),
                        )
            except ValueError:
                page.snack_bar = ft.SnackBar(ft.Text("Введите корректную сумму"), open=True)
                page.update()
                return
            except Exception:
                page.snack_bar = ft.SnackBar(ft.Text("Не удалось сохранить баланс"), open=True)
                page.update()
            finally:
                _close_dialog(page, dlg)

        dlg.content = ft.Column([
            ft.Text("Сколько денег у тебя сейчас?", color="#888888", size=14),
            ft.Text("Это поможет балансу сразу отображать реальную сумму.",
                    color="#555555", size=12),
            amount_field,
        ], tight=True, spacing=12)
        dlg.actions = [
            ft.TextButton("Пропустить", on_click=on_skip),
            ft.TextButton("Сохранить", on_click=on_submit),
        ]
        _show_dialog(page, dlg)

    def show_auth():
        inner.content = AuthPage(page, on_success=on_auth_success)
        page.update()

    # ─── ОСНОВНОЕ ПРИЛОЖЕНИЕ ──────────────────────────────────────────────────

    def show_main_app():
        content = ft.Container(expand=True)
        nav_container = ft.Container(expand=False)

        def build_nav(selected_index: int) -> ft.Container:
            items = [
                ("navigation/home.svg",         0),
                ("navigation/transactions.svg", 1),
                ("navigation/goals.svg",        2),
                ("navigation/settings.svg",     3),
            ]

            def nav_item(src, index):
                active = selected_index == index
                return ft.GestureDetector(
                    on_tap=lambda e, i=index: navigate(i),
                    content=ft.Container(
                        width=56, height=56,
                        border_radius=16,
                        bgcolor="#3D3D6B" if active else "#5B6EC7",
                        alignment=ft.Alignment(0, 0),
                        content=ft.Image(src=src, width=28, height=28),
                    ),
                )

            return ft.Container(
                height=80,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Stack(
                    controls=[
                        ft.Container(
                            expand=True,
                            content=ft.Image(src="navigation/nav_bg.svg", fit="fill", expand=True),
                        ),
                        ft.Container(
                            expand=True,
                            padding=ft.Padding(left=16, right=16, top=12, bottom=24),
                            content=ft.Row(
                                controls=[nav_item(src, i) for src, i in items],
                                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                            ),
                        ),
                    ],
                ),
            )

        def navigate(index: int):
            pages[index].refresh()
            content.content = pages[index]
            content.update()
            nav_container.content = build_nav(index)
            nav_container.update()

        pages = {
            0: HomePage(page),
            1: TransactionsPage(page),
            2: GoalsPage(page),
            3: SettingsPage(page),
            4: SubscriptionsPage(page),
            5: IncomePage(page),
            6: ExpensesPage(page),
        }

        def logout():
            _clear_session()
            page.data = {}
            show_auth()

        page.data["navigate"] = navigate
        page.data["logout"] = logout
        page.data["pages"] = pages
        page.data["show_balance_dialog"] = lambda: _show_initial_balance_dialog(
            page.data.get("user_id")
        )

        content.content = pages[0]
        nav_container.content = build_nav(0)

        inner.content = ft.Column(
            controls=[content, nav_container],
            expand=True,
            spacing=0,
        )
        page.update()

    # ─── СТАРТ ────────────────────────────────────────────────────────────────

    stored_id = _load_session()
    if stored_id:
        with get_connection() as conn:
            user = conn.execute("SELECT id FROM users WHERE id=?", (stored_id,)).fetchone()
        if user:
            page.data["user_id"] = stored_id
            show_main_app()
            return

    show_auth()


ft.run(main, assets_dir="assets")
