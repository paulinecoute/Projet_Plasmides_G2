# biolib/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login
from django.http import FileResponse, HttpResponse
import os
import pathlib
import insillyclo.data_source
import insillyclo.observer
import insillyclo.simulator
from django.conf import settings
from django.core.files.storage import FileSystemStorage

def download_empty_template(request):
    file_path = os.path.join(settings.BASE_DIR, 'data_web', 'Typed_assembly', 'Campaign_display_L1.xlsx')
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='Campaign_display_L1.xlsx')


def home(request):
    return render(request, 'biolib/home.html')


def account(request):
    return render(request, 'biolib/account.html')


def create_template(request):
    return render(request, 'biolib/create_template.html')


def simulation(request):
    if request.method == 'POST':
        # Récupérer les fichiers uploadés
        template_file = request.FILES.get('template')
        parts_file = request.FILES.get('parts')
        primers_file = request.FILES.get('primers')
        concentration_file = request.FILES.get('concentration')

        # Sauvegarder les fichiers temporairement
        fs = FileSystemStorage()
        template_path = fs.save(template_file.name, template_file)
        parts_path = fs.save(parts_file.name, parts_file)
        primers_path = fs.save(primers_file.name, primers_file)
        concentration_path = fs.save(concentration_file.name, concentration_file)

        # Créer un observateur pour la simulation
        observer = insillyclo.observer.InSillyCloCliObserver(
            debug=False,
            fail_on_error=True,
        )

        # Définir le répertoire de sortie
        output_dir = pathlib.Path(settings.BASE_DIR) / 'output'
        output_dir.mkdir(parents=True, exist_ok=True)

        # Appeler la simulation
        try:
            insillyclo.simulator.compute_all(
                observer=observer,
                settings=None,
                input_template_filled=os.path.join(settings.BASE_DIR, template_path),
                input_parts_files=[
                    os.path.join(settings.BASE_DIR, parts_path),
                ],
                gb_plasmids=pathlib.Path(settings.BASE_DIR).glob('data_web/*/*.gb'),
                output_dir=output_dir,
                data_source=insillyclo.data_source.DataSourceHardCodedImplementation(),
                primers_file=os.path.join(settings.BASE_DIR, primers_path),
                primer_id_pairs=[
                    ('P29', 'P30'),
                ],
                enzyme_names=[
                    'NotI',
                ],
                default_mass_concentration=200,
                plasmid_concentration_file=os.path.join(settings.BASE_DIR, concentration_path),
                sbol_export=False,
            )
            # Retourner les résultats à l'utilisateur
            return render(request, 'biolib/simulation_results.html', {'output_dir': output_dir})
        except Exception as e:
            return HttpResponse(f"Une erreur est survenue : {str(e)}")

    # Si la méthode n'est pas POST, afficher le formulaire
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



