from .site_config import (
    SITE_NAME, SITE_DESCRIPTION, LOGO_PATH,
    EMAIL, PHONE, CURRENCY_SYMBOL
)

def site_config(request):
    return {
        'site_name': SITE_NAME,
        'site_description': SITE_DESCRIPTION,
        'logo_path': LOGO_PATH,
        'email': EMAIL,
        'phone': PHONE,
        'currency_symbol': CURRENCY_SYMBOL,
    }