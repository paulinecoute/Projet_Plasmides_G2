from django.shortcuts import render


def home(request):
    return render(request, 'biolib/home.html')


def create_template(request):
    return render(request, 'biolib/create_template.html')


def simulation(request):
    return render(request, 'biolib/simulation.html')


def search(request):
    return render(request, 'biolib/search.html')


def logout(request):
    return render(request, 'biolib/logout.html')


def login(request):
    return render(request, 'biolib/login.html')

