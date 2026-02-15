# core/site_config.py
# Все настройки магазина в одном месте — меняй здесь под каждого клиента

SITE_NAME = "Akbars"  # Название в шапке, title и т.д.
SITE_DESCRIPTION = "Лучшая этно одежда по доступным ценам в Кыргызстане"  # Для SEO и футера

# Логотип — положи файл в static/images/logo.png (или logo.jpg)
LOGO_PATH = "images/logo.png"  # Путь относительно static (замени файл под клиента)

PRIMARY_COLOR = "#00B7EB"   # Основной цвет (hex для Tailwind или CSS)
SECONDARY_COLOR = "#1E40AF" # Вспомогательный цвет

EMAIL = "info@shop.kg"      # Для контактов и уведомлений
PHONE = "+996 702 434 330"  # Телефон в футере

CURRENCY_SYMBOL = "сом"     # Символ валюты (KGS)
CURRENCY_CODE = "KGS"

# Другие полезные (добавим позже, если нужно)
DELIVERY_INFO = "Доставка по Бишкеку — бесплатно от 5000 сом"