import flet as ft
from datetime import date
from components.base_page import BasePage
from components.dialogs import show_dialog as _show_dialog, close_dialog as _close_dialog

MONTH_SHORT = ["янв", "фев", "мар", "апр", "май", "июн",
               "июл", "авг", "сен", "окт", "ноя", "дек"]

class SubscriptionsPage(BasePage):
    def __init__(self, page: ft.Page, ctrl):
        self._ctrl = ctrl
        super().__init__(page, "Подписки")

    def build_body(self):
        subscriptions = self._ctrl.get_subscriptions()
        monthly_total = self._ctrl.get_monthly_total()

        return ft.Column([
            ft.Container(
                bgcolor="#1A1A24", border_radius=16, padding=16,
                content=ft.Column([
                    ft.Text("Сумма подписок в месяц", size=14, color="#888888"),
                    ft.Text(f"{monthly_total:,.0f} ₽", size=28,
                            weight=ft.FontWeight.BOLD, color="#FF9800"),
                ], spacing=4),
            ),
            self._subscriptions_list(subscriptions),
            ft.ElevatedButton(
                "＋ Добавить подписку",
                style=ft.ButtonStyle(bgcolor="#FF9800", color="#FFFFFF"),
                width=float("inf"),
                on_click=self._open_add_dialog,
            ),
        ], spacing=16)

    def _subscriptions_list(self, subscriptions):
        if not subscriptions:
            return ft.Container(
                bgcolor="#1A1A24", border_radius=16, padding=16,
                content=ft.Text("Подписок нет", color="#888888", size=14),
            )

        rows = []
        for s in subscriptions:
            period_label = "в месяц" if s['period'] == 'monthly' else "в год"
            next_date = self._ctrl.calc_next_charge_date(s['charge_day'], s['period'], s['start_date'])
            next_label = f"{next_date.day} {MONTH_SHORT[next_date.month - 1]}."

            rows.append(ft.Container(
                padding=ft.padding.symmetric(vertical=12),
                border=ft.Border(bottom=ft.BorderSide(1, "#2A2A35")),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column([
                            ft.Text(s['name'], size=14, color="#FFFFFF",
                                    weight=ft.FontWeight.W_500),
                            ft.Text(f"Следующее: {next_label}",
                                    size=12, color="#888888"),
                        ], spacing=2, expand=True),
                        ft.Row([
                            ft.Column([
                                ft.Text(f"{s['amount']:,.0f} ₽", color="#FF9800",
                                        size=14, weight=ft.FontWeight.W_600,
                                        text_align=ft.TextAlign.RIGHT),
                                ft.Text(period_label, size=11, color="#888888",
                                        text_align=ft.TextAlign.RIGHT),
                            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
                            ft.IconButton(
                                ft.Icons.DELETE_OUTLINE,
                                icon_color="#555555", icon_size=18,
                                on_click=lambda e, sid=s['id'], sname=s['name']: (
                                    self._confirm_delete(sid, sname)
                                ),
                            ),
                        ], spacing=4),
                    ],
                ),
            ))

        return ft.Container(
            bgcolor="#1A1A24", border_radius=16,
            padding=ft.Padding.only(left=16, right=16, top=4, bottom=4),
            content=ft.Column(rows, spacing=0),
        )

    def _confirm_delete(self, subscription_id, subscription_name):
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Удалить подписку?"))

        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)

        def on_confirm(e):
            try:
                self._ctrl.delete_subscription(subscription_id)
                self.refresh()
            finally:
                _close_dialog(self.page_ref, dlg)

        dlg.content = ft.Text(f'Подписка «{subscription_name}» будет удалена.')
        dlg.actions = [
            ft.TextButton("Отмена", on_click=on_cancel),
            ft.TextButton("Удалить", style=ft.ButtonStyle(color="#F44336"), on_click=on_confirm),
        ]
        _show_dialog(self.page_ref, dlg)

    def _open_add_dialog(self, e):
        name_field = ft.TextField(label="Название", border_color="#6C63FF")
        amount_field = ft.TextField(label="Сумма", keyboard_type=ft.KeyboardType.NUMBER,
                                    border_color="#6C63FF")
        start_field = ft.TextField(label="Дата начала", value=str(date.today()),
                                   hint_text="ГГГГ-ММ-ДД", border_color="#6C63FF")
        day_field = ft.TextField(label="День списания (1–31)",
                                 keyboard_type=ft.KeyboardType.NUMBER, border_color="#6C63FF")
        period_dd = ft.Dropdown(
            label="Период", border_color="#6C63FF",
            options=[
                ft.dropdown.Option("monthly", "Ежемесячно"),
                ft.dropdown.Option("yearly", "Ежегодно"),
            ],
            value="monthly",
        )

        dlg = ft.AlertDialog(modal=True, title=ft.Text("Добавить подписку"))

        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)

        def on_submit(e):
            # сброс ошибок
            name_field.error = None
            amount_field.error = None
            day_field.error = None
            start_field.error = None

            # 1. Название — не пустое и не только пробелы
            name = name_field.value.strip() if name_field.value else ""
            if not name:
                name_field.error = "Введите название"

            # 2. Сумма — число и больше нуля
            amount = None
            if not amount_field.value:
                amount_field.error = "Введите сумму"
            else:
                try:
                    amount = float(amount_field.value.replace(",", "."))
                    if amount <= 0:
                        amount_field.error = "Сумма должна быть больше нуля"
                except ValueError:
                    amount_field.error = "Введите число, например: 299.99"

            # 3. День списания — целое число от 1 до 31
            charge_day = None
            if not day_field.value:
                day_field.error = "Введите день списания"
            else:
                try:
                    charge_day = int(day_field.value)
                    if not 1 <= charge_day <= 31:
                        day_field.error = "День должен быть от 1 до 31"
                except ValueError:
                    day_field.error = "Введите целое число"

            # 4. Дата начала — формат ГГГГ-ММ-ДД
            start_date = start_field.value or str(date.today())
            try:
                date.fromisoformat(start_date)
            except ValueError:
                start_field.error = "Формат даты: ГГГГ-ММ-ДД"

            # если есть хоть одна ошибка — показываем и не сохраняем
            if any(f.error for f in (name_field, amount_field, day_field, start_field)):
                name_field.update()
                amount_field.update()
                day_field.update()
                start_field.update()
                return

            self._ctrl.add_subscription(
                name=name,
                amount=amount,
                charge_day=charge_day,
                period=period_dd.value,
                start_date=start_date,
            )
            _close_dialog(self.page_ref, dlg)
            self.refresh()
            self.page_ref.snack_bar = ft.SnackBar(ft.Text("Подписка добавлена"), open=True)
            self.page_ref.update()

        dlg.content = ft.Column(
            [name_field, amount_field, start_field, day_field, period_dd],
            tight=True, spacing=12,
        )
        dlg.actions = [
            ft.TextButton("Отмена", on_click=on_cancel),
            ft.TextButton("Добавить", on_click=on_submit),
        ]
        _show_dialog(self.page_ref, dlg)
