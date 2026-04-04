def show_dialog(page, dialog):
    if dialog not in page.overlay:
        page.overlay.append(dialog)
    page.update()
    page.show_dialog(dialog)


def close_dialog(page, dialog):
    page.pop_dialog()
    if dialog in page.overlay:
        page.overlay.remove(dialog)
    page.update()
