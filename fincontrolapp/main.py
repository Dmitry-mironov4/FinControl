import flet as ft
from pages import *
from components import *


def main(page: ft.Page):
    # --- Настройки страницы ---
    page.title = "FinControl"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0F0F14"
    page.padding = 0

    # --- Тёмная тема ---
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

    # --- Экраны ---
    pages = {
        0: HomePage(page),
        1: IncomePage(page),
        2: ExpensesPage(page),
        3: GoalsPage(page),
        4: SubscriptionsPage(page),
        5: AnalyticsPage(page),
        6: SettingsPage(page),
    }

    def navigate(index: int):
        content.content = pages[index]
        content.update()
        nav.selected_index = index
        nav.update()

    # --- Bottom Navigation Bar ---
    nav = ft.NavigationBar(
        selected_index=0,
        bgcolor="#1A1A24",
        indicator_color="#6C63FF",
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED, selected_icon=ft.Icons.HOME, label="Главная"),
            ft.NavigationBarDestination(icon=ft.Icons.TRENDING_UP_OUTLINED, selected_icon=ft.Icons.TRENDING_UP, label="Доходы"),
            ft.NavigationBarDestination(icon=ft.Icons.SHOPPING_CART_OUTLINED, selected_icon=ft.Icons.SHOPPING_CART, label="Расходы"),
            ft.NavigationBarDestination(icon=ft.Icons.STAR_OUTLINE, selected_icon=ft.Icons.STAR, label="Цели"),
            ft.NavigationBarDestination(icon=ft.Icons.SUBSCRIPTIONS_OUTLINED, selected_icon=ft.Icons.SUBSCRIPTIONS, label="Подписки"),
            ft.NavigationBarDestination(icon=ft.Icons.BAR_CHART_OUTLINED, selected_icon=ft.Icons.BAR_CHART, label="Графики"),
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS_OUTLINED, selected_icon=ft.Icons.SETTINGS, label="Настройки"),
        ],
        on_change=lambda e: navigate(e.control.selected_index),
    )

    # --- Начальный экран ---
    content.content = pages[0]

    page.add(
        ft.Column(
            controls=[content, nav],
            expand=True,
            spacing=0,
        )
    )


ft.app(main)