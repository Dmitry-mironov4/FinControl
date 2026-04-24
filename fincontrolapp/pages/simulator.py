import flet as ft
from components.base_page import BasePage


# ── shared style constants ────────────────────────────────────────────────────

_CARD_GRADIENT = ft.LinearGradient(
    colors=["#ffffff", "#88A2FF"],
    begin=ft.Alignment(-1, -1),
    end=ft.Alignment(1, 1),
)
_BTN_GRADIENT = ft.RadialGradient(
    colors=["#ffffff", "#88A2FF"],
    center=ft.Alignment(0, -0.2),
    radius=4.0,
    stops=[0.0, 0.8],
)

_RESULT_CARD = {
    "ok":      {"bgcolor": ft.Colors.with_opacity(0.1, "#82b6ff"),  "border_color": "#82b6ff"},
    "warning": {"bgcolor": ft.Colors.with_opacity(0.1, "#FFC802"),  "border_color": "#FFC802"},
    "error":   {"bgcolor": ft.Colors.with_opacity(0.1, "#FF7E1C"),  "border_color": ft.Colors.with_opacity(0.6, "#FF7E1C")},
}
_TONE_COLOR = {
    "neutral": "#253A82",
    "good":    "#82b6ff",
    "warn":    "#FFC802",
    "bad":     ft.Colors.with_opacity(0.6, "#FF7E1C"),
}

_TABS = ["Покупка", "Подписка", "Цель", "Урезать"]


class SimulatorPage(BasePage):
    def __init__(self, page, ctrl):
        self._ctrl = ctrl
        self._active_tab = 0
        super().__init__(page, "Симулятор")

    # ── header ────────────────────────────────────────────────────────────────

    def build_header(self):
        return ft.AppBar(
            title=ft.Text("Симулятор", font_family="Montserrat Extrabold", size=36),
            center_title=False,
            bgcolor=ft.Colors.TRANSPARENT,
            elevation=0,
            toolbar_height=50,
        )

    # ── body ──────────────────────────────────────────────────────────────────

    def build_body(self):
        self._result_container = ft.Container(visible=False)

        panel_builders = [
            self._build_purchase_panel,
            self._build_subscription_panel,
            self._build_goal_panel,
            self._build_cut_panel,
        ]
        active_panel = panel_builders[self._active_tab]()

        return ft.Column(
            controls=[self._build_tab_switcher(), active_panel, self._result_container],
            spacing=16,
        )

    def _build_tab_switcher(self) -> ft.Control:
        chips = []
        for i, label in enumerate(_TABS):
            active = (i == self._active_tab)
            chips.append(
            ft.GestureDetector(
                on_tap=lambda e, i=i: self._switch_tab(i),
                content=ft.Container(
                    padding=ft.Padding.only(left=20, right=20, top=9, bottom=9),
                    border_radius=20,
                    gradient=ft.RadialGradient(
                        colors=["#ffffff", "#88A2FF"],
                        center=ft.Alignment(0, -0.2),
                        radius=4.0,
                        stops=[0.0, 0.8],
                    ) if active else None,
                    bgcolor=ft.Colors.with_opacity(0.07, "#483EB7") if not active else None,
                    content=ft.Text(
                        label,
                        size=16,
                        font_family="Montserrat SemiBold",
                        color="#253A82" if active else ft.Colors.with_opacity(0.5, "#253A82"),
                    ),
                ),
            )
        )
        return ft.Container(
        border_radius=24,
        gradient=ft.LinearGradient(
            colors=["#ffffff", "#88A2FF"],
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(5, 5),
        ),
        padding=ft.Padding.only(left=4, right=4, top=4, bottom=4),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        content=ft.Row(
            chips,
            spacing=4,
            tight=True,
            scroll=ft.ScrollMode.AUTO,
        ),
    )

    def _switch_tab(self, i: int):
        self._active_tab = i
        self.refresh()

    # ── field factory ─────────────────────────────────────────────────────────

    def _field(self, label: str, suffix: str = "₽", hint: str = None,
               on_change=None) -> ft.TextField:
        return ft.TextField(
            label=label,
            hint_text=hint,
            border_color="#6C63FF",
            focused_border_color="#6C63FF",
            border_radius=12,
            bgcolor="#F5F5FF",
            suffix=ft.Text(suffix, font_family="Montserrat Medium",
                           color="#888888", size=14),
            label_style=ft.TextStyle(font_family="Montserrat Medium", color="#888888"),
            text_style=ft.TextStyle(font_family="Montserrat SemiBold", size=18),
            keyboard_type=ft.KeyboardType.NUMBER,
            error_style=ft.TextStyle(font_family="Montserrat Medium",
                                     size=10, color="#F44336"),
            on_change=on_change,
        )

    # ── SIM-UI-1: instant result hint below main amount field ─────────────────

    def _instant_hint(self, value_text: str, icon=ft.Icons.INFO_OUTLINE,
                      color="#6C63FF") -> ft.Container:
        """Small inline hint row that appears below the cost field."""
        return ft.Container(
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            bgcolor="rgba(108,99,255,0.07)",
            content=ft.Row(
                controls=[
                    ft.Icon(icon, color=color, size=15),
                    ft.Text(value_text, size=13, color=color,
                            font_family="Montserrat SemiBold"),
                ],
                spacing=6,
            ),
        )

    # ── SIM-UI-2: scenario cards ──────────────────────────────────────────────

    def _scenario_cards(self, scenarios: list[dict]) -> ft.Column:
        tone_icon = {
        "good":    ft.Icons.TRENDING_UP,
        "warn":    ft.Icons.WARNING_AMBER_OUTLINED,
        "bad":     ft.Icons.TRENDING_DOWN,
        "neutral": ft.Icons.COMPARE_ARROWS,
    }
        cards = []
        for s in scenarios:
          tone  = s.get("tone", "neutral")
          color = _TONE_COLOR[tone]
          icon  = tone_icon.get(tone, ft.Icons.COMPARE_ARROWS)
          cards.append(
            ft.Container(
                border_radius=14,
                padding=ft.padding.symmetric(horizontal=14, vertical=12),
                bgcolor="rgba(255,255,255,0.55)",
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                    controls=[
                        ft.Container(
                            width=36, height=36,
                            border_radius=10,
                            bgcolor=ft.Colors.with_opacity(0.15, color) if isinstance(color, str) else "rgba(255,255,255,0.15)",
                            content=ft.Icon(icon, color=color, size=18),
                            alignment=ft.Alignment(0, 0),
                        ),
                        ft.Container(
                            expand=True,
                            padding=ft.padding.only(left=10),
                            content=ft.Column(
                                controls=[
                                    ft.Text(
                                        s["label"],
                                        size=13,
                                        color="#253A82",
                                        no_wrap=True,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                        font_family="Montserrat SemiBold",
                                    ),
                                    ft.Text(
                                        s.get("sub", ""),
                                        size=11,
                                        color=ft.Colors.with_opacity(0.5, "#253A82"),
                                        font_family="Montserrat Medium",
                                    ),
                                ],
                                spacing=2,
                            ),
                        ),
                        ft.Text(
                            s["value"],
                            size=15,
                            color=color,
                            font_family="Montserrat SemiBold",
                            no_wrap=True,
                        ),
                    ],
                ),
            )
        )
        return ft.Column(controls=cards, spacing=8)

    # ── SIM-UI-3: before/after progress bars ─────────────────────────────────

    def _goal_progress_bars(self, before: float, after: float,
                            goal: float) -> ft.Container:
        """
        Shows two labelled ProgressBar rows side-by-side (before vs after).
        Values are fractions 0..1.
        """
        def _bar_row(label: str, value: float, color: str) -> ft.Column:
            pct = min(1.0, max(0.0, value))
            return ft.Column(
                expand=True,
                spacing=4,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(label, size=11, color="#888888",
                                    font_family="Montserrat Medium"),
                            ft.Text(f"{pct * 100:.0f}%", size=11, color=color,
                                    font_family="Montserrat SemiBold"),
                        ],
                    ),
                    ft.ProgressBar(
                        value=pct,
                        bgcolor="rgba(0,0,0,0.08)",
                        color=color,
                        height=8,
                        border_radius=ft.border_radius.all(4),
                    ),
                ],
            )

        before_frac = before / goal if goal > 0 else 0
        after_frac  = after  / goal if goal > 0 else 0

        return ft.Container(
            border_radius=14,
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
            bgcolor="rgba(255,255,255,0.55)",
            content=ft.Column(
                controls=[
                    ft.Text("Прогресс к цели",
                            size=13, color="#253A82",
                            font_family="Montserrat SemiBold"),
                    ft.Row(
                        controls=[
                            _bar_row("Сейчас",   before_frac, "#253A82"),
                            ft.Container(width=12),
                            _bar_row("После",    after_frac,  "#82b6ff"),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                f"Накоплено: {before:,.0f} ₽",
                                size=11,
                                color="rgba(37,58,130,0.6)",
                                font_family="Montserrat Medium",
                            ),
                            ft.Text(
                                f"Цель: {goal:,.0f} ₽",
                                size=11,
                                color="rgba(37,58,130,0.6)",
                                font_family="Montserrat Medium",
                            ),
                        ],
                    ),
                ],
                spacing=8,
            ),
        )

    # ── panels ────────────────────────────────────────────────────────────────

    def _build_purchase_panel(self) -> ft.Control:
        self._purchase_cost     = self._field("Стоимость покупки",
                                              on_change=self._on_purchase_cost_change)
        self._purchase_income   = self._field("Ежемесячный доход")
        self._purchase_expenses = self._field("Ежемесячные расходы")
        self._purchase_savings  = self._field("Уже накоплено", hint="0")

        # SIM-UI-1 — instant hint container
        self._purchase_hint = ft.Container(visible=False)

        return self._panel_card(
            hint="Узнайте, за сколько месяцев вы сможете накопить на нужную покупку",
            title="Параметры покупки",
            fields=[self._purchase_cost, self._purchase_hint,
                    self._purchase_income, self._purchase_expenses,
                    self._purchase_savings],
            on_calculate=self._on_calculate_purchase,
        )

    def _on_purchase_cost_change(self, e):
        """SIM-UI-1: instant hint when typing the cost."""
        raw = (self._purchase_cost.value or "").replace(" ", "").replace(",", ".").strip()
        try:
            val = float(raw)
            if val > 0:
                # Simple rough estimate: assume 20% saving rate as a teaser
                hint_text = f"≈ {val * 0.2:,.0f} ₽ в месяц — 20% от суммы"
                self._purchase_hint.content = self._instant_hint(
                    hint_text, ft.Icons.LIGHTBULB_OUTLINE, "#253A82")
                self._purchase_hint.visible = True
            else:
                self._purchase_hint.visible = False
        except ValueError:
            self._purchase_hint.visible = False
        try:
            self._purchase_hint.update()
        except Exception:
            pass

    def _build_subscription_panel(self) -> ft.Control:
        self._sub_cost     = self._field("Стоимость подписки в месяц")
        self._sub_income   = self._field("Ежемесячный доход")
        self._sub_expenses = self._field("Прочие расходы")
        self._sub_months   = self._field("Период анализа", suffix="мес.", hint="12")
        return self._panel_card(
            hint="Посмотрите, как подписка скажется на ваших накоплениях за период",
            title="Параметры подписки",
            fields=[self._sub_cost, self._sub_income,
                    self._sub_expenses, self._sub_months],
            on_calculate=self._on_calculate_subscription,
        )

    def _build_goal_panel(self) -> ft.Control:
        self._goal_amount   = self._field("Целевая сумма")
        self._goal_income   = self._field("Ежемесячный доход")
        self._goal_expenses = self._field("Ежемесячные расходы")
        self._goal_savings  = self._field("Уже накоплено", hint="0")
        return self._panel_card(
            hint="Рассчитайте, когда вы достигнете своей финансовой цели",
            title="Параметры цели",
            fields=[self._goal_amount, self._goal_income,
                    self._goal_expenses, self._goal_savings],
            on_calculate=self._on_calculate_goal,
        )

    def _build_cut_panel(self) -> ft.Control:
        self._cut_income   = self._field("Ежемесячный доход")
        self._cut_expenses = self._field("Текущие расходы")
        self._cut_percent  = self._field("На сколько урезать расходы",
                                         suffix="%", hint="10")
        self._cut_months   = self._field("Период анализа", suffix="мес.", hint="12")
        return self._panel_card(
            hint="Увидьте, сколько дополнительно можно накопить, сократив расходы",
            title="Параметры экономии",
            fields=[self._cut_income, self._cut_expenses,
                    self._cut_percent, self._cut_months],
            on_calculate=self._on_calculate_cut,
        )

    # ── shared panel builder ──────────────────────────────────────────────────

    def _panel_card(self, hint: str, title: str, fields: list,
                    on_calculate) -> ft.Control:
        card = ft.Container(
            border_radius=16,
            padding=16,
            gradient=_CARD_GRADIENT,
            content=ft.Column(
                controls=[
                    ft.Text(title, size=16, color="#253A82",
                            font_family="Montserrat SemiBold"),
                    *fields,
                ],
                spacing=12,
            ),
        )

        btn = ft.Container(
            width=float("inf"),
            height=48,
            border_radius=24,
            gradient=_BTN_GRADIENT,
            alignment=ft.Alignment(0, 0),
            content=ft.Text("Рассчитать", font_family="Montserrat SemiBold",
                            size=16, color="#000000"),
            on_click=on_calculate,
        )

        return ft.Column(
            controls=[
                ft.Text(hint, size=13, color="rgba(37,58,130,0.6)",
                        font_family="Montserrat Medium"),
                card,
                btn,
            ],
            spacing=16,
        )

    # ── validation ────────────────────────────────────────────────────────────

    def _parse_amount(self, field: ft.TextField, label: str,
                      required: bool = True, default: float = 0.0):
        raw = (field.value or "").replace(",", ".").replace(" ", "").replace("\u202f", "").strip()
        if not raw:
            if required:
                field.error_text = f"Введите {label}"
                return None, False
            field.error_text = None
            return default, True
        try:
            val = float(raw)
            if val < 0:
                field.error_text = "Значение не может быть отрицательным"
                return None, False
            field.error_text = None
            return val, True
        except ValueError:
            field.error_text = "Введите число, например: 50 000"
            return None, False

    def _parse_months(self, field: ft.TextField, default: int = 12):
        raw = (field.value or "").strip()
        if not raw:
            field.error_text = None
            return default, True
        try:
            val = int(raw)
            if val <= 0:
                field.error_text = "Период должен быть больше нуля"
                return None, False
            if val > 360:
                field.error_text = "Максимум 360 месяцев"
                return None, False
            field.error_text = None
            return val, True
        except ValueError:
            field.error_text = "Введите целое число, например: 12"
            return None, False

    def _parse_percent(self, field: ft.TextField, default: float = 10.0):
        raw = (field.value or "").replace(",", ".").strip()
        if not raw:
            field.error_text = None
            return default, True
        try:
            val = float(raw)
            if val <= 0 or val >= 100:
                field.error_text = "Введите значение от 1 до 99"
                return None, False
            field.error_text = None
            return val, True
        except ValueError:
            field.error_text = "Введите число, например: 10"
            return None, False

    def _refresh_fields(self, *fields):
        for f in fields:
            try:
                f.update()
            except Exception:
                pass

    # ── event handlers ────────────────────────────────────────────────────────

    def _on_calculate_purchase(self, e):
        fields = (self._purchase_cost, self._purchase_income,
                  self._purchase_expenses, self._purchase_savings)
        cost,     ok1 = self._parse_amount(self._purchase_cost, "стоимость покупки")
        income,   ok2 = self._parse_amount(self._purchase_income, "доход")
        expenses, ok3 = self._parse_amount(self._purchase_expenses, "расходы")
        savings,  ok4 = self._parse_amount(self._purchase_savings, "накопления",
                                           required=False)
        self._refresh_fields(*fields)
        if not all([ok1, ok2, ok3, ok4]):
            return
        try:
            result = self._ctrl.simulate_purchase(cost, income, expenses, savings)
        except Exception as ex:
            self._show_error(f"Ошибка расчёта: {ex}")
            return

        # SIM-UI-2 — scenario cards for purchase
        monthly_free = income - expenses
        if monthly_free > 0:
            months_needed = max(0, (cost - savings) / monthly_free)
            scenarios = [
                {
                    "label": f"Если куплю за {cost:,.0f} ₽",
                    "value": f"{months_needed:.1f} мес.",
                    "tone":  "good" if months_needed <= 6 else ("warn" if months_needed <= 18 else "bad"),
                    "sub":   "при текущем темпе накоплений",
                },
                {
                    "label": "Свободных в месяц",
                    "value": f"{monthly_free:,.0f} ₽",
                    "tone":  "good" if monthly_free > 0 else "bad",
                    "sub":   "доход минус расходы",
                },
                {
                    "label": "Уже накоплено",
                    "value": f"{savings / cost * 100:.0f}%" if cost > 0 else "—",
                    "tone":  "good" if savings / cost >= 0.5 else "neutral",
                    "sub":   f"{savings:,.0f} ₽ из {cost:,.0f} ₽",
                },
            ]
            result["_scenarios"] = scenarios

        self._show_result(result)

    def _on_calculate_subscription(self, e):
        fields = (self._sub_cost, self._sub_income, self._sub_expenses, self._sub_months)
        sub_cost,  ok1 = self._parse_amount(self._sub_cost, "стоимость подписки")
        income,    ok2 = self._parse_amount(self._sub_income, "доход")
        expenses,  ok3 = self._parse_amount(self._sub_expenses, "расходы")
        months,    ok4 = self._parse_months(self._sub_months)
        self._refresh_fields(*fields)
        if not all([ok1, ok2, ok3, ok4]):
            return
        try:
            result = self._ctrl.simulate_subscription(sub_cost, income, expenses, months)
        except Exception as ex:
            self._show_error(f"Ошибка расчёта: {ex}")
            return

        # SIM-UI-2 — subscription scenarios
        total_cost = sub_cost * months
        free_without = (income - expenses) * months
        free_with    = (income - expenses - sub_cost) * months
        scenarios = [
            {
                "label": f"Если добавлю подписку {sub_cost:,.0f} ₽/мес.",
                "value": f"−{total_cost:,.0f} ₽",
                "tone":  "warn",
                "sub":   f"за {months} мес.",
            },
            {
                "label": "Накоплю без подписки",
                "value": f"{free_without:,.0f} ₽",
                "tone":  "good",
                "sub":   f"за {months} мес.",
            },
            {
                "label": "Накоплю с подпиской",
                "value": f"{free_with:,.0f} ₽",
                "tone":  "good" if free_with > 0 else "bad",
                "sub":   f"за {months} мес.",
            },
        ]
        result["_scenarios"] = scenarios
        self._show_result(result)

    def _on_calculate_goal(self, e):
        fields = (self._goal_amount, self._goal_income,
                  self._goal_expenses, self._goal_savings)
        goal,     ok1 = self._parse_amount(self._goal_amount, "целевую сумму")
        income,   ok2 = self._parse_amount(self._goal_income, "доход")
        expenses, ok3 = self._parse_amount(self._goal_expenses, "расходы")
        savings,  ok4 = self._parse_amount(self._goal_savings, "накопления",
                                           required=False)
        self._refresh_fields(*fields)
        if not all([ok1, ok2, ok3, ok4]):
            return
        try:
            result = self._ctrl.simulate_goal(goal, income, expenses, savings)
        except Exception as ex:
            self._show_error(f"Ошибка расчёта: {ex}")
            return

        # SIM-UI-3 — before/after progress bars
        monthly_free = income - expenses
        after_savings = savings + monthly_free * 12  # projection after 1 year
        result["_goal_bars"] = {
            "before": savings,
            "after":  after_savings,
            "goal":   goal,
        }
        self._show_result(result)

    def _on_calculate_cut(self, e):
        fields = (self._cut_income, self._cut_expenses,
                  self._cut_percent, self._cut_months)
        income,   ok1 = self._parse_amount(self._cut_income, "доход")
        expenses, ok2 = self._parse_amount(self._cut_expenses, "расходы")
        percent,  ok3 = self._parse_percent(self._cut_percent)
        months,   ok4 = self._parse_months(self._cut_months)
        self._refresh_fields(*fields)
        if not all([ok1, ok2, ok3, ok4]):
            return
        try:
            result = self._ctrl.simulate_cut(income, expenses, percent, months)
        except Exception as ex:
            self._show_error(f"Ошибка расчёта: {ex}")
            return

        # SIM-UI-2 — cut scenarios
        saved_monthly = expenses * (percent / 100)
        new_expenses  = expenses - saved_monthly
        free_before   = (income - expenses) * months
        free_after    = (income - new_expenses) * months
        scenarios = [
            {
                "label": f"Если урежу на {percent:.0f}%",
                "value": f"−{saved_monthly:,.0f} ₽/мес.",
                "tone":  "good",
                "sub":   "экономия в месяц",
            },
            {
                "label": "Накоплю без изменений",
                "value": f"{free_before:,.0f} ₽",
                "tone":  "neutral",
                "sub":   f"за {months} мес.",
            },
            {
                "label": "Накоплю после сокращения",
                "value": f"{free_after:,.0f} ₽",
                "tone":  "good",
                "sub":   f"+{free_after - free_before:,.0f} ₽ дополнительно",
            },
        ]
        result["_scenarios"] = scenarios
        self._show_result(result)

    def _show_result(self, result: dict):
        self._result_container.content = self._build_result(result)
        self._result_container.visible = True
        try:
            self._result_container.update()
        except Exception:
            pass

    # ── result rendering ──────────────────────────────────────────────────────

    def _build_result(self, result: dict) -> ft.Control:
        status   = result.get("status", "ok")
        metrics  = result.get("metrics", [])
        projection = result.get("projection", [])

        card_style = _RESULT_CARD.get(status, _RESULT_CARD["ok"])

        header_color = {
            "ok":      "#82b6ff",
            "warning": "#FFC802",
            "error":   ft.Colors.with_opacity(0.6, "#FF7E1C"),
        }.get(status, "#82b6ff")

        header_icon = {
            "ok":      ft.Icons.CHECK_CIRCLE_OUTLINE,
            "warning": ft.Icons.WARNING_AMBER_OUTLINED,
            "error":   ft.Icons.CANCEL_OUTLINED,
        }.get(status, ft.Icons.CHECK_CIRCLE_OUTLINE)

        controls = [
            ft.Row(
                controls=[
                    ft.Icon(header_icon, color=header_color, size=20),
                    ft.Text(
                        "Результаты прогноза",
                        size=16,
                        color=header_color,
                        font_family="Montserrat SemiBold",
                    ),
                ],
                spacing=8,
            ),
            ft.Divider(color=f"{header_color}40", height=1),
            ft.Column(
                controls=[self._metric_tile(m) for m in metrics],
                spacing=8,
            ),
        ]

        # SIM-UI-2 — scenario cards (if provided by handler)
        if "_scenarios" in result:
            controls.append(
                ft.Text("Сценарии", size=13, color="#888888",
                        font_family="Montserrat Medium")
            )
            controls.append(self._scenario_cards(result["_scenarios"]))

        # SIM-UI-3 — before/after progress bars (goal tab only)
        if "_goal_bars" in result:
            gb = result["_goal_bars"]
            controls.append(
                self._goal_progress_bars(gb["before"], gb["after"], gb["goal"])
            )

        if projection:
            controls.append(self._projection_bars(projection))

        return ft.Container(
            border_radius=16,
            padding=16,
            bgcolor=card_style["bgcolor"],
            border=ft.border.all(1, card_style["border_color"]),
            content=ft.Column(controls=controls, spacing=12),
        )

    def _metric_tile(self, m: dict) -> ft.Control:
        tone = m.get("tone", "neutral")
        value_color = _TONE_COLOR.get(tone, "#253A82")

        value_str = m.get("value", "—")
        if value_str.endswith("₽") or value_str.endswith(" ₽"):
          icon = ft.Icons.CURRENCY_RUBLE
        elif value_str.endswith("мес."):
          icon = ft.Icons.CALENDAR_MONTH_OUTLINED
        elif value_str.endswith("%"):
          icon = ft.Icons.PERCENT
        else:
          icon = ft.Icons.INFO_OUTLINE

        return ft.Container(
        border_radius=12,
        padding=ft.Padding(left=12, right=12, top=10, bottom=10),
        bgcolor="rgba(255,255,255,0.55)",
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(icon, color=value_color, size=16),
                        ft.Text(
                            m.get("label", ""),
                            size=13,
                            color="#888888",
                            font_family="Montserrat Medium",
                            expand=True,
                        ),
                    ],
                    spacing=8,
                    expand=True,  # занимает всё доступное место
                ),
                ft.Text(
                    value_str,
                    size=14,
                    color=value_color,
                    font_family="Montserrat SemiBold",
                    no_wrap=True,  # значение не переносится
                ),
            ],
        ),
    )

    def _projection_bars(self, projection: list) -> ft.Control:
        step = max(1, len(projection) // 12)
        sampled = projection[::step]
        max_val = max((abs(v) for v in sampled), default=1) or 1

        bars = []
        for i, val in enumerate(sampled):
            height = max(4, abs(val / max_val) * 60)
            color = "#82b6ff" if val >= 0 else ft.Colors.with_opacity(0.6, "#FF7E1C")
            month_num = i * step + 1
            bars.append(
                ft.Column(
                    controls=[
                        ft.Container(
                            width=18, height=height,
                            border_radius=4,
                            bgcolor=color,
                        ),
                        ft.Text(
                            str(month_num),
                            size=9,
                            color="#888888",
                            font_family="Montserrat Medium",
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                )
            )

        return ft.Column(
            controls=[
                ft.Text(
                    "Динамика накоплений по месяцам",
                    size=12,
                    color="#888888",
                    font_family="Montserrat Medium",
                ),
                ft.Container(
                    height=80,
                    content=ft.Row(
                        controls=bars,
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                        scroll=ft.ScrollMode.AUTO,  # ← не уходит за экран
                    ),
                ),
            ],
            spacing=4,
        )