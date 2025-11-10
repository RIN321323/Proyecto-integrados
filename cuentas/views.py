
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.contrib import messages
from .forms import LoginForm, ProfesionalRegistroForm
from .models import Usuario, Rol
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
    recientes = Parto.objects.select_related('madre', 'created_by').order_by('-fecha_hora')[:5]
    # Mis registros
    mis_registros = Parto.objects.filter(created_by=request.user).select_related('madre').order_by('-fecha_hora')[:5]

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

def registro_profesional(request):
    """Vista para registro de profesionales de la salud"""
    if request.user.is_authenticated:
        return redirect("cuentas:dashboard")
    
    form = ProfesionalRegistroForm(request.POST or None)
    
    if request.method == "POST" and form.is_valid():
        # Obtener o crear el rol según el área seleccionada
        area = form.cleaned_data['area']
        rol, created = Rol.objects.get_or_create(nombre=area)
        
        # Crear el username basado en el RUN (sin guión)
        run = form.cleaned_data['run']
        username = run.replace('-', '').replace('.', '')
        
        # Verificar que el username no exista
        if Usuario.objects.filter(username=username).exists():
            form.add_error('run', 'Ya existe un usuario con este RUN')
            return render(request, "cuentas/registro_profesional.html", {"form": form})
        
        # Crear el usuario
        try:
            usuario = Usuario.objects.create_user(
                username=username,
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['nombre'],
                last_name=form.cleaned_data['apellido'],
                run=run,
                telefono=form.cleaned_data['telefono'],
                rol=rol,
                is_active=True
            )
            
            # Autenticar y hacer login automático
            user = authenticate(request, username=username, password=form.cleaned_data['password'])
            if user:
                login(request, user)
                messages.success(request, f'¡Bienvenido/a {usuario.get_full_name()}! Tu cuenta ha sido creada exitosamente.')
                return redirect("cuentas:dashboard")
        except Exception as e:
            form.add_error(None, f'Error al crear la cuenta: {str(e)}')
            return render(request, "cuentas/registro_profesional.html", {"form": form})
    
    return render(request, "cuentas/registro_profesional.html", {"form": form})
