from django.urls import path
from . import views

app_name = "cuentas"
urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("registro-profesional/", views.registro_profesional, name="registro_profesional"),
    path("", views.dashboard, name="dashboard"),
    path("gestionar-usuarios/", views.gestionar_usuarios, name="gestionar_usuarios"),
    path("formulario-parto/", views.completar_formulario_parto, name="form_parto"),
]
