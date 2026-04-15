import flet as ft
import datetime
from components.base_page import BasePage
from components.dialogs import show_dialog as _show_dialog, close_dialog as _close_dialog


class GoalsPage(BasePage):
    def __init__(self, page, ctrl):
        self._ctrl = ctrl
        super().__init__(page, "Цели")

    def build_header(self):
        return ft.AppBar(
            title=ft.Text(
                "Цели",
                font_family="Montserrat Extrabold",
                size=36,
            ),
            center_title=False,
            bgcolor=ft.Colors.TRANSPARENT,
            elevation=0,
            toolbar_height=50,
        )

    def build_body(self):
        goals = self._ctrl.get_goals()
        return ft.Column(
            controls=[
                self._goals_list(goals),
                ft.GestureDetector(
                    on_tap=self._open_add_dialog,
                    content=ft.Container(
                        width=float("inf"),
                        height=48,
                        border_radius=12,
                        gradient=ft.RadialGradient(
                            colors=["#ffffff", "#88A2FF"],
                            center=ft.Alignment(0, -0.2),
                            radius=4.0,
                            stops=[0.0, 0.8],
                        ),
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text(
                            "＋ Создать цель",
                            color=ft.Colors.BLACK,
                            font_family="Montserrat SemiBold",
                            size=16,
                        ),
                    ),
                ),
            ],
            spacing=16,
            expand=True,
        )

    def _goals_list(self, goals):
        if not goals:
            return ft.Container(
                padding=16,
                border_radius=16,
                gradient=ft.LinearGradient(
                    colors=["#ffffff", "#88A2FF"],
                    begin=ft.Alignment(-1, -1),
                    end=ft.Alignment(1, 1),
                ),
                content=ft.Text(
                    "Целей пока нет",
                    color="rgba(0,0,0,0.65)",
                    size=14,
                    font_family="Montserrat SemiBold",
                ),
            )

        cards = []
        for g in goals:
            target = g["target_amount"] or 1
            current = g["current_amount"] or 0
            progress = min(current / target, 1.0)
            percent = int(progress * 100)
            done = progress >= 1.0
            pace = self._ctrl.calc_pace(target, current, g["deadline"])

            bar_color = "#E3FC87" if done else "#253A82"
            percent_color = "#E3FC87" if done else "#253A82"

            status_row = []
            if done:
                status_row.append(
                    ft.Text(
                        "Цель достигнута!",
                        size=14,
                        color="#253A82",
                        font_family="Montserrat SemiBold",
                        weight=ft.FontWeight.W_600,
                    )
                )
            elif pace:
                status_row.append(
                    ft.Text(
                        pace,
                        size=12,
                        color="rgba(255, 126, 28, 0.6)",
                        font_family="Montserrat SemiBold",
                    )
                )

            # Фон-подсказка, который показывается при свайпе влево
            delete_bg = ft.Container(
                border_radius=16,
                padding=ft.Padding.only(right=20),
                alignment=ft.Alignment(1, 0),
                gradient=ft.RadialGradient(
                    colors=["#ffffff", "#FF7E1C"],
                    center=ft.Alignment(0.8, 0),
                    radius=2.0,
                ),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    controls=[
                        ft.Icon(
                            ft.Icons.DELETE_OUTLINE,
                            color=ft.Colors.with_opacity(0.8, "#FF7E1C"),
                            size=26,
                        ),
                        ft.Text(
                            "Удалить",
                            color=ft.Colors.with_opacity(0.8, "#FF7E1C"),
                            font_family="Montserrat SemiBold",
                            size=13,
                        ),
                    ],
                    spacing=4,
                ),
                visible=False,
            )

            # Сама карточка цели
            card_content = ft.Container(
                gradient=ft.RadialGradient(
                    colors=["#ffffff", "#88A2FF"],
                    center=ft.Alignment(0, -0.2),
                    radius=2.0,
                    stops=[0.0, 0.5],
                ),
                border_radius=16,
                padding=16,
                content=ft.Column(
                    [
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Row(
                                    [
                                        ft.Icon(ft.Icons.EMOJI_EVENTS, color="#E3FC87", size=18)
                                        if done
                                        else ft.Icon(ft.Icons.FLAG_OUTLINED, color="#253A82", size=18),
                                        ft.Text(
                                            g["name"],
                                            size=15,
                                            color="#253A82",
                                            font_family="Montserrat SemiBold",
                                            weight=ft.FontWeight.W_600,
                                        ),
                                    ],
                                    spacing=6,
                                ),
                                ft.Text(
                                    f"{percent}%",
                                    size=13,
                                    color=percent_color,
                                    font_family="Montserrat SemiBold",
                                    weight=ft.FontWeight.W_600,
                                ),
                            ],
                        ),
                        ft.ProgressBar(
                            value=progress,
                            color=bar_color,
                            bgcolor="rgba(37, 58, 130, 0.7)",
                            height=6,
                            border_radius=3,
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    f"{current:,.0f} ₽",
                                    size=13,
                                    color="rgba(37, 58, 130, 0.4)",
                                    font_family="Montserrat SemiBold",
                                ),
                                ft.Text(
                                    f"из {target:,.0f} ₽",
                                    size=13,
                                    color="rgba(37, 58, 130, 0.4)",
                                    font_family="Montserrat SemiBold",
                                ),
                            ],
                        ),
                        *([ft.Row(status_row)] if status_row else []),
                        ft.Row(
                            [
                                ft.TextButton(
                                    "Пополнить",
                                    icon=ft.Icons.ADD,
                                    on_click=lambda e, gid=g["id"], gname=g["name"]: self._open_deposit_dialog(
                                        gid, gname
                                    ),
                                    style=ft.ButtonStyle(
                                        color="#253A82",
                                        text_style=ft.TextStyle(
                                            font_family="Montserrat SemiBold",
                                            size=13,
                                        ),
                                    ),
                                ),
                                ft.Row(
                                    [
                                        ft.IconButton( #Изменить
                                            icon=ft.Icons.EDIT_OUTLINED,
                                            style=ft.ButtonStyle(
                                                color="#253A82",
                                                text_style=ft.TextStyle(
                                                    font_family="Montserrat SemiBold",
                                                    size=13,
                                                ),
                                            ),
                                            on_click=lambda e, goal=g: self._open_edit_dialog(goal),
                                        ),
                                        ft.IconButton( #Удалить
                                            icon=ft.Icons.DELETE_OUTLINE,
                                            style=ft.ButtonStyle(
                                                color=ft.Colors.with_opacity(0.6, "#FF7E1C"),
                                                text_style=ft.TextStyle(
                                                    font_family="Montserrat SemiBold",
                                                    size=13,
                                                ),
                                            ),
                                            on_click=lambda e, gid=g["id"], gname=g["name"]: self._confirm_delete(
                                                gid, gname
                                            ),
                                        ),
                                    ],
                                    spacing=0,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    ],
                    spacing=10,
                ),
            )

            # Стек: фон корзины снизу, карточка сверху
            stack = ft.Stack(
                controls=[delete_bg, card_content],
            )

            # Свайп влево через GestureDetector (замена Dismissible для Flet 0.82)
            # last_x запоминается в on_pan_update, т.к. DragEndEvent не имеет local_x
            swipe = {"start_x": 0.0, "last_x": 0.0}

            def on_pan_start(e, sw=swipe):
                sw["start_x"] = e.local_position.x
                sw["last_x"] = e.local_position.x

            def on_pan_update(e, cc=card_content, db=delete_bg, sw=swipe):
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
                    # свайп вправо — возвращаем на место
                    cc.offset = ft.Offset(0, 0)
                    cc.update()
                    if db.visible:
                        db.visible = False
                        db.update()

            def on_pan_end(e, cc=card_content, db=delete_bg, sw=swipe, gid=g["id"], gname=g["name"]):
                delta = sw["last_x"] - sw["start_x"]
                if delta < -80:
                    self._confirm_delete(gid, gname)
                cc.offset = ft.Offset(0, 0)
                cc.update()
                db.visible = False
                db.update()

            gesture = ft.GestureDetector(
                on_pan_start=on_pan_start,
                on_pan_update=on_pan_update,
                on_pan_end=on_pan_end,
                content=stack,
            )

            cards.append(gesture)

        return ft.Column(cards, spacing=12)

    def _confirm_delete(self, goal_id, goal_name):
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "Удалить цель?",
                color="#000000",
                font_family="Montserrat SemiBold",
                size=24,
            ),
        )

        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)

        def on_confirm(e):
            try:
                self._ctrl.delete_goal(goal_id)
                self.refresh()
            finally:
                _close_dialog(self.page_ref, dlg)

        dlg.content = ft.Text(
            f"Цель «{goal_name}» будет удалена.",
            color=ft.Colors.with_opacity(0.6, "#000000"),
            font_family="Montserrat Medium",
            size=14,
        )
        dlg.actions = [
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
                style=ft.ButtonStyle(
                    color=ft.Colors.with_opacity(0.6, "#FF7E1C"),
                    text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=14),
                ),
                on_click=on_confirm,
            ),
        ]
        _show_dialog(self.page_ref, dlg)

    def _open_add_dialog(self, e):
        error_style = ft.TextStyle(
            font_family="Montserrat Medium",
            size=10,
            color="#FF0000",
        )

        name_field = ft.TextField(
            label="Название цели",
            border_color="#6976EB",
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
            error_style=error_style,
        )
        amount_field = ft.TextField(
            label="Целевая сумма",
            border_color="#6976EB",
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
            error_style=error_style,
        )
        deadline_display = ft.TextField(
            label="Дата (необязательно)",
            hint_text="Выберите дату",
            read_only=True,
            border_color="#6976EB",
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
            suffix_icon=ft.Icons.CALENDAR_MONTH,
            error_style=error_style,
        )

        # Валидация при вводе
        def validate_name(e):
            name_field.error = (
                None if (name_field.value or "").strip() else "Введите название цели"
            )
            name_field.update()

        def validate_amount(e):
            v = (amount_field.value or "").replace(",", ".")
            if not v:
                amount_field.error = "Введите сумму"
            else:
                try:
                    amount_field.error = (
                        None if float(v) > 0 else "Сумма должна быть больше нуля"
                    )
                except ValueError:
                    amount_field.error = "Введите число, например: 10000"
            amount_field.update()

        name_field.on_change = validate_name
        amount_field.on_change = validate_amount

        # DatePicker
        def on_date_selected(e):
            deadline_display.value = (
                e.control.value.strftime("%Y-%m-%d") if e.control.value else ""
            )
            deadline_display.update()

        date_picker = ft.DatePicker(
            on_change=on_date_selected,
            first_date=datetime.datetime(year=2000, month=1, day=1),
            last_date=datetime.datetime(year=2030, month=12, day=31),
        )
        self.page.overlay.append(date_picker)

        def open_date_picker(e):
            self.page.dialog = date_picker
            date_picker.open = True
            self.page.update()

        deadline_display.on_click = open_date_picker

        # BottomSheet для Flet 0.82: открываем через bs.open = True
        bs = ft.BottomSheet(open=False, content=ft.Container())

        def on_cancel(e):
            bs.open = False
            self.page.update()

        def on_submit(e):
            name_field.error = None
            amount_field.error = None
            deadline_display.error = None

            name = (name_field.value or "").strip()
            if not name:
                name_field.error = "Введите название цели"

            amount = None
            if not amount_field.value:
                amount_field.error = "Введите сумму"
            else:
                try:
                    amount = float(amount_field.value.replace(",", "."))
                    if amount <= 0:
                        amount_field.error = "Сумма должна быть больше нуля"
                except ValueError:
                    amount_field.error = "Введите число, например: 10000"

            deadline = (deadline_display.value or "").strip() or None
            if deadline:
                try:
                    from datetime import date as _date
                    _date.fromisoformat(deadline)
                except ValueError:
                    deadline_display.error = "Формат даты: ГГГГ-ММ-ДД"

            if any(f.error for f in (name_field, amount_field, deadline_display)):
                name_field.update()
                amount_field.update()
                deadline_display.update()
                return

            self._ctrl.add_goal(name=name, target_amount=amount, deadline=deadline)
            bs.open = False
            self.page.update()
            self.refresh()

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
                                "Новая цель",
                                color="#000000",
                                font_family="Montserrat SemiBold",
                                size=24,
                            ),
                        ],
                    ),
                    name_field,
                    amount_field,
                    deadline_display,
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
                                "Создать",
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

    def _open_deposit_dialog(self, goal_id, goal_name):
        error_style = ft.TextStyle(
            font_family="Montserrat Medium",
            size=10,
            color="#FF0000",
        )
        amount_field = ft.TextField(
            label="Сумма пополнения",
            text_style=ft.TextStyle(
                font_family="Montserrat SemiBold",
                size=15,
                color="#000000",
            ),
            border_color="#6976EB",
            error_style=error_style,
        )

        # Валидация при вводе
        def validate(e):
            v = (amount_field.value or "").replace(",", ".")
            if not v:
                amount_field.error = "Введите сумму"
            else:
                try:
                    amount_field.error = (
                        None if float(v) > 0 else "Сумма должна быть больше нуля"
                    )
                except ValueError:
                    amount_field.error = "Введите число, например: 5000"
            amount_field.update()

        amount_field.on_change = validate

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
                    amount = float(amount_field.value.replace(",", "."))
                    if amount <= 0:
                        amount_field.error = "Сумма должна быть больше нуля"
                except ValueError:
                    amount_field.error = "Введите число, например: 5000"

            if amount_field.error:
                amount_field.update()
                return

            self._ctrl.deposit(goal_id, amount)
            bs.open = False
            self.page.update()
            self.rebuild()
            pages = self.page_ref.data.get("pages", {})
            if 0 in pages:
                pages[0].rebuild()
            self.page_ref.snack_bar = ft.SnackBar(
                ft.Text(f"Пополнено на {amount:,.0f} ₽"), open=True
            )
            self.page_ref.update()

        bs.content = ft.Container(
            padding=ft.Padding.only(left=20, right=20, top=24, bottom=32),
            content=ft.Column(
                tight=True,
                spacing=12,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                f"Пополнить: {goal_name}",
                                color="#000000",
                                font_family="Montserrat SemiBold",
                                size=24,
                            ),
                        ],
                    ),
                    ft.Text(
                        "Сумма спишется с баланса как расход «Накопления».",
                        size=12,
                        color=ft.Colors.with_opacity(0.6, "#000000"),
                        font_family="Montserrat Medium",
                    ),
                    amount_field,
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
                                "Пополнить",
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

    def _open_edit_dialog(self, goal):
        error_style = ft.TextStyle(
            font_family="Montserrat Medium",
            size=10,
            color="#FF0000",
        )

        name_field = ft.TextField(
            label="Название цели",
            value=goal["name"],
            border_color="#6976EB",
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
            error_style=error_style,
        )
        amount_field = ft.TextField(
            label="Целевая сумма",
            value=str(int(goal["target_amount"]) if goal["target_amount"] == int(goal["target_amount"]) else goal["target_amount"]),
            border_color="#6976EB",
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
            error_style=error_style,
        )
        deadline_display = ft.TextField(
            label="Дата (необязательно)",
            hint_text="Выберите дату",
            value=goal["deadline"] or "",
            read_only=True,
            border_color="#6976EB",
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
            suffix_icon=ft.Icons.CALENDAR_MONTH,
            error_style=error_style,
        )

        def validate_name(e):
            name_field.error = (
                None if (name_field.value or "").strip() else "Введите название цели"
            )
            name_field.update()

        def validate_amount(e):
            v = (amount_field.value or "").replace(",", ".")
            if not v:
                amount_field.error = "Введите сумму"
            else:
                try:
                    amount_field.error = (
                        None if float(v) > 0 else "Сумма должна быть больше нуля"
                    )
                except ValueError:
                    amount_field.error = "Введите число, например: 10000"
            amount_field.update()

        name_field.on_change = validate_name
        amount_field.on_change = validate_amount

        def on_date_selected(e):
            deadline_display.value = (
                e.control.value.strftime("%Y-%m-%d") if e.control.value else ""
            )
            deadline_display.update()

        date_picker = ft.DatePicker(
            on_change=on_date_selected,
            first_date=datetime.datetime(year=2000, month=1, day=1),
            last_date=datetime.datetime(year=2030, month=12, day=31),
        )
        self.page.overlay.append(date_picker)

        def open_date_picker(e):
            self.page.dialog = date_picker
            date_picker.open = True
            self.page.update()

        deadline_display.on_click = open_date_picker

        bs = ft.BottomSheet(open=False, content=ft.Container())

        def on_cancel(e):
            bs.open = False
            self.page.update()

        def on_submit(e):
            name_field.error = None
            amount_field.error = None
            deadline_display.error = None

            name = (name_field.value or "").strip()
            if not name:
                name_field.error = "Введите название цели"

            amount = None
            if not amount_field.value:
                amount_field.error = "Введите сумму"
            else:
                try:
                    amount = float(amount_field.value.replace(",", "."))
                    if amount <= 0:
                        amount_field.error = "Сумма должна быть больше нуля"
                except ValueError:
                    amount_field.error = "Введите число, например: 10000"

            deadline = (deadline_display.value or "").strip() or None
            if deadline:
                try:
                    from datetime import date as _date
                    _date.fromisoformat(deadline)
                except ValueError:
                    deadline_display.error = "Формат даты: ГГГГ-ММ-ДД"

            if any(f.error for f in (name_field, amount_field, deadline_display)):
                name_field.update()
                amount_field.update()
                deadline_display.update()
                return

            self._ctrl.update_goal(goal_id=goal["id"], name=name, target_amount=amount, deadline=deadline)
            bs.open = False
            self.page.update()
            self.refresh()

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
                                "Редактировать цель",
                                color="#000000",
                                font_family="Montserrat SemiBold",
                                size=24,
                            ),
                        ],
                    ),
                    name_field,
                    amount_field,
                    deadline_display,
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