# biolib/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage

import os
import pathlib

# import insillyclo.data_source
# import insillyclo.observer
# import insillyclo.simulator


def home(request):
    return render(request, 'biolib/home.html')


def template(request):
    return render(request, 'biolib/template.html')


def create_template(request):
    return render(request, 'biolib/create_template.html')


def simulation(request):
    return render(request, 'biolib/simulation.html')

def simulation_result(request):
    return render(request, 'biolib/simulation_result.html')

def template_detail(request):
    return render(request, 'biolib/template_detail.html')
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()

    return render(request, 'biolib/signup.html', {'form': form})


# ESPACE PERSONNEL (DASHBOARD)

@login_required
def dashboard(request):
    return render(request, 'biolib/dashboard.html')
