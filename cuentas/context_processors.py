from django.conf import settings


def signup_settings(request):
    """Expose minimal signup-related flags to templates.

    Returns:
        dict: {
            'ACCOUNT_ALLOW_PUBLIC_SIGNUP': bool,
            'ACCOUNT_INVITE_CODES_PRESENT': bool,
        }
    """
    return {
        'ACCOUNT_ALLOW_PUBLIC_SIGNUP': getattr(settings, 'ACCOUNT_ALLOW_PUBLIC_SIGNUP', True),
        'ACCOUNT_INVITE_CODES_PRESENT': bool(getattr(settings, 'ACCOUNT_INVITE_CODES', [])),
    }
