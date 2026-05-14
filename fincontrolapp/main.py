import os  # noqa: F401
import flet as ft
from pages import (HomePage, TransactionsPage, GoalsPage, SettingsPage, SubscriptionsPage, IncomePage, ExpensesPage, AnalyticsPage, SimulatorPage, BudgetPage)
from pages.auth import AuthPage
from components import AppTheme
from controllers import (HomeController, GoalsController, SubscriptionsController,
                         TransactionsController, ExpensesController, IncomeController,
                         SettingsController, SimulatorController, BudgetController)
from database import create_tables, get_connection
import json


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
    page.bgcolor = AppTheme.BACKGROUND
    page.padding = 0
    page.data = {}
    page.data.setdefault("_s_currency", "RUB")

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
        page.session.store.set("user_id", user_id)
        show_main_app()
        _check_and_add_recurring_income(user_id)  # AUTO-1: автодобавить зарплату, если наступил новый месяц
        _check_and_charge_subscriptions(user_id)  # AUTO-2: списать подписки с charge_day ≤ сегодня
        page.data["pages"][0].refresh()  # обновить главный экран после авто-операций

    def show_auth():
        inner.content = AuthPage(page, on_success=on_auth_success)
        page.update()

    def _check_and_add_recurring_income(user_id: int):
        # AUTO-1: при входе проверяем, нужно ли зачислить зарплату за текущий месяц
        from datetime import date
        from modules.transactions.repository import TransactionRepository

        today = date.today()
        with get_connection() as con:
            repo = TransactionRepository(con)

            # Если зарплата за этот месяц уже есть — ничего не делаем
            existing = repo.get_recurring_income_for_month(user_id, today.year, today.month)
            if existing:
                return

            # Берём последнюю зарплату как шаблон (сумма, категория, описание)
            template = repo.get_last_recurring_income(user_id)
            if not template:
                return  # пользователь ещё ни разу не добавлял зарплату

            # Зачисляем 1-м числом текущего месяца
            first_of_month = date(today.year, today.month, 1).isoformat()
            repo.add_transaction(
                user_id=user_id,
                type_="income",
                amount=template["amount"],
                category_id=template["category_id"],
                description=template["description"],
                date=first_of_month,
                is_recurring=1,
            )

    def _check_and_charge_subscriptions(user_id: int):
        # AUTO-2: списываем подписки с charge_day ≤ сегодня (is_paused=0), если ещё не списывали в этом месяце
        from datetime import date
        from modules.subscriptions.repository import SubscriptionRepository
        from modules.transactions.repository import TransactionRepository

        today = date.today()
        with get_connection() as con:
            sub_repo = SubscriptionRepository(con)
            tx_repo = TransactionRepository(con)

            due = sub_repo.get_due_subscriptions(user_id, today)
            if not due:
                return []

            cat = con.execute(
                "SELECT id FROM categories WHERE name='Подписки' AND type='expense'"
            ).fetchone()
            cat_id = cat['id'] if cat else con.execute(
                "SELECT id FROM categories WHERE name='Другое' AND type='expense'"
            ).fetchone()['id']

            for sub in due:
                tx_repo.add_transaction(
                    user_id=user_id,
                    type_='expense',
                    amount=sub['amount'],
                    category_id=cat_id,
                    description=sub['name'],
                    date=today.isoformat(),
                    is_recurring=1,
                )
                sub_repo.mark_charged(sub['id'], today.isoformat())

        return

# ─── ОСНОВНОЕ ПРИЛОЖЕНИЕ ──────────────────────────────────────────────────

    def show_main_app():
        # 1. Сначала определяем uid и словарь pages
        uid = page.data["user_id"]
        pages = {
            0: HomePage(page, HomeController(uid)),
            1: AnalyticsPage(page, uid),
            2: GoalsPage(page, GoalsController(uid)),
            3: SettingsPage(page, SettingsController(uid)),
            4: SubscriptionsPage(page, SubscriptionsController(uid)),
            5: IncomePage(page, IncomeController(uid)),
            6: ExpensesPage(page, ExpensesController(uid)),
            7: TransactionsPage(page, TransactionsController(uid)),
            8: SimulatorPage(page, SimulatorController()),
        }

        # 2. Теперь можем безопасно использовать pages[0]
        content = ft.AnimatedSwitcher(
            content=pages[0],
            expand=True,
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=200,
            reverse_duration=200,
            switch_in_curve=ft.AnimationCurve.EASE_IN,
            switch_out_curve=ft.AnimationCurve.EASE_OUT,
        )
        nav_container = ft.Container(expand=False)

        def build_nav(selected_index: int) -> ft.Container:
            items = [
                ("navigation/home.svg",        0),
                ("navigation/analytics.svg",    1),
                ("navigation/goals.svg",        2),
                ("navigation/test.svg",         8),
                ("navigation/settings.svg",     3),
            ]

            def nav_item(src, index):
                active = selected_index == index
                icon_widget = ft.Image(src=src, width=28, height=28)
                return ft.GestureDetector(
                    on_tap=lambda e, i=index: navigate(i),
                    content=ft.Container(
                        width=56, height=56,
                        border_radius=16,
                        bgcolor="#3D3D6B" if active else "#5B6EC7",
                        alignment=ft.Alignment(0, 0),
                        content=icon_widget,
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
            pages[index].key = str(index) + "_" + str(id(pages[index]))
            content.content = pages[index]
            nav_container.content = build_nav(index)
            nav_container.update()

        uid = page.data["user_id"]
        pages = {
            0: HomePage(page, HomeController(uid)),
            1: AnalyticsPage(page, uid, budget_controller=BudgetController(uid)),
            2: GoalsPage(page, GoalsController(uid)),
            3: SettingsPage(page, SettingsController(uid)),
            4: SubscriptionsPage(page, SubscriptionsController(uid)),
            5: IncomePage(page, IncomeController(uid)),
            6: ExpensesPage(page, ExpensesController(uid)),
            7: TransactionsPage(page, TransactionsController(uid)),
            8: SimulatorPage(page, SimulatorController()),
            9: BudgetPage(page, BudgetController(uid)),
        }

        def logout():
            page.session.store.remove("user_id")
            page.data = {}
            page.data.setdefault("_s_currency", "RUB")
            show_auth()

        page.data["navigate"] = navigate
        page.data["logout"] = logout
        page.data["pages"] = pages

        content.content = ft.Container(
            content=pages[0],
            key="0",
        )
        nav_container.content = build_nav(0)

        inner.content = ft.Column(
            controls=[content, nav_container],
            expand=True,
            spacing=0,
        )
        page.update()

    # ─── СТАРТ ────────────────────────────────────────────────────────────────

    stored_id = page.session.store.get("user_id") if page.session.store.contains_key("user_id") else None
    if stored_id:
        with get_connection() as conn:
            user = conn.execute("SELECT id FROM users WHERE id=?", (stored_id,)).fetchone()
        if user:
            page.data["user_id"] = stored_id
            show_main_app()
            _check_and_add_recurring_income(stored_id)  # AUTO-1: автодобавить зарплату при авто-логине
            _check_and_charge_subscriptions(stored_id)  # AUTO-2: списать подписки с charge_day ≤ сегодня
            page.data["pages"][0].refresh()  # обновить главный экран после авто-операций
            return

    show_auth()


ft.run(main, assets_dir="assets")