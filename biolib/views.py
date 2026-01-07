# biolib/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth import login
from django.http import FileResponse
import os
from django.conf import settings

def download_empty_template(request):
    file_path = os.path.join(settings.BASE_DIR, 'data_web', 'Typed_assembly', 'Campaign_display_L1.xlsx')
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='Campaign_display_L1.xlsx')


def home(request):
    return render(request, 'biolib/home.html')


def create_template(request):
    return render(request, 'biolib/create_template.html')


def simulation(request):
    return render(request, 'biolib/simulation.html')


def search(request):
    return render(request, 'biolib/search.html')


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



