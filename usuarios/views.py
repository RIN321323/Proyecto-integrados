from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Perfil

    
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']  
        password = request.POST['password']
        usuario = authenticate(request, username=username, password=password)
    if usuario is not None:
        login(request, usuario)
        return redirect('blog:lista_articulos')
    else:
        messages.error(request, 'Nombre de usuario o contraseña erroneos')
    return render (request/login.html)

@login_required
def logout_view(request):
    logout(request)
    return redirect('usuarios:login')






