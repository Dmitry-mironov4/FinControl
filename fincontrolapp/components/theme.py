import flet as ft


class AppTheme:
    # ── Палитра: Arctic Light ─────────────────────────────────────────────────

    BACKGROUND      = "#f0f4f8"
    SURFACE         = "#ffffff"
    PRIMARY         = "#2563eb"
    SECONDARY       = ft.Colors.with_opacity(0.6,  "#88A2FF")
    INCOME          = "#16a34a"
    EXPENSE         = "#dc2626"
    TEXT            = "#0f172a"
    TEXT_MUTED      = "#64748b"

    # ── Производные / часто используемые ─────────────────────────────────────

    TEXT_MUTED_60   = ft.Colors.with_opacity(0.6,  TEXT_MUTED)
    TEXT_MUTED_45   = ft.Colors.with_opacity(0.45, TEXT_MUTED)
    PRIMARY_08      = ft.Colors.with_opacity(0.08,  PRIMARY)
    PRIMARY_15      = ft.Colors.with_opacity(0.15,  PRIMARY)
    INCOME_10       = ft.Colors.with_opacity(0.10,  INCOME)
    EXPENSE_10      = ft.Colors.with_opacity(0.10,  EXPENSE)

    # ── Градиенты ─────────────────────────────────────────────────────────────

    CARD_GRADIENT = ft.LinearGradient(
        colors=[SURFACE, "#88A2FF"],
        begin=ft.Alignment(-1, -1),
        end=ft.Alignment(1, 1),
    )

    BTN_GRADIENT = ft.RadialGradient(
        colors=[SURFACE, "#88A2FF"],
        center=ft.Alignment(0, -0.2),
        radius=4.0,
        stops=[0.0, 0.8],
    )

    # ── Радиусы ───────────────────────────────────────────────────────────────

    RADIUS_SM   = 10
    RADIUS_MD   = 16
    RADIUS_LG   = 24
    RADIUS_FULL = 100

    # ── Отступы ───────────────────────────────────────────────────────────────

    PAD_SM  = ft.padding.all(8)
    PAD_MD  = ft.padding.all(16)
    PAD_LG  = ft.padding.all(24)
    PAD_ROW = ft.padding.symmetric(horizontal=16, vertical=12)

    # ── Отступы (новый API) ───────────────────────────────────────────────────

    PAD_SM  = ft.Padding.all(8)
    PAD_MD  = ft.Padding.all(16)
    PAD_LG  = ft.Padding.all(24)
    PAD_ROW = ft.Padding.symmetric(horizontal=16, vertical=12)
    
    # ── Типографика ───────────────────────────────────────────────────────────

    FONT_REGULAR   = "Montserrat Medium"
    FONT_SEMI      = "Montserrat SemiBold"
    FONT_EXTRABOLD = "Montserrat Extrabold"

    # ── Borders ───────────────────────────────────────────────────────────────

    DIVIDER_COLOR  = ft.Colors.with_opacity(0.12, TEXT)
    BORDER_PRIMARY = ft.Colors.with_opacity(0.30, PRIMARY)

    # ── Алиасы для удобства ───────────────────────────────────────────────────
    BG_PAGE    = BACKGROUND
    BG_SURFACE = SURFACE
    BG_CARD    = SURFACE