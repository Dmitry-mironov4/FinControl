"""Общие рендереры текст+клавиатура для подписок и целей.

Используются и в командах (/subscriptions, /goals), и в инлайн-меню
(sub_active, profile_goals) — чтобы не расходилось поведение между ними.

Каждая функция возвращает (text, markup | None):
- text — готовая строка для Message.answer / edit_text;
- markup — контент-специфичная клавиатура (например, кнопки пополнения целей),
  либо None, если вызывающая сторона сама прикрепит навигационное меню.
"""

import calendar
import datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.utils.formatters import MONTH_SHORT, fmt_amount
from fincontrolapp.db_queries import get_goals, get_subscriptions


def merge_keyboards(*markups: InlineKeyboardMarkup | None) -> InlineKeyboardMarkup:
    """Склеивает ряды кнопок из нескольких клавиатур сверху вниз, пропуская None."""
    rows: list[list[InlineKeyboardButton]] = []
    for m in markups:
        if m is None:
            continue
        rows.extend(m.inline_keyboard)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _next_charge_date(charge_day: int) -> str:
    today = datetime.date.today()

    last_day_this = calendar.monthrange(today.year, today.month)[1]
    day_this = min(charge_day, last_day_this)
    candidate = today.replace(day=day_this)

    if candidate < today:
        if today.month == 12:
            next_year, next_month = today.year + 1, 1
        else:
            next_year, next_month = today.year, today.month + 1
        last_day_next = calendar.monthrange(next_year, next_month)[1]
        day_next = min(charge_day, last_day_next)
        candidate = datetime.date(next_year, next_month, day_next)

    return f"{candidate.day} {MONTH_SHORT[candidate.month]}"


def _progress_bar(pct: float) -> str:
    filled = round(pct / 10)
    return "█" * filled + "░" * (10 - filled)


def _format_deadline(deadline_str: str | None) -> str:
    if not deadline_str:
        return ""
    try:
        d = datetime.date.fromisoformat(deadline_str)
        return f" · до {d.strftime('%d.%m.%Y')}"
    except ValueError:
        return ""


def render_subscriptions(user_id: int) -> tuple[str, InlineKeyboardMarkup | None]:
    """Текст со списком активных подписок и итогом в месяц.

    Markup всегда None — навигационное меню (subscriptions_keyboard)
    прикрепляет вызывающая сторона, если нужно.
    """
    subs = get_subscriptions(user_id)
    if not subs:
        return (
            "У вас нет активных подписок.\nДобавьте подписку в приложении FinControl.",
            None,
        )

    total = sum(
        float(s["amount"]) / 12 if s["period"] == "yearly" else float(s["amount"])
        for s in subs
    )
    lines = ["📋 Активные подписки:", ""]
    for s in subs:
        next_date = _next_charge_date(s["charge_day"])
        period = "/год" if s["period"] == "yearly" else "/мес"
        lines.append(
            f"• {s['name']} — {fmt_amount(float(s['amount']))}₽{period} · спишется {next_date}"
        )
    lines += ["", f"Итого в месяц: {fmt_amount(total)}₽"]
    return "\n".join(lines), None


def render_goals(
    user_id: int, with_topup_buttons: bool
) -> tuple[str, InlineKeyboardMarkup | None]:
    """Текст со списком целей (прогресс-бары, остаток, дедлайн).

    При with_topup_buttons=True возвращает клавиатуру с кнопками
    «+ Пополнить» для каждой недостигнутой цели; иначе markup=None.
    """
    goals = get_goals(user_id)
    if not goals:
        return (
            "🎯 У вас пока нет целей.\nДобавьте цель в приложении FinControl.",
            None,
        )

    lines = ["🎯 Твои цели:", ""]
    for g in goals:
        target = float(g["target_amount"])
        current = float(g["current_amount"])
        pct = min(current / target * 100, 100) if target > 0 else 0
        bar = _progress_bar(pct)
        remaining = max(target - current, 0)

        lines.append(f"🎯 {g['name']}")
        lines.append(
            f"   {bar} {pct:.0f}% · {fmt_amount(current)} / {fmt_amount(target)}₽"
        )
        if remaining > 0:
            deadline = _format_deadline(g["deadline"])
            lines.append(f"   Осталось: {fmt_amount(remaining)}₽{deadline}")
        else:
            lines.append("   ✅ Цель достигнута!")
        lines.append("")

    text = "\n".join(lines).rstrip()

    markup: InlineKeyboardMarkup | None = None
    if with_topup_buttons:
        buttons = [
            [
                InlineKeyboardButton(
                    text=f"+ Пополнить «{g['name']}»",
                    callback_data=f"goal_deposit_{g['id']}",
                )
            ]
            for g in goals
            if float(g["current_amount"]) < float(g["target_amount"])
        ]
        if buttons:
            markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    return text, markup
