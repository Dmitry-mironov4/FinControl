import flet as ft


def empty_state(
    icon: str,
    title: str,
    subtitle: str,
    icon_color: str = "#483EB7",
) -> ft.Container:
    return ft.Container(
        padding=ft.Padding(left=16, right=16, top=32, bottom=32),
        border_radius=24,
        gradient=ft.LinearGradient(
            colors=["#ffffff", "#88A2FF"],
            begin=ft.Alignment(-2, -1),
            end=ft.Alignment(1, 8),
        ),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            controls=[
                ft.Container(
                    width=72, height=72,
                    border_radius=36,
                    bgcolor=ft.Colors.with_opacity(0.1, icon_color),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(icon, size=36, color=ft.Colors.with_opacity(0.5, icon_color)),
                ),
                ft.Text(
                    title,
                    size=16,
                    font_family="Montserrat SemiBold",
                    color=ft.Colors.with_opacity(0.6, "#000000"),
                    text_align=ft.TextAlign.CENTER,
                    weight=ft.FontWeight.W_600,
                ),
                ft.Text(
                    subtitle,
                    size=13,
                    font_family="Montserrat SemiBold",
                    color=ft.Colors.with_opacity(0.5, "#000000"),
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
        ),
    )