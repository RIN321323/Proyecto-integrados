from allauth.account.adapter import DefaultAccountAdapter
from django.http import HttpResponse
from django.conf import settings
from django.utils import timezone


class ControlledAccountAdapter(DefaultAccountAdapter):
    """
    Adaptador que controla el registro público.
    - Si SETTINGS.ACCOUNT_ALLOW_PUBLIC_SIGNUP es True -> permite registro público
    - Si es False -> permite registro solo si se provee un código de invitación
      vía GET/POST (?invite=CODE or invite_code) o si la sesión ya tiene 'account_invited'
    Esto combina la opción 1 (permitir público) y 2 (control con invitaciones).
    """
    def is_open_for_signup(self, request):
        allow = getattr(settings, 'ACCOUNT_ALLOW_PUBLIC_SIGNUP', True)
        # Check for invite code in GET or POST parameters early so we can consume it
        invite = None
        if request.method == 'GET':
            invite = request.GET.get('invite') or request.GET.get('invite_code')
        else:
            invite = request.POST.get('invite') or request.POST.get('invite_code')

        # If public signup is allowed and there's no invite, allow immediately
        if allow and not invite:
            return True

        # If the session already marked the user as invited, allow signup
        if request.session.get('account_invited'):
            return True

        # At this point, invite may be set (from above) or None

        # First check DB-backed InviteCode model (preferred)
        if invite:
            try:
                from .models import InviteCode
                code_qs = InviteCode.objects.filter(code=invite)
                if code_qs.exists():
                    code_obj = code_qs.first()
                    if not code_obj.is_valid():
                        return False
                    # Reserve a use slot immediately to avoid races and mark session so downstream can consume it when creating user
                    try:
                        code_obj.reserve()
                        request.session['account_invited'] = True
                        request.session['account_invite_code'] = invite
                        request.session['account_invite_reserved'] = True
                        return True
                    except Exception:
                        # if reserve fails, fallback to not accepting
                        return False
            except Exception:
                # If anything goes wrong (e.g., migrations not applied), fallback to settings
                pass

        # Fallback to settings-based static codes
        codes = getattr(settings, 'ACCOUNT_INVITE_CODES', []) or []
        if invite and invite in codes:
            request.session['account_invited'] = True
            request.session['account_invite_code'] = invite
            return True

        return False

    def respond_user_inactive(self, request):
        return HttpResponse(
            "Esta cuenta está inactiva. Por favor contacte al administrador.",
            status=403
        )

    def save_user(self, request, user, form, commit=True):
        """
        After a successful signup, if there is an invite code in session, try to mark it used.
        """
        # Use parent to actually save the user
        user = super().save_user(request, user, form, commit=commit)

        invite_code = request.session.get('account_invite_code')
        if invite_code:
            try:
                from .models import InviteCode
                code_qs = InviteCode.objects.filter(code=invite_code)
                if code_qs.exists():
                    code = code_qs.first()
                    # If we reserved earlier (on GET), finalize consumption without double-counting
                    if request.session.get('account_invite_reserved'):
                        code.consume(user=user)
                        try:
                            del request.session['account_invite_reserved']
                        except KeyError:
                            pass
                    else:
                        # Only mark if single_use or used flag not set
                        code.mark_used(user=user)
                    # remove session keys
                    try:
                        del request.session['account_invite_code']
                    except KeyError:
                        pass
                    try:
                        del request.session['account_invited']
                    except KeyError:
                        pass
            except Exception:
                # if migrations not applied or model missing, ignore
                pass

        return user