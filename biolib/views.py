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


def download_empty_template(request):
    file_path = os.path.join(
        settings.BASE_DIR,
        'data_web',
        'Typed_assembly',
        'Campaign_display_L1.xlsx'
    )
    return FileResponse(
        open(file_path, 'rb'),
        as_attachment=True,
        filename='Campaign_display_L1.xlsx'
    )


def home(request):
    return render(request, 'biolib/home.html')


def create_template(request):
    return render(request, 'biolib/create_template.html')


def simulation(request):
    if request.method == 'POST':
        template_file = request.FILES.get('template')
        parts_file = request.FILES.get('parts')
        primers_file = request.FILES.get('primers')
        concentration_file = request.FILES.get('concentration')

        fs = FileSystemStorage()
        template_path = fs.save(template_file.name, template_file)
        parts_path = fs.save(parts_file.name, parts_file)
        primers_path = fs.save(primers_file.name, primers_file)
        concentration_path = fs.save(concentration_file.name, concentration_file)

        try:
            # Simulation désactivée pour l’instant
            return render(
                request,
                'biolib/simulation_results.html',
                {'output_dir': 'output'}
            )
        except Exception as e:
            return HttpResponse(f"Une erreur est survenue : {str(e)}")

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


# ESPACE PERSONNEL (DASHBOARD)

@login_required
def dashboard(request):
    return render(request, 'biolib/dashboard.html')
