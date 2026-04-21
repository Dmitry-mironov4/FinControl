import flet as ft
import datetime
from datetime import date
from components.base_page import BasePage
from components.dialogs import close_dialog as _close_dialog
from components.form_utils import parse_amount, parse_date


class IncomePage(BasePage):
    def __init__(self, page: ft.Page, ctrl):
        self._ctrl = ctrl
        super().__init__(page, "Доходы")

    def build_header(self):
        return ft.AppBar(
            title=ft.Text(
                "Доходы",
                font_family="Montserrat Extrabold",
                size=36,
            ),
            center_title=False,
            bgcolor=ft.Colors.TRANSPARENT,
            elevation=0,
            toolbar_height=50,
        )

    def build_body(self):
        period = self._current_period_label()
        salary = self._ctrl.get_salary()
        incomes_all = self._ctrl.get_transactions()
        monthly_incomes = [t for t in incomes_all if self._is_current_month(t["date"])]
        additional = [t for t in monthly_incomes if not t["is_recurring"]]
        month_total = sum(t["amount"] for t in monthly_incomes)

        return ft.Column([
            self._salary_card(salary),
            ft.Container(
                bgcolor="#FFF2EE",
                border_radius=10,
                
                padding=ft.Padding.only(left=10, right=10, top=6, bottom=6),
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CALENDAR_MONTH, size=14, color="#6976EB"),
                        ft.Text(f"Период: {period}", size=12,font_family="Montserrat SemiBold", color="#6976EB"),
                        ft.Text(f"Сумма: {month_total:,.0f} ₽",font_family="Montserrat SemiBold", size=12, color="#483EB7"),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ),
            ft.Text("Дополнительные доходы", size=16, font_family="Montserrat SemiBold",
                    weight=ft.FontWeight.W_600, color="#1A1A24"),
            self._income_list(additional),
            ft.GestureDetector(
                on_tap=self._open_add_dialog,
                content=ft.Container(
                    width=float("inf"),
                    height=48,
                    border_radius=24,
                    gradient=ft.RadialGradient(
                        colors=["#ffffff", "#88A2FF"],
                        center=ft.Alignment(0, -0.2),
                        radius=4.0,
                        stops=[0.0, 0.8],
                    ),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text(
                        "＋ Добавить доход",
                        color=ft.Colors.BLACK,
                        font_family="Montserrat SemiBold",
                        size=16,
                    ),
                ),
            ),
        ], spacing=16)

    def _salary_card(self, salary):
        amount_text = f"{salary['amount']:,.0f} ₽" if salary else "Не указана"
        return ft.Container(
                padding=16,
                border_radius=16,
                gradient=ft.LinearGradient(
                    colors=["#ffffff", "#88A2FF"],
                    begin=ft.Alignment(-1, -1),
                    end=ft.Alignment(1, 1),
                ),
            content=ft.Column([
                ft.Text("Основная зарплата", size=14, font_family="Montserrat SemiBold", color="#888888"),
                ft.Text(amount_text, size=24, font_family="Montserrat SemiBold",
                        weight=ft.FontWeight.BOLD, color=ft.Colors.with_opacity(0.8, "#000000")),
                ft.ElevatedButton(
                    "Указать зарплату" if not salary else "Изменить зарплату",
                    icon=ft.Icons.EDIT,
                    style=ft.ButtonStyle(bgcolor="#E3FC87", text_style=ft.TextStyle(font_family="Montserrat SemiBold"), color="#000000"),
                    on_click=self._open_salary_dialog,
                ),
            ], spacing=8),
        )

    def _income_list(self, incomes):
        if not incomes:
            return ft.Container(
                                padding=16,
                border_radius=16,
                gradient=ft.LinearGradient(
                    colors=["#ffffff", "#88A2FF"],
                    begin=ft.Alignment(-1, -1),
                    end=ft.Alignment(1, 1),
                ),
                content=ft.Text("Нет записей", font_family="Montserrat SemiBold", color=ft.Colors.with_opacity(0.8, "#000000"), size=14),
            )

        rows = []
        for t in incomes:
            delete_bg = ft.Container(
                border_radius=16,
                padding=ft.Padding.only(right=16),
                alignment=ft.Alignment(1, 0),
                bgcolor=ft.Colors.TRANSPARENT,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    controls=[
                        ft.Icon(ft.Icons.DELETE_OUTLINE, color=ft.Colors.with_opacity(0.8, "#FF7E1C"), size=22),
                        ft.Text("Удалить", color=ft.Colors.with_opacity(0.8, "#FF7E1C"), size=13),
                    ],
                    spacing=4,
                ),
                visible=False,
            )

            row_content = ft.Container(
                padding=ft.Padding.only(left=16, right=8, top=10, bottom=10),
                border_radius=16,
                shadow=None,
                border=ft.Border(),
                gradient=ft.LinearGradient(
                    colors=["#ffffff", "#88A2FF"],
                    begin=ft.Alignment(-1, -1),
                    end=ft.Alignment(1, 1),
                ),

                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column([
                            ft.Text(t["category_name"], size=14, color="#000000", font_family="Montserrat SemiBold",
                                    weight=ft.FontWeight.W_500),
                            ft.Text(t["description"] or t["date"], font_family="Montserrat SemiBold",
                                    size=12, color=ft.Colors.with_opacity(0.8, "#000000")),
                        ], spacing=2, expand=True),
                        ft.Row([
                            ft.Text(
                                f"+ {t['amount']:,.0f} ₽",
                                color="#483EB7", size=14, font_family="Montserrat SemiBold",
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.IconButton(
                                ft.Icons.EDIT_OUTLINED,
                                icon_color=ft.Colors.with_opacity(0.8, "#000000"),
                                icon_size=18,
                                on_click=lambda e, tr=t: self._open_edit_dialog(tr),
                            ),
                            ft.IconButton(
                                ft.Icons.DELETE_OUTLINE,
                                icon_color=ft.Colors.with_opacity(0.8, "#000000"),
                                icon_size=18,
                                on_click=lambda e, tid=t["id"], cat=t["category_name"]: (
                                    self._confirm_delete(tid, cat)
                                ),
                            ),
                        ], spacing=0),
                    ],
                ),
            )

            stack = ft.Container(
                border_radius=16,
                bgcolor=ft.Colors.TRANSPARENT,
                border=ft.Border(),
                content=ft.Stack(
                    controls=[delete_bg, row_content],
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
    ),
)

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
            border_radius=16,
            padding=ft.Padding.only(top=4, bottom=4),
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
                self._show_success("Доход удалён")
            except Exception:
                self._show_error("Не удалось удалить доход")

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "Удалить доход?",
                color="#000000",
                font_family="Montserrat SemiBold",
                size=24,
            ),
            content=ft.Text(
                f"Доход «{category_name}» будет удалён.",
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

    def _make_date_field(self, label, initial_value):
        """Создаёт TextField с DatePicker для повторного использования."""
        field = ft.TextField(
            label=label,
            value=initial_value,
            read_only=True,
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
            border_color="#6976EB",
            suffix_icon=ft.Icons.CALENDAR_MONTH,
        )

        def on_date_selected(e):
            field.value = (
                e.control.value.strftime("%d.%m.%Y")
                if e.control.value
                else initial_value
            )
            field.update()

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

        field.on_click = open_date_picker
        return field

    def _open_salary_dialog(self, e):
        cats = self._ctrl.get_categories()
        salary_cat = next(
            (c for c in cats if c.name == "Зарплата"), cats[0] if cats else None
        )

        error_style = ft.TextStyle(
            font_family="Montserrat Medium", size=10, color="#FF0000"
        )

        amount_field = ft.TextField(
            label="Сумма зарплаты",
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
            border_color="#6976EB",
            error_style=error_style,
        )
        date_field = self._make_date_field("Дата", date.today().strftime("%d.%m.%Y"))

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
                    amount_field.error = "Введите число, например: 50000"
            amount_field.update()

        amount_field.on_change = validate_amount

        bs = ft.BottomSheet(open=False, content=ft.Container())

        def on_cancel(e):
            bs.open = False
            self.page.update()

        def on_submit(e):
            amount_field.error = None

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

            if amount_field.error:
                amount_field.update()
                return

            parsed_date = parse_date(date_field.value)

            try:
                existing = self._ctrl.get_salary()
                if existing:
                    self._ctrl.update_transaction(
                        existing["id"], amount,
                        existing["category_id"], existing["description"], str(parsed_date)
                    )
                else:
                    self._ctrl.add_transaction(
                        amount=amount,
                        category_id=salary_cat.id,
                        description="Зарплата",
                        date=str(parsed_date),
                        is_recurring=1,
                    )
            except Exception:
                self._show_error("Не удалось сохранить зарплату", close_bs=bs)
                return
            self.rebuild()
            pages = self.page_ref.data.get("pages", {})
            if 0 in pages:
                pages[0].rebuild()
            bs.open = False
            self.page.update()
            self._show_success("Зарплата сохранена")

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
                                "Указать зарплату",
                                color="#000000",
                                font_family="Montserrat SemiBold",
                                size=24,
                            ),
                        ],
                    ),
                    amount_field,
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

    def _open_add_dialog(self, e):
        cats = self._ctrl.get_categories()

        error_style = ft.TextStyle(
            font_family="Montserrat Medium", size=10, color="#FF0000"
        )

        _other = next((c for c in cats if c.name == "Другое"), None)
        category_dd = ft.Dropdown(
            label="Категория",
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
            border_color="#6976EB", 
            options=[ft.dropdown.Option(str(c.id), c.name) for c in cats],
            value=str(_other.id) if _other else None,
            error_style=error_style,
        )
        amount_field = ft.TextField(
            label="Сумма",
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
            border_color="#6976EB",
            error_style=error_style,
        )
        desc_field = ft.TextField(
            label="Описание (необязательно)", 
            border_color="#6976EB", text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=10),
        )
        date_field = self._make_date_field("Дата", date.today().strftime("%d.%m.%Y"))

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
                    amount_field.error = "Введите число, например: 1000"
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
                    amount_field.error = "Введите число, например: 1000"

            if any(f.error for f in (category_dd, amount_field)):
                category_dd.update()
                amount_field.update()
                return

            parsed_date = parse_date(date_field.value)

            try:
                self._ctrl.add_transaction(
                    amount=amount,
                    category_id=int(category_dd.value),
                    description=desc_field.value or None,
                    date=str(parsed_date),
                )
            except Exception:
                self._show_error("Не удалось добавить доход", close_bs=bs)
                return
            self.rebuild()
            pages = self.page_ref.data.get("pages", {})
            if 0 in pages:
                pages[0].rebuild()
            bs.open = False
            self.page.update()
            self._show_success("Доход добавлен")

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
                                "Добавить доход",
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
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
            border_color="#6976EB",
            options=[ft.dropdown.Option(str(c.id), c.name) for c in cats],
            value=str(transaction["category_id"]),
            error_style=error_style,
        )
        amount_field = ft.TextField(
            label="Сумма",
            value=str(int(transaction["amount"]) if transaction["amount"] == int(transaction["amount"]) else transaction["amount"]),
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
            border_color="#6976EB",
            error_style=error_style,
        )
        desc_field = ft.TextField(
            label="Описание (необязательно)",
            value=transaction["description"] or "",
            border_color="#6976EB", text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
        )
        date_field = self._make_date_field(
            "Дата",
            datetime.datetime.strptime(transaction["date"], "%Y-%m-%d").strftime("%d.%m.%Y"),
        )

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
                    amount_field.error = "Введите число, например: 1000"
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
                    amount_field.error = "Введите число, например: 1000"

            if any(f.error for f in (category_dd, amount_field)):
                category_dd.update()
                amount_field.update()
                return

            parsed_date = parse_date(date_field.value)

            try:
                self._ctrl.update_transaction(
                    transaction_id=transaction["id"],
                    amount=amount,
                    category_id=int(category_dd.value),
                    description=desc_field.value or None,
                    date=str(parsed_date),
                )
            except Exception:
                self._show_error("Не удалось сохранить доход", close_bs=bs)
                return
            self.rebuild()
            pages = self.page_ref.data.get("pages", {})
            if 0 in pages:
                pages[0].rebuild()
            bs.open = False
            self.page.update()
            self._show_success("Доход сохранён")

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
                                "Редактировать доход",
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