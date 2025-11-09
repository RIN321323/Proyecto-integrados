
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from .forms import LoginForm
from registros.models import Parto
from django.utils import timezone

def login_view(request):
    if request.user.is_authenticated:
        return redirect("cuentas:dashboard")
    form = LoginForm(request.POST or None)
    error = None
    if request.method == "POST" and form.is_valid():
        u = form.cleaned_data["username"]
        p = form.cleaned_data["password"]
        user = authenticate(request, username=u, password=p)
        if user and user.is_active:
            login(request, user)
            return redirect("cuentas:dashboard")
        error = "Credenciales inválidas."
    return render(request, "cuentas/login.html", {"form": form, "error": error})

@login_required
def dashboard(request):
    # Estadísticas rápidas para matronas
    now = timezone.now()
    inicio_mes = now.replace(day=1)
    # Totales
    total_mes = Parto.objects.filter(fecha_hora__date__gte=inicio_mes.date()).count()
    total_30dias = Parto.objects.filter(fecha_hora__gte=now - timezone.timedelta(days=30)).count()
    # Últimos 5 registros (global)
    recientes = Parto.objects.select_related('madre').order_by('-fecha_hora')[:5]
    # Mis registros
    mis_registros = Parto.objects.filter(created_by=request.user).order_by('-fecha_hora')[:5]

    return render(request, "cuentas/dashboard.html", {
        'total_mes': total_mes,
        'total_30dias': total_30dias,
        'recientes': recientes,
        'mis_registros': mis_registros,
    })

@login_required
def logout_view(request):
    logout(request)
    return redirect("cuentas:login")


def requiere_rol(*rol_nombres):
    def _decorador(vista):
        def _wrap(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("cuentas:login")
            if not request.user.rol or request.user.rol.nombre not in rol_nombres:
                return HttpResponseForbidden("No tiene permisos para esta acción.")
            return vista(request, *args, **kwargs)
        return _wrap
    return _decorador


@requiere_rol("superusuario")
def gestionar_usuarios(request):
    # CRUD de usuarios solo para superusuario
    return render(request, "cuentas/gestionar_usuarios.html")

@requiere_rol("usuario", "superusuario")
def completar_formulario_parto(request):
    # Redirigir al formulario de registro de partos del app `registros`.
    # Esto permite centralizar la lógica de creación/edición en esa app.
    from django.shortcuts import redirect
    return redirect('registros:registro_parto')
