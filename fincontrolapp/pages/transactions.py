import flet as ft
import datetime
from datetime import date
from components.base_page import BasePage
from components.dialogs import close_dialog as _close_dialog
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
            ft.GestureDetector(
                on_tap=self._open_add_dialog,
                content=ft.Container(
                    width=float("inf"),
                    height=48,
                    border_radius=12,
                    gradient=ft.RadialGradient(
                        colors=["#ffffff", "#6C63FF"],
                        center=ft.Alignment(0, -0.2),
                        radius=4.0,
                        stops=[0.0, 0.8],
                    ),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text(
                        "＋ Добавить",
                        color=ft.Colors.BLACK,
                        font_family="Montserrat SemiBold",
                        size=16,
                    ),
                ),
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
        page = self.page_ref

        def on_cancel(e):
            _close_dialog(page, dlg)

        def on_confirm(e):
            _close_dialog(page, dlg)
            try:
                self._ctrl.delete_transaction(transaction_id)
                self.refresh()
                self._show_success("Транзакция удалена")
            except Exception:
                self._show_error("Не удалось удалить транзакцию")

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "Удалить транзакцию?",
                color="#000000",
                font_family="Montserrat SemiBold",
                size=24,
            ),
            content=ft.Text(
                f"Операция «{category_name}» будет удалена.",
                color=ft.Colors.with_opacity(0.6, "#000000"),
                font_family="Montserrat Medium",
                size=14,
            ),
            actions=[
                ft.TextButton(
                    "Отмена",
                    on_click=on_cancel,
                    style=ft.ButtonStyle(
                        color="#483EB7",
                        text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=14),
                    ),
                ),
                ft.TextButton(
                    "Удалить",
                    on_click=on_confirm,
                    style=ft.ButtonStyle(
                        color=ft.Colors.with_opacity(0.6, "#FF7E1C"),
                        text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=14),
                    ),
                ),
            ],
        )
        page.overlay.append(dlg)
        page.update()
        page.show_dialog(dlg)

    def _transactions_list(self, transactions):
        if not transactions:
            return ft.Container(
                bgcolor="#1A1A24",
                border_radius=16,
                padding=16,
                content=ft.Text("Операций нет", color="#888888", size=14),
            )

        rows = []
        for t in transactions:
            is_income = t["type"] == "income"

            # Фон корзины — виден при свайпе влево
            delete_bg = ft.Container(
                border_radius=8,
                padding=ft.Padding.only(right=16),
                alignment=ft.Alignment(1, 0),
                bgcolor="#F4433622",
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    controls=[
                        ft.Icon(
                            ft.Icons.DELETE_OUTLINE,
                            color="#F44336",
                            size=22,
                        ),
                        ft.Text(
                            "Удалить",
                            color="#F44336",
                            size=13,
                        ),
                    ],
                    spacing=4,
                ),
                visible=False,
            )

            row_content = ft.Container(
                padding=ft.Padding.symmetric(vertical=10),
                bgcolor="#1A1A24",
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row([
                            ft.Container(
                                width=36,
                                height=36,
                                border_radius=18,
                                bgcolor="#4CAF5022" if is_income else "#F4433622",
                                content=ft.Icon(
                                    CATEGORY_ICONS.get(t["category_name"], ft.Icons.MORE_HORIZ),
                                    color="#4CAF50" if is_income else "#F44336",
                                    size=18,
                                ),
                                alignment=ft.Alignment(0, 0),
                            ),
                            ft.Column([
                                ft.Text(
                                    t["category_name"],
                                    size=14,
                                    color="#FFFFFF",
                                    weight=ft.FontWeight.W_500,
                                ),
                                ft.Text(
                                    t["description"] or t["date"],
                                    size=12,
                                    color="#888888",
                                ),
                            ], spacing=2),
                        ], spacing=12, expand=True),
                        ft.Row([
                            ft.Text(
                                f"{'+ ' if is_income else '− '}{t['amount']:,.0f} ₽",
                                color="#4CAF50" if is_income else "#F44336",
                                size=14,
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.IconButton(
                                ft.Icons.EDIT_OUTLINED,
                                icon_color="#555555",
                                icon_size=18,
                                on_click=lambda e, tr=t: self._open_edit_dialog(tr),
                            ),
                            ft.IconButton(
                                ft.Icons.DELETE,
                                icon_color="#555555",
                                icon_size=18,
                                on_click=lambda e, tid=t["id"], cat=t["category_name"]: (
                                    self._confirm_delete(tid, cat)
                                ),
                            ),
                        ], spacing=0),
                    ],
                ),
            )

            stack = ft.Stack(controls=[delete_bg, row_content])

            # Свайп влево через GestureDetector
            swipe = {"start_x": 0.0, "last_x": 0.0}

            def on_pan_start(e, sw=swipe):
                sw["start_x"] = e.local_position.x
                sw["last_x"] = e.local_position.x

            def on_pan_update(e, cc=row_content, db=delete_bg, sw=swipe):
                sw["last_x"] = e.local_position.x
                delta = e.local_position.x - sw["start_x"]
                if delta < 0:
                    offset_x = max(delta / 300, -0.35)
                    cc.offset = ft.Offset(offset_x, 0)
                    cc.update()
                    if not db.visible:
                        db.visible = True
                        db.update()
                else:
                    cc.offset = ft.Offset(0, 0)
                    cc.update()
                    if db.visible:
                        db.visible = False
                        db.update()

            def on_pan_end(e, cc=row_content, db=delete_bg, sw=swipe, tid=t["id"], cat=t["category_name"]):
                delta = sw["last_x"] - sw["start_x"]
                if delta < -80:
                    self._confirm_delete(tid, cat)
                cc.offset = ft.Offset(0, 0)
                cc.update()
                db.visible = False
                db.update()

            rows.append(
                ft.GestureDetector(
                    on_pan_start=on_pan_start,
                    on_pan_update=on_pan_update,
                    on_pan_end=on_pan_end,
                    content=stack,
                )
            )

        return ft.Container(
            bgcolor="#1A1A24",
            border_radius=16,
            padding=ft.Padding.only(left=16, right=16, top=4, bottom=4),
            content=ft.Column(
                [
                    *rows,
                    # разделитель между строками
                ],
                spacing=0,
            ),
        )

    def _open_add_dialog(self, e):
        error_style = ft.TextStyle(
            font_family="Montserrat Medium",
            size=10,
            color="#FF0000",
        )

        type_field = ft.Dropdown(
            label="Тип",
            border_color="#6C63FF",
            options=[
                ft.dropdown.Option("income", "Доход"),
                ft.dropdown.Option("expense", "Расход"),
            ],
            value="expense",
        )
        category_dd = ft.Dropdown(
            label="Категория",
            border_color="#6C63FF",
            options=[],
            error_style=error_style,
        )
        amount_field = ft.TextField(
            label="Сумма",
            border_color="#6C63FF",
            error_style=error_style,
        )
        desc_field = ft.TextField(
            label="Описание (необязательно)",
            border_color="#6C63FF",
        )
        date_field = ft.TextField(
            label="Дата",
            value=date.today().strftime("%d.%m.%Y"),
            read_only=True,
            border_color="#6C63FF",
            suffix_icon=ft.Icons.CALENDAR_MONTH,
            error_style=error_style,
        )

        def on_date_selected(e):
            import datetime
            date_field.value = (
                e.control.value.strftime("%d.%m.%Y") if e.control.value else date.today().strftime("%d.%m.%Y")
            )
            date_field.update()

        date_picker = ft.DatePicker(
            on_change=on_date_selected,
            first_date=__import__('datetime').datetime(2000, 1, 1),
            last_date=__import__('datetime').datetime(2030, 12, 31),
        )
        self.page.overlay.append(date_picker)

        def open_date_picker(e):
            self.page.dialog = date_picker
            date_picker.open = True
            self.page.update()

        date_field.on_click = open_date_picker

        # Валидация on_change
        def validate_amount(e):
            v = (amount_field.value or "").replace(",", ".")
            if not v:
                amount_field.error = "Введите сумму"
            else:
                try:
                    amount_field.error = (
                        None if parse_amount(amount_field.value) > 0
                        else "Сумма должна быть больше нуля"
                    )
                except ValueError:
                    amount_field.error = "Введите число, например: 500"
            amount_field.update()

        def validate_category(e):
            category_dd.error = None if category_dd.value else "Выберите категорию"
            category_dd.update()

        amount_field.on_change = validate_amount
        category_dd.on_change = validate_category

        def load_categories(type_val):
            try:
                cats = self._ctrl.get_categories(type_=type_val)
            except Exception:
                self._show_error("Не удалось загрузить категории")
                return
            category_dd.options = [ft.dropdown.Option(str(c.id), c.name) for c in cats]
            _other = next((c for c in cats if c.name == "Другое"), None)
            category_dd.value = str(_other.id) if _other else None
            self.page_ref.update()

        type_field.on_change = lambda e: load_categories(type_field.value)
        load_categories("expense")

        bs = ft.BottomSheet(open=False, content=ft.Container())

        def on_cancel(e):
            bs.open = False
            self.page.update()

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

            parsed_date = parse_date(date_field.value)

            if any(f.error for f in (category_dd, amount_field)):
                category_dd.update()
                amount_field.update()
                return

            try:
                self._ctrl.add_transaction(
                    type_=type_field.value,
                    amount=amount,
                    category_id=int(category_dd.value),
                    description=desc_field.value or None,
                    date=str(parsed_date),
                )
            except Exception:
                self._show_error("Не удалось добавить транзакцию", close_bs=bs)
                return
            bs.open = False
            self.page.update()
            self.refresh()
            self._show_success("Транзакция добавлена")

        bs.content = ft.Container(
            padding=ft.Padding.only(left=20, right=20, top=16, bottom=16),
            content=ft.Column(
                tight=True,
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                "Добавить транзакцию",
                                color="#000000",
                                font_family="Montserrat SemiBold",
                                size=24,
                            ),
                        ],
                    ),
                    type_field,
                    category_dd,
                    amount_field,
                    desc_field,
                    date_field,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.END,
                        controls=[
                            ft.TextButton(
                                "Отмена",
                                on_click=on_cancel,
                                style=ft.ButtonStyle(
                                    color="#483EB7",
                                    text_style=ft.TextStyle(
                                        font_family="Montserrat SemiBold", size=14
                                    ),
                                ),
                            ),
                            ft.TextButton(
                                "Добавить",
                                on_click=on_submit,
                                style=ft.ButtonStyle(
                                    color="#483EB7",
                                    text_style=ft.TextStyle(
                                        font_family="Montserrat SemiBold", size=14
                                    ),
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        )

        self.page.overlay.append(bs)
        bs.open = True
        self.page.update()

    def _open_edit_dialog(self, transaction):
        error_style = ft.TextStyle(
            font_family="Montserrat Medium",
            size=10,
            color="#FF0000",
        )

        # Форматируем дату из ISO (YYYY-MM-DD) в DD.MM.YYYY для отображения
        raw_date = transaction["date"]
        try:
            d = datetime.datetime.strptime(raw_date, "%Y-%m-%d").date()
            display_date = d.strftime("%d.%m.%Y")
        except Exception:
            display_date = raw_date

        type_field = ft.Dropdown(
            label="Тип",
            border_color="#6C63FF",
            options=[
                ft.dropdown.Option("income", "Доход"),
                ft.dropdown.Option("expense", "Расход"),
            ],
            value=transaction["type"],
        )
        category_dd = ft.Dropdown(
            label="Категория",
            border_color="#6C63FF",
            options=[],
            error_style=error_style,
        )
        amount_field = ft.TextField(
            label="Сумма",
            value=str(int(transaction["amount"]) if transaction["amount"] == int(transaction["amount"]) else transaction["amount"]),
            border_color="#6C63FF",
            error_style=error_style,
        )
        desc_field = ft.TextField(
            label="Описание (необязательно)",
            value=transaction["description"] or "",
            border_color="#6C63FF",
        )
        date_field = ft.TextField(
            label="Дата",
            value=display_date,
            read_only=True,
            border_color="#6C63FF",
            suffix_icon=ft.Icons.CALENDAR_MONTH,
            error_style=error_style,
        )

        def on_date_selected(e):
            date_field.value = (
                e.control.value.strftime("%d.%m.%Y") if e.control.value else display_date
            )
            date_field.update()

        date_picker = ft.DatePicker(
            on_change=on_date_selected,
            first_date=datetime.datetime(2000, 1, 1),
            last_date=datetime.datetime(2030, 12, 31),
        )
        self.page.overlay.append(date_picker)

        def open_date_picker(e):
            self.page.dialog = date_picker
            date_picker.open = True
            self.page.update()

        date_field.on_click = open_date_picker

        def validate_amount(e):
            v = (amount_field.value or "").replace(",", ".")
            if not v:
                amount_field.error = "Введите сумму"
            else:
                try:
                    amount_field.error = (
                        None if parse_amount(amount_field.value) > 0
                        else "Сумма должна быть больше нуля"
                    )
                except ValueError:
                    amount_field.error = "Введите число, например: 500"
            amount_field.update()

        def validate_category(e):
            category_dd.error = None if category_dd.value else "Выберите категорию"
            category_dd.update()

        amount_field.on_change = validate_amount
        category_dd.on_change = validate_category

        def load_categories(type_val, selected_id=None):
            try:
                cats = self._ctrl.get_categories(type_=type_val)
            except Exception:
                self._show_error("Не удалось загрузить категории")
                return
            category_dd.options = [ft.dropdown.Option(str(c.id), c.name) for c in cats]
            if selected_id and any(str(c.id) == str(selected_id) for c in cats):
                category_dd.value = str(selected_id)
            else:
                _other = next((c for c in cats if c.name == "Другое"), None)
                category_dd.value = str(_other.id) if _other else None
            self.page_ref.update()

        type_field.on_change = lambda e: load_categories(type_field.value)
        load_categories(transaction["type"], transaction["category_id"])

        bs = ft.BottomSheet(open=False, content=ft.Container())

        def on_cancel(e):
            bs.open = False
            self.page.update()

        def on_submit(e):
            category_dd.error = None
            amount_field.error = None

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

            parsed_date = parse_date(date_field.value)

            if any(f.error for f in (category_dd, amount_field)):
                category_dd.update()
                amount_field.update()
                return

            try:
                self._ctrl.update_transaction(
                    transaction_id=transaction["id"],
                    type_=type_field.value,
                    amount=amount,
                    category_id=int(category_dd.value),
                    description=desc_field.value or None,
                    date=str(parsed_date),
                )
            except Exception:
                self._show_error("Не удалось сохранить транзакцию", close_bs=bs)
                return
            bs.open = False
            self.page.update()
            self.refresh()
            self._show_success("Транзакция сохранена")

        bs.content = ft.Container(
            padding=ft.Padding.only(left=20, right=20, top=16, bottom=16),
            content=ft.Column(
                tight=True,
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                "Редактировать транзакцию",
                                color="#000000",
                                font_family="Montserrat SemiBold",
                                size=24,
                            ),
                        ],
                    ),
                    type_field,
                    category_dd,
                    amount_field,
                    desc_field,
                    date_field,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.END,
                        controls=[
                            ft.TextButton(
                                "Отмена",
                                on_click=on_cancel,
                                style=ft.ButtonStyle(
                                    color="#483EB7",
                                    text_style=ft.TextStyle(
                                        font_family="Montserrat SemiBold", size=14
                                    ),
                                ),
                            ),
                            ft.TextButton(
                                "Сохранить",
                                on_click=on_submit,
                                style=ft.ButtonStyle(
                                    color="#483EB7",
                                    text_style=ft.TextStyle(
                                        font_family="Montserrat SemiBold", size=14
                                    ),
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        )

        self.page.overlay.append(bs)
        bs.open = True
        self.page.update()