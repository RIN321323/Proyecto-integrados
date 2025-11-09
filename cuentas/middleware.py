from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.conf import settings
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            current_time = timezone.now()
            last_activity = request.session.get('last_activity')
            
            if last_activity:
                last_activity = timezone.datetime.fromisoformat(last_activity)
                time_elapsed = (current_time - last_activity).total_seconds()
                
                if time_elapsed > 1200:  # 20 minutos
                    logout(request)
                    messages.warning(request, 'Tu sesión ha expirado por inactividad.')
                    # Redirigir a la URL de login definida en settings
                    return redirect(settings.LOGIN_URL)
            
            request.session['last_activity'] = current_time.isoformat()
        
        return self.get_response(request)

class AuditoriaMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated:
            logger.info(
                f"[AUDITORIA] usuario={request.user.username} "
                f"metodo={request.method} path={request.path} "
                f"fecha={timezone.now().isoformat()}"
            )
        return None
