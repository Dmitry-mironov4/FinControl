
import flet as ft


def build_nav(selected_index: int, on_navigate: callable) -> ft.Container:
    items = [
        ("navigation/home.svg",         0),
        ("navigation/analytics.svg",    1),
        ("navigation/goals.svg",        2),
        ("navigation/settings.svg",     3),
    ]

    def nav_item(src, index):
        active = selected_index == index
        return ft.GestureDetector(
            on_tap=lambda e, i=index: on_navigate(i),
            content=ft.Container(
                width=56, height=56,
                border_radius=16,
                bgcolor="#3D3D6B" if active else "#5B6EC7",
                alignment=ft.Alignment(0, 0),
                content=ft.Image(src=src, width=28, height=28),
            ),
        )

    return ft.Container(
        height=80,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        content=ft.Stack(
            controls=[
                ft.Container(
                    expand=True,
                    content=ft.Image(src="navigation/nav_bg.svg", fit="fill", expand=True),
                ),
                ft.Container(
                    expand=True,
                    padding=ft.Padding(left=16, right=16, top=12, bottom=24),
                    content=ft.Row(
                    controls=[nav_item(src, i) for src, i in items],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    ),
                ),
            ],
        ),
    )
