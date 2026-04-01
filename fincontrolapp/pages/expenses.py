import flet as ft
from datetime import date
from database import get_connection
from components.form_utils import parse_amount, parse_date
from components.dialogs import show_dialog as _show_dialog, close_dialog as _close_dialog
from components.base_page import BasePage
from modules.categories.repository import CategoryRepository
from modules.categories.service import CategoryService
from modules.transactions.repository import TransactionRepository
from modules.transactions.service import TransactionService


CATEGORY_ICONS = {
    "Еда": (ft.Icons.RESTAURANT, "#FF9800"),
    "Транспорт": (ft.Icons.DIRECTIONS_CAR, "#2196F3"),
    "Здоровье": (ft.Icons.LOCAL_HOSPITAL, "#F44336"),
    "Покупки": (ft.Icons.SHOPPING_BAG, "#9C27B0"),
    "Развлечения": (ft.Icons.SPORTS_ESPORTS, "#00BCD4"),
    "Жильё": (ft.Icons.HOME, "#795548"),
    "Образование": (ft.Icons.SCHOOL, "#4CAF50"),
    "Другое": (ft.Icons.MORE_HORIZ, "#607D8B"),
}


class ExpensesPage(BasePage):
    def __init__(self, page: ft.Page):
        self._selected_category_id = None
        self._selected_category_name = None
        super().__init__(page, "Расходы")

    def build_body(self):
        with get_connection() as con:
            repo = CategoryRepository(con)
            service = CategoryService(repo)
            categories = service.get_all(type_='expense')
        # categories = get_categories(type_='expense')
        with get_connection() as con:
            repo = TransactionRepository(con)
            service = TransactionService(repo)
            expenses_all = service.get_transactions(
                self._user_id, type_='expense',
                category_id=self._selected_category_id,
            )
        expenses = [t for t in expenses_all if self._is_current_month(t['date'])]
        period = self._current_period_label()
        month_total = sum(t['amount'] for t in expenses)
        title = (
            f"История: {self._selected_category_name}"
            if self._selected_category_name
            else "История расходов"
        )

        return ft.Column([
            ft.Text("Категории", size=16, weight=ft.FontWeight.W_600, color="#1A1A24"),
            ft.GridView(
                runs_count=4, max_extent=90,
                spacing=10, run_spacing=10, height=200,
                controls=[self._category_card(c) for c in categories],
            ),
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(title, size=16, weight=ft.FontWeight.W_600, color="#1A1A24"),
                    ft.TextButton("Все", on_click=lambda e: self._clear_filter())
                    if self._selected_category_id else ft.Container(),
                ],
            ),
            ft.Container(
                bgcolor="#FFF3E0",
                border_radius=10,
                padding=ft.Padding.only(left=10, right=10, top=6, bottom=6),
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CALENDAR_MONTH, size=14, color="#EF6C00"),
                        ft.Text(f"Период: {period}", size=12, color="#EF6C00"),
                        ft.Text(f"Сумма: {month_total:,.0f} ₽", size=12, color="#C62828"),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ),
            self._expense_list(expenses),
            ft.ElevatedButton(
                "＋ Добавить расход",
                style=ft.ButtonStyle(bgcolor="#F44336", color="#FFFFFF"),
                width=float("inf"),
                on_click=self._open_add_dialog,
            ),
        ], spacing=16)

    def _category_card(self, category):
        icon, color = CATEGORY_ICONS.get(category.name, (ft.Icons.MORE_HORIZ, "#607D8B"))
        active = self._selected_category_id == category.id
        return ft.Container(
            bgcolor="#6C63FF" if active else "#1A1A24",
            border_radius=12, padding=8, ink=True,
            on_click=lambda e, c=category: self._set_filter(c.id, c.name),
            content=ft.Column([
                ft.Icon(icon, color=color, size=28),
                ft.Text(category.name, size=11, color="#CCCCCC",
                        text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
        )

    def _set_filter(self, category_id, category_name):
        self._selected_category_id = category_id
        self._selected_category_name = category_name
        self.refresh()

    def _clear_filter(self):
        self._selected_category_id = None
        self._selected_category_name = None
        self.refresh()

    def _expense_list(self, expenses):
        if not expenses:
            return ft.Container(
                bgcolor="#1A1A24", border_radius=16, padding=16,
                content=ft.Text("Нет записей", color="#888888", size=14),
            )

        rows = []
        for t in expenses:
            icon, color = CATEGORY_ICONS.get(t['category_name'], (ft.Icons.MORE_HORIZ, "#607D8B"))
            rows.append(ft.Container(
                padding=ft.padding.symmetric(vertical=10),
                border=ft.Border(bottom=ft.BorderSide(1, "#2A2A35")),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row([
                            ft.Container(
                                width=36, height=36, border_radius=18,
                                bgcolor=color + "22",
                                content=ft.Icon(icon, color=color, size=18),
                                alignment=ft.Alignment(0, 0),
                            ),
                            ft.Column([
                                ft.Text(t['category_name'], size=14, color="#FFFFFF",
                                        weight=ft.FontWeight.W_500),
                                ft.Text(t['description'] or t['date'], size=12, color="#888888"),
                            ], spacing=2),
                        ], spacing=12, expand=True),
                        ft.Row([
                            ft.Text(f"− {t['amount']:,.0f} ₽", color="#F44336",
                                    size=14, weight=ft.FontWeight.W_600),
                            ft.IconButton(
                                ft.Icons.DELETE_OUTLINE,
                                icon_color="#555555",
                                icon_size=18,
                                on_click=lambda e, tid=t['id'], cat=t['category_name']: (
                                    self._confirm_delete(tid, cat)
                                ),
                            ),
                        ], spacing=0),
                    ],
                ),
            ))

        return ft.Container(
            bgcolor="#1A1A24", border_radius=16,
            padding=ft.Padding.only(left=16, right=16, top=4, bottom=4),
            content=ft.Column(rows, spacing=0),
        )

    def _confirm_delete(self, transaction_id, category_name):
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Удалить расход?"))

        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)

        def on_confirm(e):
            try:
                with get_connection() as con:
                    repo = TransactionRepository(con)
                    service = TransactionService(repo)
                    service.delete_transaction(transaction_id)
                self.refresh()                
            finally:
                _close_dialog(self.page_ref, dlg)

        dlg.content = ft.Text(f'Расход «{category_name}» будет удалён.')
        dlg.actions = [
            ft.TextButton("Отмена", on_click=on_cancel),
            ft.TextButton("Удалить", style=ft.ButtonStyle(color="#F44336"), on_click=on_confirm),
        ]
        _show_dialog(self.page_ref, dlg)

    def _open_add_dialog(self, e):
        with get_connection() as con:
            repo = CategoryRepository(con)
            service = CategoryService(repo)
            cats = service.get_all(type_='expense')
        # cats = get_categories(type_='expense')
        category_dd = ft.Dropdown(
            label="Категория", border_color="#6C63FF",
            options=[ft.dropdown.Option(str(c.id), c.name) for c in cats],
            value=str(self._selected_category_id) if self._selected_category_id else None,
        )
        amount_field = ft.TextField(label="Сумма", keyboard_type=ft.KeyboardType.NUMBER,
                                    border_color="#6C63FF", max_length=10)
        desc_field = ft.TextField(label="Описание (необязательно)", border_color="#6C63FF")
        date_field = ft.TextField(label="Дата", value=date.today().strftime("%d.%m.%Y"), border_color="#6C63FF")

        dlg = ft.AlertDialog(modal=True, title=ft.Text("Добавить расход"))

        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)

        def on_submit(e):
            category_dd.error = None
            amount_field.error = None
            date_field.error = None

            if not category_dd.value:
                category_dd.error = "Выберите категорию"

            amount = None
            if not amount_field.value:
                amount_field.error = "Введите сумму"
            else:
                try:
                    amount = parse_amount(amount_field.value)
                    if amount <= 0:
                        amount_field.error = "Сумма должна быть больше нуля"
                except ValueError:
                    amount_field.error = "Введите целое число"

            parsed_date = None
            try:
                parsed_date = parse_date(date_field.value)
            except ValueError:
                date_field.error = "Формат даты: ДД.ММ.ГГГГ"

            if any(f.error for f in (category_dd, amount_field, date_field)):
                category_dd.update()
                amount_field.update()
                date_field.update()
                return

            with get_connection() as con:
                repo = TransactionRepository(con)
                service = TransactionService(repo)
                service.add_transaction(
                    user_id=self._user_id,
                    type_='expense',
                    amount=amount,
                    category_id=int(category_dd.value),
                    description=desc_field.value or None,
                    date=str(parsed_date),
                )
            self.rebuild()
            pages = self.page_ref.data.get("pages", {})
            if 0 in pages:
                pages[0].rebuild()
            _close_dialog(self.page_ref, dlg)
            self.page_ref.show_dialog(ft.SnackBar(ft.Text("Расход добавлен")))
            self.page_ref.update()
        dlg.content = ft.Column(
            [category_dd, amount_field, desc_field, date_field],
            tight=True, spacing=12,
        )
        dlg.actions = [
            ft.TextButton("Отмена", on_click=on_cancel),
            ft.TextButton("Добавить", on_click=on_submit),
        ]
        _show_dialog(self.page_ref, dlg)