# FinControl — flet-app
> Ветка с реализацией мобильного приложения на Python + Flet

## Запуск
```bash
git clone https://github.com/Dmitry-mironov4/FinControl.git
cd FinControl

uv sync

### Desktop
uv run python main.py

### iOS (Нужен Flet)
uv run flet run --ios main.py

### Android (Нужен Flet)
uv run flet run --android main.py
```

## Требования

| Инструмент | Версия |
|---|---|
| Python | 3.11+ |
| uv | 0.4+ |
| flet | 0.21+ |
| Flutter | для мобильной сборки |
