"""
base_page.py — Базовый класс для всех экранов приложения.

Паттерн: Template Method.
BasePage определяет скелет экрана (заголовок + тело), а каждая
дочерняя страница переопределяет только метод build_body().

Наследование:
    ft.Container → BasePage → HomePage, IncomePage, ExpensesPage, ...

Пример создания новой страницы:
    class MyPage(BasePage):
        def __init__(self, page):
            super().__init__(page, "Мой экран")

        def build_body(self):
            return ft.Text("Привет!")
"""

import flet as ft
from datetime import date

MONTH_NAMES = [
    "январь", "февраль", "март", "апрель", "май", "июнь",
    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
]

class BasePage(ft.Container):
    """
    Базовый класс для всех страниц приложения.

    Наследуется от ft.Container — значит сама является виджетом
    и может быть напрямую помещена в page или другой контейнер.

    Атрибуты:
        page_ref  (ft.Page): ссылка на объект страницы Flet.
                             Используется дочерними классами для показа
                             диалогов, снэкбаров и т.д.
        page_title (str):   заголовок экрана, отображается вверху.
    """

    def __init__(self, page: ft.Page, title: str, **kwargs):
        """
        Инициализирует базовую страницу.

        Параметры:
            page  (ft.Page): объект страницы от Flet (передаётся из main).
            title (str):     текст заголовка экрана.
            **kwargs:        дополнительные параметры для ft.Container.

        Порядок инициализации:
            1. super().__init__() — инициализация ft.Container.
            2. Сохранение ссылки на page и заголовка.
            3. Настройка внешнего вида контейнера.
            4. Вызов build_header() и build_body() для построения UI.
               ВАЖНО: build_body() вызывается здесь, поэтому дочерние
               классы должны вызывать super().__init__() в самом конце
               своего __init__, либо не определять __init__ вообще.
        """
        super().__init__(**kwargs)
        self.page_ref   = page
        self.page_title = title
        self.expand     = True                    # занимает всё доступное пространство
        self.bgcolor    = "transparent"               # фоновый цвет экрана
        self.padding    = ft.Padding(left=16, right=16, top=48, bottom=8)
        # top=48 — отступ сверху, чтобы контент не уходил под системную строку статуса
        # scroll=AUTO на внешней колонке — скроллится весь экран целиком,
        # включая заголовок. Дочерние build_body() НЕ должны задавать
        # собственный scroll, иначе получится скролл внутри скролла.
        self.content = ft.Column(
            controls=[self.build_header(), self.build_body()],
            expand=True,
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
        )

    def build_header(self) -> ft.Text:
        """
        Строит заголовок экрана.

        Возвращает крупный белый текст с названием страницы.
        Можно переопределить в дочернем классе для кастомной шапки
        (например, с кнопкой или аватаром пользователя).

        Возвращает:
            ft.Text: виджет заголовка.
        """
        return ft.Text(
            self.page_title,
            size=45,
            weight=ft.FontWeight.BOLD,
            color="#1A1A24",
        )

    def build_body(self) -> ft.Control:
        """
        Строит тело страницы. ДОЛЖЕН быть переопределён в каждом дочернем классе.

        Базовая реализация возвращает пустой контейнер — используется
        только как заглушка, если метод не переопределён.

        Возвращает:
            ft.Control: любой виджет Flet (Column, ListView, Stack и т.д.)
        """
        return ft.Container()

    @property
    def _user_id(self):
        return self.page_ref.data.get("user_id")

    def rebuild(self):
        """Перестраивает тело страницы без вызова update."""
        self.content.controls[1] = self.build_body()

    def refresh(self):
        """Перестраивает тело страницы и обновляет UI."""
        self.rebuild()
        try:
            self.update()
        except RuntimeError:
            pass

    def _is_current_month(self, value):
        if not value:
            return False
        return str(value).startswith(date.today().strftime("%Y-%m"))

    def _current_period_label(self):
        today = date.today()
        return f"{MONTH_NAMES[today.month - 1]} {today.year}"
