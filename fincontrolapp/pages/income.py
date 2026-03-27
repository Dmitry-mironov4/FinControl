import flet as ft
from datetime import date, datetime
from components.base_page import BasePage
from components.dialogs import show_dialog as _show_dialog, close_dialog as _close_dialog
from db_queries import get_transactions, add_transaction, delete_transaction, get_categories, update_transaction


MONTH_NAMES = [
    "январь", "февраль", "март", "апрель", "май", "июнь",
    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
]

class IncomePage(BasePage):
    def __init__(self, page: ft.Page):
        super().__init__(page, "Доходы")

    def build_body(self):
        period = self._current_period_label()
        salary = self._get_salary()
        incomes = get_transactions(self._user_id, type_='income')
        monthly_incomes = [t for t in incomes if self._is_current_month(t['date'])]
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

    def _is_current_month(self, value):
        if not value:
            return False
        dt = str(value)
        month_key = date.today().strftime("%Y-%m")
        return dt.startswith(month_key)

    def _current_period_label(self):
        today = date.today()
        return f"{MONTH_NAMES[today.month - 1]} {today.year}"

    def _get_salary(self):
        salaries = get_transactions(self._user_id, type_='income')
        recurring = [t for t in salaries if t['is_recurring']]
        return recurring[0] if recurring else None

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
                delete_transaction(transaction_id)
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
        amount_field = ft.TextField(label="Сумма зарплаты", keyboard_type=ft.KeyboardType.NUMBER,
                                    border_color="#6C63FF", max_length=10)
        date_field = ft.TextField(label="Дата", value=str(date.today().strftime("%d.%m.%Y")), border_color="#6C63FF")
        cats = get_categories(type_='income')
        salary_cat = next((c for c in cats if c['name'] == 'Зарплата'), cats[0] if cats else None)

        dlg = ft.AlertDialog(modal=True, title=ft.Text("Указать зарплату"))

        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)

        def on_submit(e):
            if not amount_field.value or not salary_cat:
                return
            try:
                amount = float(amount_field.value.replace(",", "."))
            except ValueError:
                self.page_ref.show_dialog(ft.SnackBar(ft.Text("Введите корректную сумму")))
                return              
            try:
                parsed_date = datetime.strptime(date_field.value, "%d.%m.%Y").date()
            except ValueError:
                self.page_ref.show_dialog(ft.SnackBar(ft.Text("Введите корректную дату в формате ДД.ММ.ГГГГ")))
                return 
            existing = self._get_salary()
            if existing:
                update_transaction(existing['id'], amount, str(parsed_date))
            else:
                add_transaction(
                    user_id=self._user_id,
                    type_='income',
                    amount=amount,
                    category_id=salary_cat['id'],
                    description="Зарплата",
                    date=str(parsed_date),
                    is_recurring=1,
                )
            # refresh + snackbar — одинаково для обоих случаев
            self.refresh()
            pages = self.page_ref.data.get("pages", {})
            if 0 in pages:
                pages[0].refresh()
            _close_dialog(self.page_ref, dlg)
            self.page_ref.show_dialog(ft.SnackBar(ft.Text("Зарплата сохранена")))

        dlg.content = ft.Column([amount_field, date_field], tight=True, spacing=12)
        dlg.actions = [
            ft.TextButton("Отмена", on_click=on_cancel),
            ft.TextButton("Сохранить", on_click=on_submit),
        ]
        _show_dialog(self.page_ref, dlg)

    def _open_add_dialog(self, e):
        cats = get_categories(type_='income')
        category_dd = ft.Dropdown(
            label="Категория", border_color="#6C63FF",
            options=[ft.dropdown.Option(str(c['id']), c['name']) for c in cats],
        )
        amount_field = ft.TextField(label="Сумма", keyboard_type=ft.KeyboardType.NUMBER,
                                    border_color="#6C63FF", max_length=10)
        desc_field = ft.TextField(label="Описание (необязательно)", border_color="#6C63FF")
        date_field = ft.TextField(label="Дата", value=str(date.today().strftime("%d.%m.%Y")), border_color="#6C63FF")

        dlg = ft.AlertDialog(modal=True, title=ft.Text("Добавить доход"))

        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)

        def on_submit(e):
            if not amount_field.value or not category_dd.value:
                return
            try:
                amount = float(amount_field.value.replace(",", "."))
            except ValueError:
                self.page_ref.show_dialog(ft.SnackBar(ft.Text("Введите корректную сумму")))

                return
            
            try:
                parsed_date = datetime.strptime(date_field.value, "%d.%m.%Y").date()
            except ValueError:
                self.page_ref.show_dialog(ft.SnackBar(ft.Text("Введите корректную дату в формате ДД.ММ.ГГГГ"))) 
                return
            add_transaction(
                user_id=self._user_id,
                type_='income',
                amount=amount,
                category_id=int(category_dd.value),
                description=desc_field.value or None,
                date=str(parsed_date),
            )
            self.refresh()
            pages = self.page_ref.data.get("pages", {})
            if 0 in pages:
                pages[0].refresh()
            self.page_ref.show_dialog(ft.SnackBar(ft.Text("Доход добавлен")))   
            _close_dialog(self.page_ref, dlg)

        dlg.content = ft.Column(
            [category_dd, amount_field, desc_field, date_field],
            tight=True, spacing=12,
        )
        dlg.actions = [
            ft.TextButton("Отмена", on_click=on_cancel),
            ft.TextButton("Добавить", on_click=on_submit),
        ]
        _show_dialog(self.page_ref, dlg)