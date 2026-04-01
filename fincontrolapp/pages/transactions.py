import flet as ft
from datetime import date
from components.base_page import BasePage
from components.dialogs import show_dialog as _show_dialog, close_dialog as _close_dialog
from components.form_utils import parse_amount, parse_date


CATEGORY_ICONS = {
    "Еда": ft.Icons.RESTAURANT,
    "Транспорт": ft.Icons.DIRECTIONS_CAR,
    "Здоровье": ft.Icons.LOCAL_HOSPITAL,
    "Покупки": ft.Icons.SHOPPING_BAG,
    "Развлечения": ft.Icons.SPORTS_ESPORTS,
    "Жильё": ft.Icons.HOME,
    "Образование": ft.Icons.SCHOOL,
    "Зарплата": ft.Icons.WORK,
    "Фриланс": ft.Icons.LAPTOP,
    "Другое": ft.Icons.MORE_HORIZ,
}


class TransactionsPage(BasePage):
    def __init__(self, page: ft.Page, ctrl):
        self._ctrl = ctrl
        self._filter = None
        super().__init__(page, "Транзакции")

    def build_body(self):
        transactions = self._ctrl.get_transactions(type_=self._filter)
        return ft.Column([
            ft.Row([
                self._filter_btn("Все", None),
                self._filter_btn("Доходы", "income"),
                self._filter_btn("Расходы", "expense"),
            ], spacing=8),
            self._transactions_list(transactions),
            ft.ElevatedButton(
                "＋ Добавить",
                style=ft.ButtonStyle(bgcolor="#6C63FF", color="#FFFFFF"),
                width=float("inf"),
                on_click=self._open_add_dialog,
            ),
        ], spacing=16)

    def _filter_btn(self, label, value):
        active = self._filter == value
        return ft.ElevatedButton(
            label,
            style=ft.ButtonStyle(
                bgcolor="#6C63FF" if active else "#1A1A24",
                color="#FFFFFF",
            ),
            on_click=lambda e, v=value: self._set_filter(v),
        )

    def _set_filter(self, value):
        self._filter = value
        self.refresh()

    def _confirm_delete(self, transaction_id, category_name):
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Удалить транзакцию?"))

        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)

        def on_confirm(e):
            try:
                self._ctrl.delete_transaction(transaction_id)
                self.refresh()
            finally:
                _close_dialog(self.page_ref, dlg)

        dlg.content = ft.Text(f'Операция «{category_name}» будет удалена.')
        dlg.actions = [
            ft.TextButton("Отмена", on_click=on_cancel),
            ft.TextButton("Удалить", style=ft.ButtonStyle(color="#F44336"), on_click=on_confirm),
        ]
        _show_dialog(self.page_ref, dlg)

    def _transactions_list(self, transactions):
        if not transactions:
            return ft.Container(
                bgcolor="#1A1A24", border_radius=16, padding=16,
                content=ft.Text("Операций нет", color="#888888", size=14),
            )

        rows = []
        for t in transactions:
            is_income = t['type'] == 'income'
            rows.append(ft.Container(
                padding=ft.padding.symmetric(vertical=10),
                border=ft.Border(bottom=ft.BorderSide(1, "#2A2A35")),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row([
                            ft.Container(
                                width=36, height=36, border_radius=18,
                                bgcolor="#4CAF5022" if is_income else "#F4433622",
                                content=ft.Icon(
                                    CATEGORY_ICONS.get(t['category_name'], ft.Icons.MORE_HORIZ),
                                    color="#4CAF50" if is_income else "#F44336",
                                    size=18,
                                ),
                                alignment=ft.Alignment(0, 0),
                            ),
                            ft.Column([
                                ft.Text(t['category_name'], size=14, color="#FFFFFF",
                                        weight=ft.FontWeight.W_500),
                                ft.Text(t['description'] or t['date'], size=12, color="#888888"),
                            ], spacing=2),
                        ], spacing=12, expand=True),
                        ft.Row([
                            ft.Text(
                                f"{'+ ' if is_income else '− '}{t['amount']:,.0f} ₽",
                                color="#4CAF50" if is_income else "#F44336",
                                size=14, weight=ft.FontWeight.W_600,
                            ),
                            ft.IconButton(
                                ft.Icons.DELETE,
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

    def _open_add_dialog(self, e):
        type_field = ft.Dropdown(
            label="Тип", border_color="#6C63FF",
            options=[
                ft.dropdown.Option("income", "Доход"),
                ft.dropdown.Option("expense", "Расход"),
            ],
            value="expense",
        )
        category_dd = ft.Dropdown(label="Категория", border_color="#6C63FF", options=[])
        amount_field = ft.TextField(label="Сумма", keyboard_type=ft.KeyboardType.NUMBER,
                                    border_color="#6C63FF")
        desc_field = ft.TextField(label="Описание (необязательно)", border_color="#6C63FF")
        date_field = ft.TextField(label="Дата", value=date.today().strftime("%d.%m.%Y"),
                                  border_color="#6C63FF")

        dlg = ft.AlertDialog(modal=True, title=ft.Text("Добавить транзакцию"))

        def load_categories(type_val):
            cats = self._ctrl.get_categories(type_=type_val)
            category_dd.options = [ft.dropdown.Option(str(c.id), c.name) for c in cats]
            category_dd.value = None
            self.page_ref.update()

        type_field.on_change = lambda e: load_categories(type_field.value)
        load_categories("expense")

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
                    amount_field.error = "Введите число, например: 500"

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
                type_=type_field.value,
                amount=amount,
                category_id=int(category_dd.value),
                description=desc_field.value or None,
                date=str(parsed_date),
            )
            _close_dialog(self.page_ref, dlg)
            self.refresh()

        dlg.content = ft.Column(
            [type_field, category_dd, amount_field, desc_field, date_field],
            tight=True, spacing=12,
        )
        dlg.actions = [
            ft.TextButton("Отмена", on_click=on_cancel),
            ft.TextButton("Добавить", on_click=on_submit),
        ]
        _show_dialog(self.page_ref, dlg)
