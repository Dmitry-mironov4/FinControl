"""
budget.py — Экран бюджетирования по категориям.

Показывает список бюджетов пользователя: категория, лимит, прогресс-бар,
сумма потрачено / лимит. Цвет бара: зелёный < 70%, жёлтый 70–90%, красный > 90%.

Кнопка «+» открывает диалог задания нового лимита.
Тап по строке открывает диалог редактирования лимита.
"""
import flet as ft
from components.base_page import BasePage
from controllers.budget_ctrl import BudgetController
from components import AppTheme
from utils import get_currency_symbol


class BudgetPage(BasePage):
    def __init__(self, page: ft.Page, controller: BudgetController):
        self._ctrl = controller
        self._page = page
        super().__init__(page,"Бюджеты")

    def build_body(self) -> ft.Control:
        return self._build_content()

    def refresh(self):
        self.rebuild()
        try:
            self.update()
        except RuntimeError:
            pass

    def _build_content(self) -> ft.Control:
        budgets = self._ctrl.get_budgets()
        currency = get_currency_symbol(self._page)

        self._list_ref = ft.Column(
            controls=self._build_budget_rows(budgets),
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        add_btn = ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            bgcolor="#6C63FF",
            foreground_color=ft.Colors.WHITE,
            on_click=lambda e: self._show_set_budget_dialog(),
        )

        return ft.Stack(
            controls=[
                ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Text("Бюджеты", font_family="Montserrat Bold",
                                           size=22, color=ft.Colors.WHITE),
                            padding=ft.padding.only(left=16, top=16, bottom=8),
                        ),
                        ft.Container(
                            content=self._list_ref,
                            expand=True,
                            padding=ft.padding.symmetric(horizontal=16),
                        ),
                    ],
                    expand=True,
                    spacing=0,
                ),
                ft.Container(
                    content=add_btn,
                    alignment=ft.Alignment(1, 1),
                    padding=ft.padding.only(right=16, bottom=16),
                ),
            ],
            expand=True,
        )

    def _build_budget_rows(self, budgets) -> list[ft.Control]:
        currency = get_currency_symbol(self._page)
        if not budgets:
            return [
                ft.Container(
                    content=ft.Text(
                        "Нет бюджетов. Нажмите + чтобы задать лимит.",
                        color=ft.Colors.WHITE54, font_family="Montserrat Medium",
                        size=14, text_align=ft.TextAlign.CENTER,
                    ),
                    alignment=ft.Alignment(0, 0),
                    padding=ft.padding.only(top=60),
                )
            ]

        rows = []
        for b in budgets:
            pct = min(b.progress_pct, 100)
            rows.append(
                ft.GestureDetector(
                    on_tap=lambda e, budget=b: self._show_set_budget_dialog(budget),
                    content=ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Text(b.category_name, font_family="Montserrat SemiBold",
                                                size=14, color=ft.Colors.WHITE, expand=True),
                                        ft.Text(
                                            f"{b.spent_amount:,.0f} / {b.limit_amount:,.0f} {currency}",
                                            font_family="Montserrat Medium",
                                            size=12, color=ft.Colors.WHITE70,
                                        ),
                                    ],
                                ),
                                ft.Stack(
                                    controls=[
                                        ft.Container(height=8, border_radius=4, bgcolor="#333355"),
                                        ft.Container(
                                            height=8, border_radius=4,
                                            bgcolor=b.status_color,
                                            width=None,  # задаётся через expand trick ниже
                                        ),
                                    ],
                                ),
                                ft.ProgressBar(
                                    value=pct / 100,
                                    bgcolor="#333355",
                                    color=b.status_color,
                                    height=8,
                                    border_radius=ft.border_radius.all(4),
                                ),
                                ft.Text(
                                    f"{b.progress_pct:.0f}% использовано",
                                    font_family="Montserrat Medium",
                                    size=11, color=ft.Colors.WHITE54,
                                ),
                            ],
                            spacing=6,
                        ),
                        padding=ft.padding.all(14),
                        border_radius=14,
                        bgcolor="#1A1A24",
                    ),
                )
            )
        return rows

    def _show_set_budget_dialog(self, budget=None):
        """Диалог задания / редактирования лимита."""
        categories = self._ctrl.get_expense_categories()
        if not categories:
            return

        currency = get_currency_symbol(self._page)

        amount_field = ft.TextField(
            label=f"Лимит ({currency})",
            keyboard_type=ft.KeyboardType.NUMBER,
            text_style=ft.TextStyle(font_family="Montserrat Medium"),
            label_style=ft.TextStyle(font_family="Montserrat Medium"),
            border_color="#6976EB",
            value=str(int(budget.limit_amount)) if budget else "",
        )

        cat_dropdown = ft.Dropdown(
            label="Категория",
            value=str(budget.category_id) if budget else None,
            options=[ft.dropdown.Option(key=str(c["id"]), text=c["name"]) for c in categories],
            text_style=ft.TextStyle(font_family="Montserrat Medium"),
            label_style=ft.TextStyle(font_family="Montserrat Medium"),
            border_color="#6976EB",
            disabled=budget is not None,  # нельзя менять категорию при редактировании
        )

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Бюджет по категории", font_family="Montserrat SemiBold"),
        )

        def on_save(e):
            raw = (amount_field.value or "").strip()
            cat_id_str = cat_dropdown.value
            if not raw or not cat_id_str:
                return
            try:
                limit = float(raw.replace(",", "."))
            except ValueError:
                return
            if limit <= 0:
                return
            self._ctrl.set_budget(int(cat_id_str), limit)
            from components import close_dialog
            close_dialog(self._page, dlg)
            self.refresh()

        def on_delete(e):
            if budget:
                self._ctrl.delete_budget(budget.id)
            from components import close_dialog
            close_dialog(self._page, dlg)
            self.refresh()

        def on_cancel(e):
            from components import close_dialog
            close_dialog(self._page, dlg)

        dlg.content = ft.Column(
            controls=[cat_dropdown, amount_field],
            tight=True, spacing=12,
        )
        actions = [
            ft.TextButton("Отмена", on_click=on_cancel,
                          style=ft.ButtonStyle(color="#483EB7",
                              text_style=ft.TextStyle(font_family="Montserrat SemiBold"))),
            ft.TextButton("Сохранить", on_click=on_save,
                          style=ft.ButtonStyle(color="#483EB7",
                              text_style=ft.TextStyle(font_family="Montserrat SemiBold"))),
        ]
        if budget:
            actions.insert(1, ft.TextButton("Удалить", on_click=on_delete,
                               style=ft.ButtonStyle(color="#F44336",
                                   text_style=ft.TextStyle(font_family="Montserrat SemiBold"))))
        dlg.actions = actions

        from components import show_dialog
        show_dialog(self._page, dlg)