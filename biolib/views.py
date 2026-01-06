# biolib/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login


def home(request):
    return render(request, 'biolib/home.html')

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


def logout(request):
    return render(request, 'biolib/logout.html')


def create_template(request):
    return render(request, 'biolib/create_template.html')


def simulation(request):
    return render(request, 'biolib/simulation.html')


def search(request):
    return render(request, 'biolib/search.html')






