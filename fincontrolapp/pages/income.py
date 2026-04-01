import flet as ft
from datetime import date
from components.base_page import BasePage
from components.form_utils import parse_amount, parse_date
from components.dialogs import show_dialog as _show_dialog, close_dialog as _close_dialog


class IncomePage(BasePage):
    def __init__(self, page: ft.Page, ctrl):
        self._ctrl = ctrl
        super().__init__(page, "Доходы")

    def build_body(self):
        period = self._current_period_label()
        salary = self._ctrl.get_salary()
        incomes_all = self._ctrl.get_transactions()
        monthly_incomes = [t for t in incomes_all if self._is_current_month(t['date'])]
        additional = [t for t in monthly_incomes if not t['is_recurring']]
        month_total = sum(t['amount'] for t in monthly_incomes)

        return ft.Column([
            self._salary_card(salary),
            ft.Container(
                bgcolor="#EEF3FF",
                border_radius=10,
                padding=ft.Padding.only(left=10, right=10, top=6, bottom=6),
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CALENDAR_MONTH, size=14, color="#5B6EC7"),
                        ft.Text(f"Период: {period}", size=12, color="#5B6EC7"),
                        ft.Text(f"Сумма: {month_total:,.0f} ₽", size=12, color="#2E7D32"),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ),
            ft.Text("Дополнительные доходы", size=16, weight=ft.FontWeight.W_600, color="#1A1A24"),
            self._income_list(additional),
            ft.ElevatedButton(
                "＋ Добавить доход",
                style=ft.ButtonStyle(bgcolor="#4CAF50", color="#FFFFFF"),
                width=float("inf"),
                on_click=self._open_add_dialog,
            ),
        ], spacing=16)

    def _salary_card(self, salary):
        amount_text = f"{salary['amount']:,.0f} ₽" if salary else "Не указана"
        return ft.Container(
            bgcolor="#1A1A24", border_radius=16, padding=16,
            content=ft.Column([
                ft.Text("Основная зарплата", size=14, color="#888888"),
                ft.Text(amount_text, size=24, weight=ft.FontWeight.BOLD, color="#4CAF50"),
                ft.ElevatedButton(
                    "Указать зарплату" if not salary else "Изменить зарплату",
                    icon=ft.Icons.EDIT,
                    style=ft.ButtonStyle(bgcolor="#6C63FF", color="#FFFFFF"),
                    on_click=self._open_salary_dialog,
                ),
            ], spacing=8),
        )

    def _income_list(self, incomes):
        if not incomes:
            return ft.Container(
                bgcolor="#1A1A24", border_radius=16, padding=16,
                content=ft.Text("Нет записей", color="#888888", size=14),
            )

        rows = []
        for t in incomes:
            rows.append(ft.Container(
                padding=ft.padding.symmetric(vertical=10),
                border=ft.Border(bottom=ft.BorderSide(1, "#2A2A35")),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column([
                            ft.Text(t['category_name'], size=14, color="#FFFFFF",
                                    weight=ft.FontWeight.W_500),
                            ft.Text(t['description'] or t['date'], size=12, color="#888888"),
                        ], spacing=2, expand=True),
                        ft.Row([
                            ft.Text(f"+ {t['amount']:,.0f} ₽", color="#4CAF50",
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
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Удалить доход?"))

        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)

        def on_confirm(e):
            try:
                self._ctrl.delete_transaction(transaction_id)
                self.refresh()
            finally:
                _close_dialog(self.page_ref, dlg)

        dlg.content = ft.Text(f'Доход «{category_name}» будет удалён.')
        dlg.actions = [
            ft.TextButton("Отмена", on_click=on_cancel),
            ft.TextButton("Удалить", style=ft.ButtonStyle(color="#F44336"), on_click=on_confirm),
        ]
        _show_dialog(self.page_ref, dlg)

    def _open_salary_dialog(self, e):
        cats = self._ctrl.get_categories()
        salary_cat = next((c for c in cats if c.name == 'Зарплата'), cats[0] if cats else None)

        amount_field = ft.TextField(label="Сумма зарплаты", keyboard_type=ft.KeyboardType.NUMBER,
                                    border_color="#6C63FF", max_length=10)
        date_field = ft.TextField(label="Дата", value=date.today().strftime("%d.%m.%Y"),
                                  border_color="#6C63FF")

        dlg = ft.AlertDialog(modal=True, title=ft.Text("Указать зарплату"))

        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)

        def on_submit(e):
            amount_field.error = None
            date_field.error = None

            amount = None
            if not amount_field.value:
                amount_field.error = "Введите сумму"
            else:
                try:
                    amount = parse_amount(amount_field.value)
                    if amount <= 0:
                        amount_field.error = "Сумма должна быть больше нуля"
                except ValueError:
                    amount_field.error = "Введите число, например: 50000"

            parsed_date = None
            try:
                parsed_date = parse_date(date_field.value)
            except ValueError:
                date_field.error = "Формат даты: ДД.ММ.ГГГГ"

            if any(f.error for f in (amount_field, date_field)):
                amount_field.update()
                date_field.update()
                return

            existing = self._ctrl.get_salary()
            if existing:
                self._ctrl.update_transaction(existing['id'], amount, str(parsed_date))
            else:
                self._ctrl.add_transaction(
                    amount=amount,
                    category_id=salary_cat.id,
                    description="Зарплата",
                    date=str(parsed_date),
                    is_recurring=1,
                )
            self.rebuild()
            pages = self.page_ref.data.get("pages", {})
            if 0 in pages:
                pages[0].rebuild()
            _close_dialog(self.page_ref, dlg)
            self.page_ref.show_dialog(ft.SnackBar(ft.Text("Зарплата сохранена")))
            self.page_ref.update()

        dlg.content = ft.Column([amount_field, date_field], tight=True, spacing=12)
        dlg.actions = [
            ft.TextButton("Отмена", on_click=on_cancel),
            ft.TextButton("Сохранить", on_click=on_submit),
        ]
        _show_dialog(self.page_ref, dlg)

    def _open_add_dialog(self, e):
        cats = self._ctrl.get_categories()
        category_dd = ft.Dropdown(
            label="Категория", border_color="#6C63FF",
            options=[ft.dropdown.Option(str(c.id), c.name) for c in cats],
        )
        amount_field = ft.TextField(label="Сумма", keyboard_type=ft.KeyboardType.NUMBER,
                                    border_color="#6C63FF", max_length=10)
        desc_field = ft.TextField(label="Описание (необязательно)", border_color="#6C63FF")
        date_field = ft.TextField(label="Дата", value=date.today().strftime("%d.%m.%Y"),
                                  border_color="#6C63FF")

        dlg = ft.AlertDialog(modal=True, title=ft.Text("Добавить доход"))

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
                    amount_field.error = "Введите число, например: 1000"

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

            self._ctrl.add_transaction(
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
            self.page_ref.show_dialog(ft.SnackBar(ft.Text("Доход добавлен")))
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
