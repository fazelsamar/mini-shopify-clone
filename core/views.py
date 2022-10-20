from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def home(request):
    return render(request, 'core/index.html')


def login_view(request):
    if request.user.is_authenticated:
        messages.add_message(request, messages.WARNING, 'You are already loged in!')
        return redirect(reverse('core_app:home'))
    if request.method == 'POST':
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)
        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                messages.add_message(request, messages.SUCCESS, 'Login was successful')
                quey_param = request.GET.get('next', None)
                return redirect(quey_param if quey_param else reverse('core_app:home'))

        messages.add_message(request, messages.WARNING, 'User not found!')

    return render(request, 'core/login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.add_message(request, messages.SUCCESS, 'Logout was successful')
    return redirect(reverse('core_app:home'))
