"""
main.py — Точка входа приложения FinControl.

Здесь происходит:
- настройка страницы (тема, цвета, отступы)
- создание всех экранов приложения
- настройка нижней навигационной панели
- первоначальная навигация на главный экран

Запуск:
    flet run --ios fincontrolapp/main.py
"""

import flet as ft
from pages import *
from components import *


def main(page: ft.Page):
    """
    Главная функция приложения. Вызывается Flet при старте.

    Параметры:
        page (ft.Page): объект страницы Flet — аналог окна/экрана приложения.
                        Через него управляем темой, навигацией и контентом.
    """

    # --- Настройки страницы ---
    page.fonts = {
        "Montserrat": "fonts/Montserrat-Regular.ttf",
        "Montserrat Bold": "fonts/Montserrat-Bold.ttf",
        "Montserrat Semibold": "fonts/Montserrat-SemiBold.ttf",
        "Montserrat Medium": "fonts/Montserrat-Medium.ttf",
        "Montserrat Extrabold": "fonts/Montserrat-ExtraBold.ttf"
    }

    page.title = "FinControl"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = AppTheme.BG_PAGE
    page.padding = 0

    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary="#6C63FF",
            secondary="#03DAC6",
            surface="#1A1A24",
            on_primary="#FFFFFF",
        )
    )

    # --- Контейнер для контента ---
    content = ft.Container(expand=True)

    # --- Контейнер для навигации ---
    # Пересоздаётся при каждом переключении вкладки,
    # чтобы обновить активное состояние иконок.
    nav_container = ft.Container(expand=False)

    def build_nav(selected_index: int) -> ft.Container:
        """
        Строит кастомную нижнюю навигационную панель.

        Параметры:
            selected_index (int): индекс активной вкладки.

        Возвращает:
            ft.Container: панель навигации.
        """
        items = [
            ("navigation/home.svg", 0),
            ("navigation/transactions.svg", 1),
            ("navigation/goals.svg", 2),
            ("navigation/settings.svg", 3),
        ]

        def nav_item(src, index):
            active = selected_index == index
            return ft.GestureDetector(
                on_tap=lambda e, i=index: navigate(i),
                content=ft.Container(
                    width=56,
                    height=56,
                    border_radius=16,
                    bgcolor="#3D3D6B" if active else "#5B6EC7",
                    alignment=ft.Alignment(0, 0),
                    content=ft.Image(
                        src=src,
                        width=28,
                        height=28,
                    ),
                ),
            )

        return ft.Container(
            height=80,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Stack(
                controls=[
                    ft.Container(
                        expand=True,
                        content=ft.Image(
                            src="navigation/test.svg",
                            fit="fill",
                            expand=True,
                        ),
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

    def navigate(index: int):
        """
        Переключает активный экран при нажатии на вкладку навигации.

        Параметры:
            index (int): индекс выбранной вкладки.
        """
        content.content = pages[index]
        content.update()
        nav_container.content = build_nav(index)
        nav_container.update()

    # --- Экраны ---
    pages = {
        0: HomePage(page),
        1: TransactionsPage(page),
        2: GoalsPage(page),
        3: SettingsPage(page),
        4: SubscriptionsPage(page),
    }

    # Сохраняем функцию навигации в данных страницы
    page.data = {"navigate": navigate}

    # --- Начальный экран ---
    content.content = pages[0]
    nav_container.content = build_nav(0)

    # --- Компоновка ---
    page.add(
        ft.Stack(
            expand=True,
            controls=[
                ft.Image(
                    src="bg.svg",
                    fit="fill",
                    expand=True,
                ),
                ft.Column(
                    controls=[content, nav_container],
                    expand=True,
                    spacing=0,
                ),
            ],
        )
    )


ft.app(main, assets_dir="assets")