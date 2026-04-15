import flet as ft
import datetime
from datetime import date
from components.base_page import BasePage
from components.dialogs import close_dialog as _close_dialog
from components.form_utils import parse_amount, parse_date


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
    def __init__(self, page: ft.Page, ctrl):
        self._ctrl = ctrl
        self._selected_category_id = None
        self._selected_category_name = None
        super().__init__(page, "Расходы")

    def build_body(self):
        categories = self._ctrl.get_categories()
        expenses_all = self._ctrl.get_transactions(
            category_id=self._selected_category_id
        )
        expenses = [t for t in expenses_all if self._is_current_month(t["date"])]
        period = self._current_period_label()
        month_total = sum(t["amount"] for t in expenses)
        title = (
            f"История: {self._selected_category_name}"
            if self._selected_category_name
            else "История расходов"
        )

        return ft.Column([
            ft.Text("Категории", size=16,
                    weight=ft.FontWeight.W_600, color="#1A1A24"),
            ft.GridView(
                runs_count=4, max_extent=90,
                spacing=10, run_spacing=10, height=200,
                controls=[self._category_card(c) for c in categories],
            ),
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(title, size=16,
                            weight=ft.FontWeight.W_600, color="#1A1A24"),
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
            ft.GestureDetector(
                on_tap=self._open_add_dialog,
                content=ft.Container(
                    width=float("inf"),
                    height=48,
                    border_radius=12,
                    gradient=ft.RadialGradient(
                        colors=["#ffffff", "#F44336"],
                        center=ft.Alignment(0, -0.2),
                        radius=4.0,
                        stops=[0.0, 0.8],
                    ),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text(
                        "＋ Добавить расход",
                        color=ft.Colors.BLACK,
                        font_family="Montserrat SemiBold",
                        size=16,
                    ),
                ),
            ),
        ], spacing=16)

    def _category_card(self, category):
        icon, color = CATEGORY_ICONS.get(
            category.name, (ft.Icons.MORE_HORIZ, "#607D8B")
        )
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
            icon, color = CATEGORY_ICONS.get(
                t["category_name"], (ft.Icons.MORE_HORIZ, "#607D8B")
            )

            delete_bg = ft.Container(
                border_radius=8,
                padding=ft.Padding.only(right=16),
                alignment=ft.Alignment(1, 0),
                bgcolor="#F4433622",
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    controls=[
                        ft.Icon(ft.Icons.DELETE_OUTLINE, color="#F44336", size=22),
                        ft.Text("Удалить", color="#F44336", size=13),
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
                                width=36, height=36, border_radius=18,
                                bgcolor=color + "22",
                                content=ft.Icon(icon, color=color, size=18),
                                alignment=ft.Alignment(0, 0),
                            ),
                            ft.Column([
                                ft.Text(t["category_name"], size=14, color="#FFFFFF",
                                        weight=ft.FontWeight.W_500),
                                ft.Text(t["description"] or t["date"],
                                        size=12, color="#888888"),
                            ], spacing=2),
                        ], spacing=12, expand=True),
                        ft.Row([
                            ft.Text(
                                f"− {t['amount']:,.0f} ₽",
                                color="#F44336", size=14,
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.IconButton(
                                ft.Icons.EDIT_OUTLINED,
                                icon_color="#555555",
                                icon_size=18,
                                on_click=lambda e, tr=t: self._open_edit_dialog(tr),
                            ),
                            ft.IconButton(
                                ft.Icons.DELETE_OUTLINE,
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

            def on_pan_end(e, cc=row_content, db=delete_bg, sw=swipe,
                           tid=t["id"], cat=t["category_name"]):
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
            bgcolor="#1A1A24", border_radius=16,
            padding=ft.Padding.only(left=16, right=16, top=4, bottom=4),
            content=ft.Column(rows, spacing=0),
        )

    def _confirm_delete(self, transaction_id, category_name):
        page = self.page_ref

        def on_cancel(e):
            _close_dialog(page, dlg)

        def on_confirm(e):
            _close_dialog(page, dlg)
            try:
                self._ctrl.delete_transaction(transaction_id)
                self.refresh()
            except Exception as ex:
                print("delete error:", ex)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "Удалить расход?",
                color="#000000",
                font_family="Montserrat SemiBold",
                size=24,
            ),
            content=ft.Text(
                f"Расход «{category_name}» будет удалён.",
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
                        text_style=ft.TextStyle(
                            font_family="Montserrat SemiBold", size=14),
                    ),
                ),
                ft.TextButton(
                    "Удалить",
                    on_click=on_confirm,
                    style=ft.ButtonStyle(
                        color=ft.Colors.with_opacity(0.6, "#FF7E1C"),
                        text_style=ft.TextStyle(
                            font_family="Montserrat SemiBold", size=14),
                    ),
                ),
            ],
        )
        page.overlay.append(dlg)
        page.update()
        page.show_dialog(dlg)

    def _open_add_dialog(self, e):
        cats = self._ctrl.get_categories()

        error_style = ft.TextStyle(
            font_family="Montserrat Medium", size=10, color="#FF0000"
        )

        _other = next((c for c in cats if c.name == "Другое"), None)
        category_dd = ft.Dropdown(
            label="Категория",
            border_color="#6C63FF",
            options=[ft.dropdown.Option(str(c.id), c.name) for c in cats],
            value=str(self._selected_category_id) if self._selected_category_id else (str(_other.id) if _other else None),
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

        # DatePicker
        date_field = ft.TextField(
            label="Дата",
            value=date.today().strftime("%d.%m.%Y"),
            read_only=True,
            border_color="#6C63FF",
            suffix_icon=ft.Icons.CALENDAR_MONTH,
        )

        def on_date_selected(e):
            date_field.value = (
                e.control.value.strftime("%d.%m.%Y")
                if e.control.value
                else date.today().strftime("%d.%m.%Y")
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

        # Валидация on_change
        def validate_category(e):
            category_dd.error = None if category_dd.value else "Выберите категорию"
            category_dd.update()

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

        category_dd.on_change = validate_category
        amount_field.on_change = validate_amount

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

            if any(f.error for f in (category_dd, amount_field)):
                category_dd.update()
                amount_field.update()
                return

            parsed_date = parse_date(date_field.value)

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
            bs.open = False
            self.page.update()
            self.page_ref.snack_bar = ft.SnackBar(ft.Text("Расход добавлен"), open=True)
            self.page_ref.update()

        bs.content = ft.Container(
            padding=ft.Padding.only(left=20, right=20, top=24, bottom=32),
            content=ft.Column(
                tight=True,
                spacing=16,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                "Добавить расход",
                                color="#000000",
                                font_family="Montserrat SemiBold",
                                size=24,
                            ),
                        ],
                    ),
                    category_dd,
                    amount_field,
                    desc_field,
                    date_field,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.END,
                        controls=[
                            ft.TextButton(
                                "Отмена", on_click=on_cancel,
                                style=ft.ButtonStyle(
                                    color="#483EB7",
                                    text_style=ft.TextStyle(
                                        font_family="Montserrat SemiBold", size=14),
                                ),
                            ),
                            ft.TextButton(
                                "Добавить", on_click=on_submit,
                                style=ft.ButtonStyle(
                                    color="#483EB7",
                                    text_style=ft.TextStyle(
                                        font_family="Montserrat SemiBold", size=14),
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
        cats = self._ctrl.get_categories()

        error_style = ft.TextStyle(
            font_family="Montserrat Medium", size=10, color="#FF0000"
        )

        category_dd = ft.Dropdown(
            label="Категория",
            border_color="#6C63FF",
            options=[ft.dropdown.Option(str(c.id), c.name) for c in cats],
            value=str(transaction["category_id"]),
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

        raw_date = transaction["date"]
        try:
            d = datetime.datetime.strptime(raw_date, "%Y-%m-%d").date()
            display_date = d.strftime("%d.%m.%Y")
        except Exception:
            display_date = raw_date

        date_field = ft.TextField(
            label="Дата",
            value=display_date,
            read_only=True,
            border_color="#6C63FF",
            suffix_icon=ft.Icons.CALENDAR_MONTH,
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

        def validate_category(e):
            category_dd.error = None if category_dd.value else "Выберите категорию"
            category_dd.update()

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

        category_dd.on_change = validate_category
        amount_field.on_change = validate_amount

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

            if any(f.error for f in (category_dd, amount_field)):
                category_dd.update()
                amount_field.update()
                return

            parsed_date = parse_date(date_field.value)

            self._ctrl.update_transaction(
                transaction_id=transaction["id"],
                amount=amount,
                category_id=int(category_dd.value),
                description=desc_field.value or None,
                date=str(parsed_date),
            )
            self.rebuild()
            pages = self.page_ref.data.get("pages", {})
            if 0 in pages:
                pages[0].rebuild()
            bs.open = False
            self.page.update()

        bs.content = ft.Container(
            padding=ft.Padding.only(left=20, right=20, top=24, bottom=32),
            content=ft.Column(
                tight=True,
                spacing=16,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                "Редактировать расход",
                                color="#000000",
                                font_family="Montserrat SemiBold",
                                size=24,
                            ),
                        ],
                    ),
                    category_dd,
                    amount_field,
                    desc_field,
                    date_field,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.END,
                        controls=[
                            ft.TextButton(
                                "Отмена", on_click=on_cancel,
                                style=ft.ButtonStyle(
                                    color="#483EB7",
                                    text_style=ft.TextStyle(
                                        font_family="Montserrat SemiBold", size=14),
                                ),
                            ),
                            ft.TextButton(
                                "Сохранить", on_click=on_submit,
                                style=ft.ButtonStyle(
                                    color="#483EB7",
                                    text_style=ft.TextStyle(
                                        font_family="Montserrat SemiBold", size=14),
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