import flet as ft
import datetime
from datetime import date
from components.base_page import BasePage
from components.dialogs import close_dialog as _close_dialog
from components.empty_state import empty_state

MONTH_SHORT = ["янв", "фев", "мар", "апр", "май", "июн",
               "июл", "авг", "сен", "окт", "ноя", "дек"]

# Иконки популярных сервисов по ключевым словам в названии
SERVICE_ICONS = {
    "spotify": (ft.Icons.MUSIC_NOTE, "#1DB954"),
    "netflix": (ft.Icons.MOVIE, "#E50914"),
    "youtube": (ft.Icons.PLAY_CIRCLE, "#FF0000"),
    "apple": (ft.Icons.APPLE, "#555555"),
    "google": (ft.Icons.LANGUAGE, "#4285F4"),
    "yandex": (ft.Icons.SEARCH, "#FF0000"),
    "vk": (ft.Icons.PEOPLE, "#0077FF"),
    "telegram": (ft.Icons.TELEGRAM, "#2CA5E0"),
    "icloud": (ft.Icons.CLOUD, "#3C8DBC"),
    "xbox": (ft.Icons.SPORTS_ESPORTS, "#107C10"),
    "playstation": (ft.Icons.SPORTS_ESPORTS, "#003791"),
    "steam": (ft.Icons.VIDEOGAME_ASSET, "#1B2838"),
    "amazon": (ft.Icons.SHOPPING_CART, "#FF9900"),
    "курс": (ft.Icons.SCHOOL, "#6C63FF"),
    "gym": (ft.Icons.FITNESS_CENTER, "#FF5722"),
    "зал": (ft.Icons.FITNESS_CENTER, "#FF5722"),
    "фитнес": (ft.Icons.FITNESS_CENTER, "#FF5722"),
}

def _get_service_icon(name: str):
    name_lower = name.lower()
    for key, (icon, color) in SERVICE_ICONS.items():
        if key in name_lower:
            return icon, color
    return ft.Icons.SUBSCRIPTIONS, "#483EB7"

def _days_until(next_date) -> int:
    return (next_date - date.today()).days


class SubscriptionsPage(BasePage):
    def __init__(self, page: ft.Page, ctrl):
        self._ctrl = ctrl
        super().__init__(page, "Подписки")

    def build_header(self):
        return ft.AppBar(
            title=ft.Text(
                "Подписки",
                font_family="Montserrat Extrabold",
                size=36,
            ),
            center_title=False,
            bgcolor=ft.Colors.TRANSPARENT,
            elevation=0,
            toolbar_height=50,
        )

    def build_body(self):
        subscriptions = self._ctrl.get_subscriptions()
        monthly_total = self._ctrl.get_monthly_total()

        return ft.Column([
            ft.Container(
                padding=16,
                border_radius=16,
                gradient=ft.LinearGradient(
                    colors=["#ffffff", "#88A2FF"],
                    begin=ft.Alignment(-2, -1),
                    end=ft.Alignment(1, 8),
                ),
                content=ft.Column([
                    ft.Text("Сумма подписок в месяц", size=14,font_family="Montserrat SemiBold", color=ft.Colors.with_opacity(0.8, "#000000")),
                    ft.Text(f"{monthly_total:,.0f} ₽", size=28,font_family="Montserrat SemiBold",
                            weight=ft.FontWeight.BOLD, color="#000000"),
                ], spacing=4),
            ),
            self._subscriptions_list(subscriptions),
            ft.GestureDetector(
                on_tap=self._open_add_dialog,
                content=ft.Container(
                    width=float("inf"),
                    height=48,
                    border_radius=24,
                    gradient=ft.RadialGradient(
                        colors=["#ffffff", "#88A2FF"],
                        center=ft.Alignment(0, -0.2),
                        radius=8.0,
                        stops=[0.0, 0.8],
                    ),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text(
                        "＋ Добавить подписку",
                        color=ft.Colors.BLACK,
                        font_family="Montserrat SemiBold",
                        size=16,
                    ),
                ),
            ),
        ], spacing=16)

    def _subscriptions_list(self, subscriptions):
        if not subscriptions:
            return empty_state(
                icon=ft.Icons.SUBSCRIPTIONS_OUTLINED,
                title="Подписок нет",
                subtitle="Добавьте подписки чтобы отслеживать регулярные списания",
                icon_color="#DB5C0D",
            )

        rows = []
        for s in subscriptions:
            period_label = "в месяц" if s["period"] == "monthly" else "в год"
            next_date = self._ctrl.calc_next_charge_date(
                s["charge_day"], s["period"], s["start_date"]
            )
            next_label = f"{next_date.day} {MONTH_SHORT[next_date.month - 1]}."

            # Фон корзины — виден при свайпе влево
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

            svc_icon, svc_color = _get_service_icon(s["name"])
            days_left = _days_until(next_date)
            urgent = days_left <= 3
            next_color = ft.Colors.with_opacity(0.8, "#FF7E1C") if urgent else ft.Colors.with_opacity(0.7, "#000000")
            next_text = f"⚠ через {days_left} дн." if urgent else f"Следующее: {next_label}"
            # Годовая стоимость для месячных подписок
            yearly_text = f"{s['amount'] * 12:,.0f} ₽/год" if s["period"] == "monthly" else None

            row_content = ft.Container(
                padding=ft.Padding.only(left=16, right=8, top=10, bottom=10),
                border_radius=16,
                shadow=None,
                border=ft.Border(
                    top=ft.BorderSide(1.5, ft.Colors.with_opacity(0.5, "#FF7E1C")),
                    bottom=ft.BorderSide(1.5, ft.Colors.with_opacity(0.5, "#FF7E1C")),
                    left=ft.BorderSide(1.5, ft.Colors.with_opacity(0.5, "#FF7E1C")),
                    right=ft.BorderSide(1.5, ft.Colors.with_opacity(0.5, "#FF7E1C")),
                ) if urgent else ft.Border(),
                gradient=ft.LinearGradient(
                    colors=["#ffffff", "#88A2FF"],
                    begin=ft.Alignment(-2, -1),
                    end=ft.Alignment(1, 8),
                ),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row([
                            ft.Container(
                                width=36, height=36, border_radius=18,
                                bgcolor=ft.Colors.with_opacity(0.7, "#FFFFFF"),
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(svc_icon, color=svc_color, size=20),
                            ),
                            ft.Column([
                                ft.Text(s["name"], size=14, color="#000000",
                                        font_family="Montserrat SemiBold",
                                        weight=ft.FontWeight.W_500),
                                ft.Text(next_text, font_family="Montserrat SemiBold",
                                        size=12, color=next_color),
                            ], spacing=2, expand=True),
                        ], spacing=10, expand=True),
                        ft.Row([
                            ft.Column([
                                ft.Text(
                                    f"{s['amount']:,.0f} ₽",
                                    color="#483EB7", size=14,
                                    font_family="Montserrat SemiBold",
                                    weight=ft.FontWeight.W_600,
                                    text_align=ft.TextAlign.RIGHT,
                                ),
                                ft.Text(period_label, size=11,
                                        color=ft.Colors.with_opacity(0.8, "#000000"),
                                        font_family="Montserrat SemiBold",
                                        text_align=ft.TextAlign.RIGHT),
                                *([ft.Text(yearly_text, size=10,
                                           color=ft.Colors.with_opacity(0.5, "#000000"),
                                           font_family="Montserrat Medium",
                                           text_align=ft.TextAlign.RIGHT)]
                                  if yearly_text else []),
                            ], spacing=1,
                                horizontal_alignment=ft.CrossAxisAlignment.END),
                            ft.IconButton(
                                ft.Icons.EDIT_OUTLINED,
                                icon_color=ft.Colors.with_opacity(0.8, "#000000"), icon_size=18,
                                on_click=lambda e, sub=s: self._open_edit_dialog(sub),
                            ),
                            ft.IconButton(
                                ft.Icons.DELETE_OUTLINE,
                                icon_color=ft.Colors.with_opacity(0.8, "#000000"), icon_size=18,
                                on_click=lambda e, sid=s["id"], sname=s["name"]: (
                                    self._confirm_delete(sid, sname)
                                ),
                            ),
                        ], spacing=4),
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

            def on_pan_end(e, cc=row_content, db=delete_bg, sw=swipe,
                           sid=s["id"], sname=s["name"]):
                delta = sw["last_x"] - sw["start_x"]
                if delta < -80:
                    self._confirm_delete(sid, sname)
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

    def _confirm_delete(self, subscription_id, subscription_name):
        page = self.page_ref

        def on_cancel(e):
            _close_dialog(page, dlg)

        def on_confirm(e):
            _close_dialog(page, dlg)
            try:
                self._ctrl.delete_subscription(subscription_id)
                self.refresh()
                self._show_success("Подписка удалена")
            except Exception:
                self._show_error("Не удалось удалить подписку")

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "Удалить подписку?",
                color="#000000",
                font_family="Montserrat SemiBold",
                size=24,
            ),
            content=ft.Text(
                f"Подписка «{subscription_name}» будет удалена.",
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

    def _open_add_dialog(self, e):
        error_style = ft.TextStyle(
            font_family="Montserrat Medium",
            size=10,
            color="#FF0000",
        )

        name_field = ft.TextField(
            label="Название",
            border_color="#6976EB",
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
            error_style=error_style,
        )
        amount_field = ft.TextField(
            label="Сумма",
            border_color="#6976EB",
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
            error_style=error_style,
        )
        day_field = ft.TextField(
            label="День списания (1–31)",
            border_color="#6976EB",
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
            error_style=error_style,
        )
        period_dd = ft.Dropdown(
            label="Период",
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
            border_color="#6976EB",
            options=[
                ft.dropdown.Option("monthly", "Ежемесячно"),
                ft.dropdown.Option("yearly", "Ежегодно"),
            ],
            value="monthly",
        )

        # Поле даты с DatePicker
        start_field = ft.TextField(
            label="Дата начала",
            value=str(date.today()),
            read_only=True,
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
            border_color="#6976EB",
            suffix_icon=ft.Icons.CALENDAR_MONTH,
            error_style=error_style,
        )

        def on_date_selected(e):
            start_field.value = (
                e.control.value.strftime("%Y-%m-%d") if e.control.value else str(date.today())
            )
            start_field.update()

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

        start_field.on_click = open_date_picker

        # Валидация on_change
        def validate_name(e):
            name_field.error = (
                None if (name_field.value or "").strip() else "Введите название"
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
                    amount_field.error = "Введите число, например: 299.99"
            amount_field.update()

        def validate_day(e):
            v = (day_field.value or "").strip()
            if not v:
                day_field.error = "Введите день списания"
            else:
                try:
                    d = int(v)
                    day_field.error = (
                        None if 1 <= d <= 31 else "День должен быть от 1 до 31"
                    )
                except ValueError:
                    day_field.error = "Введите целое число"
            day_field.update()

        name_field.on_change = validate_name
        amount_field.on_change = validate_amount
        day_field.on_change = validate_day

        def dismiss_bs(e=None):
            # Убираем фокус со всех полей (закрывает клавиатуру)
            self.page.focus_trap = None
            for field in (name_field, amount_field, day_field, start_field):
                field.focused = False
                field.update()
            self.page.update()

        bs = ft.BottomSheet(
            open=False,
            content=ft.Container(),
            on_dismiss=lambda e: dismiss_bs(),
        )

        def on_cancel(e):
            bs.open = False
            self.page.update()

        def on_submit(e):
            name_field.error = None
            amount_field.error = None
            day_field.error = None

            name = (name_field.value or "").strip()
            if not name:
                name_field.error = "Введите название"

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

            if any(f.error for f in (name_field, amount_field, day_field)):
                name_field.update()
                amount_field.update()
                day_field.update()
                return

            try:
                self._ctrl.add_subscription(
                    name=name,
                    amount=amount,
                    charge_day=charge_day,
                    period=period_dd.value,
                    start_date=start_field.value,
                )
            except Exception:
                self._show_error("Не удалось добавить подписку", close_bs=bs)
                return
            bs.open = False
            self.page.update()
            self.refresh()
            self._show_success("Подписка добавлена")

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
                                "Добавить подписку",
                                color="#000000",
                                font_family="Montserrat SemiBold",
                                size=24,
                            ),
                        ],
                    ),
                    name_field,
                    amount_field,
                    start_field,
                    day_field,
                    period_dd,
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

    def _open_edit_dialog(self, subscription):
        error_style = ft.TextStyle(
            font_family="Montserrat Medium",
            size=10,
            color="#FF0000",
        )

        name_field = ft.TextField(
            label="Название",
            value=subscription["name"],
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
            border_color="#6976EB",
            error_style=error_style,
        )
        amount_field = ft.TextField(
            label="Сумма",
            value=str(int(subscription["amount"]) if subscription["amount"] == int(subscription["amount"]) else subscription["amount"]),
            border_color="#6976EB",
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
            error_style=error_style,
        )
        day_field = ft.TextField(
            label="День списания (1–31)",
            value=str(subscription["charge_day"]),
            border_color="#6976EB",
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
            error_style=error_style,
        )
        period_dd = ft.Dropdown(
            label="Период",
            border_color="#6976EB",
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
            options=[
                ft.dropdown.Option("monthly", "Ежемесячно"),
                ft.dropdown.Option("yearly", "Ежегодно"),
            ],
            value=subscription["period"],
        )

        start_field = ft.TextField(
            label="Дата начала",
            value=subscription["start_date"],
            read_only=True,
            border_color="#6976EB",
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=15),
            suffix_icon=ft.Icons.CALENDAR_MONTH,
            error_style=error_style,
        )

        def on_date_selected(e):
            start_field.value = (
                e.control.value.strftime("%Y-%m-%d") if e.control.value else subscription["start_date"]
            )
            start_field.update()

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

        start_field.on_click = open_date_picker

        def validate_name(e):
            name_field.error = (
                None if (name_field.value or "").strip() else "Введите название"
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
                    amount_field.error = "Введите число, например: 299.99"
            amount_field.update()

        def validate_day(e):
            v = (day_field.value or "").strip()
            if not v:
                day_field.error = "Введите день списания"
            else:
                try:
                    d = int(v)
                    day_field.error = (
                        None if 1 <= d <= 31 else "День должен быть от 1 до 31"
                    )
                except ValueError:
                    day_field.error = "Введите целое число"
            day_field.update()

        name_field.on_change = validate_name
        amount_field.on_change = validate_amount
        day_field.on_change = validate_day

        bs = ft.BottomSheet(open=False, content=ft.Container())

        def on_cancel(e):
            bs.open = False
            self.page.update()

        def on_submit(e):
            name_field.error = None
            amount_field.error = None
            day_field.error = None

            name = (name_field.value or "").strip()
            if not name:
                name_field.error = "Введите название"

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

            if any(f.error for f in (name_field, amount_field, day_field)):
                name_field.update()
                amount_field.update()
                day_field.update()
                return

            try:
                self._ctrl.update_subscription(
                    subscription_id=subscription["id"],
                    name=name,
                    amount=amount,
                    charge_day=charge_day,
                    period=period_dd.value,
                    start_date=start_field.value,
                )
            except Exception:
                self._show_error("Не удалось сохранить подписку", close_bs=bs)
                return
            bs.open = False
            self.page.update()
            self.refresh()
            self._show_success("Подписка сохранена")

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
                                "Редактировать подписку",
                                color="#000000",
                                font_family="Montserrat SemiBold",
                                size=24,
                            ),
                        ],
                    ),
                    name_field,
                    amount_field,
                    start_field,
                    day_field,
                    period_dd,
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