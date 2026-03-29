import flet as ft
from components.base_page import BasePage
from components.dialogs import show_dialog as _show_dialog, close_dialog as _close_dialog


    
class GoalsPage(BasePage):
    def __init__(self, page, ctrl):
        self._ctrl = ctrl
        super().__init__(page, "Цели")

    def build_body(self):
        goals = self._ctrl.get_goals()
        return ft.Column([
            self._goals_list(goals),
            ft.ElevatedButton(
                "＋ Создать цель",
                style=ft.ButtonStyle(bgcolor="#6C63FF", color="#FFFFFF"),
                width=float("inf"),
                on_click=self._open_add_dialog,
            ),
        ], spacing=16)

    def _goals_list(self, goals):
        if not goals:
            return ft.Container(
                bgcolor="#1A1A24", border_radius=16, padding=16,
                content=ft.Text("Целей пока нет", color="#888888", size=14),
            )

        cards = []
        for g in goals:
            target = g['target_amount'] or 1
            current = g['current_amount'] or 0
            progress = min(current / target, 1.0)
            percent = int(progress * 100)
            done = progress >= 1.0
            pace = self._ctrl.calc_pace(target, current, g['deadline'])

            bar_color = "#4CAF50" if done else "#6C63FF"
            percent_color = "#4CAF50" if done else "#6C63FF"

            status_row = []
            if done:
                status_row.append(
                    ft.Text("Цель достигнута!", size=12, color="#4CAF50",
                            weight=ft.FontWeight.W_600)
                )
            elif pace:
                status_row.append(ft.Text(pace, size=12, color="#888888"))

            cards.append(ft.Container(
                bgcolor="#1A1A24", border_radius=16, padding=16,
                content=ft.Column([
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row([
                                ft.Icon(ft.Icons.EMOJI_EVENTS, color="#FFD700", size=18) if done
                                else ft.Icon(ft.Icons.FLAG_OUTLINED, color="#6C63FF", size=18),
                                ft.Text(g['name'], size=15, color="#FFFFFF",
                                        weight=ft.FontWeight.W_600),
                            ], spacing=6),
                            ft.Text(f"{percent}%", size=13, color=percent_color,
                                    weight=ft.FontWeight.W_600),
                        ],
                    ),
                    ft.ProgressBar(value=progress, color=bar_color, bgcolor="#2A2A35",
                                   height=6, border_radius=3),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(f"{current:,.0f} ₽", size=13, color="#CCCCCC"),
                            ft.Text(f"из {target:,.0f} ₽", size=13, color="#888888"),
                        ],
                    ),
                    *([ft.Row(status_row)] if status_row else []),
                    ft.Row([
                        ft.TextButton(
                            "Пополнить", icon=ft.Icons.ADD,
                            on_click=lambda e, gid=g['id'], gname=g['name']: (
                                self._open_deposit_dialog(gid, gname)
                            ),
                        ),
                        ft.TextButton(
                            "Удалить", icon=ft.Icons.DELETE_OUTLINE,
                            style=ft.ButtonStyle(color="#F44336"),
                            on_click=lambda e, gid=g['id'], gname=g['name']: (
                                self._confirm_delete(gid, gname)
                            ),
                        ),
                    ], spacing=0),
                ], spacing=10),
            ))

        return ft.Column(cards, spacing=12)

    def _confirm_delete(self, goal_id, goal_name):
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Удалить цель?"))

        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)

        def on_confirm(e):
            try:
                self._ctrl.delete_goal(goal_id)
                self.refresh()
            finally:
                _close_dialog(self.page_ref, dlg)

        dlg.content = ft.Text(f'Цель «{goal_name}» будет удалена.')
        dlg.actions = [
            ft.TextButton("Отмена", on_click=on_cancel),
            ft.TextButton("Удалить", style=ft.ButtonStyle(color="#F44336"), on_click=on_confirm),
        ]
        _show_dialog(self.page_ref, dlg)

    def _open_add_dialog(self, e):
        name_field = ft.TextField(label="Название цели", border_color="#6C63FF")
        amount_field = ft.TextField(label="Целевая сумма", keyboard_type=ft.KeyboardType.NUMBER,
                                    border_color="#6C63FF")
        deadline_field = ft.TextField(label="Дата (необязательно)", hint_text="ГГГГ-ММ-ДД",
                                      border_color="#6C63FF")

        dlg = ft.AlertDialog(modal=True, title=ft.Text("Новая цель"))

        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)

        def on_submit(e):
            try:
                if not name_field.value or not amount_field.value:
                    return
                amount = float(amount_field.value.replace(",", "."))
                self._ctrl.add_goal(
                    name=name_field.value,
                    target_amount=amount,
                    deadline=deadline_field.value or None,
                )
                self.refresh()
            except ValueError:
                return
            finally:
                _close_dialog(self.page_ref, dlg)

        dlg.content = ft.Column([name_field, amount_field, deadline_field], tight=True, spacing=12)
        dlg.actions = [
            ft.TextButton("Отмена", on_click=on_cancel),
            ft.TextButton("Создать", on_click=on_submit),
        ]
        _show_dialog(self.page_ref, dlg)

    def _open_deposit_dialog(self, goal_id, goal_name):
        amount_field = ft.TextField(label="Сумма пополнения", keyboard_type=ft.KeyboardType.NUMBER,
                                    border_color="#6C63FF")

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Пополнить: {goal_name}"),
            content=ft.Column([
                ft.Text("Сумма спишется с баланса как расход «Накопления».",
                        size=12, color="#888888"),
                amount_field,
            ], tight=True, spacing=12),
        )

        def on_cancel(e):
            _close_dialog(self.page_ref, dlg)

        def on_submit(e):
            try:
                if not amount_field.value:
                    return
                amount = float(amount_field.value.replace(",", "."))
                self._ctrl.deposit(goal_id, amount)
                self.rebuild()
                pages = self.page_ref.data.get("pages", {})
                if 0 in pages:
                    pages[0].rebuild()
                self.page_ref.snack_bar = ft.SnackBar(
                    ft.Text(f"Пополнено на {amount:,.0f} ₽"), open=True
                )
                self.page_ref.update()
            except ValueError:
                return
            finally:
                _close_dialog(self.page_ref, dlg)

        dlg.actions = [
            ft.TextButton("Отмена", on_click=on_cancel),
            ft.TextButton("Пополнить", on_click=on_submit),
        ]
        _show_dialog(self.page_ref, dlg)
