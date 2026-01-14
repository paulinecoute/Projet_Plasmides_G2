import os
import pathlib
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse, FileResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
import csv

# On importe le moteur de simulation
import insillyclo.simulator
import insillyclo.observer
import insillyclo.data_source

# 1. PAGE D'ACCUEIL
def home(request):
    return render(request, 'biolib/home.html')

# 2. INSCRIPTION
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

# 3. LA SIMULATION
def simulation(request):
    context = {}

    if request.method == 'POST' and request.FILES.get('template_file'):
        try:
            template_file = request.FILES['template_file']
            mapping_file = request.FILES.get('mapping_file')
            enzyme_name = request.POST.get('enzyme', 'BsmBI')

            output_dir = os.path.join(settings.MEDIA_ROOT, 'simulations', 'result_latest')
            os.makedirs(output_dir, exist_ok=True)

            template_path = os.path.join(output_dir, template_file.name)
            with open(template_path, 'wb+') as dest:
                for chunk in template_file.chunks(): dest.write(chunk)

            csv_paths = []
            if mapping_file:
                csv_path = os.path.join(output_dir, mapping_file.name)
                with open(csv_path, 'wb+') as dest:
                    for chunk in mapping_file.chunks(): dest.write(chunk)
                csv_paths.append(pathlib.Path(csv_path))

            # Recherche des plasmides
            plasmids_dir = pathlib.Path(settings.BASE_DIR) / 'plasmids'
            list_of_gb_files = list(plasmids_dir.rglob('*.gb'))

            if len(list_of_gb_files) == 0:
                raise Exception("Aucun fichier .gb trouvé dans le dossier 'plasmids' !")

            # Simulation
            observer = insillyclo.observer.InSillyCloCliObserver()
            insillyclo.simulator.compute_all(
                observer=observer,
                settings=None,
                output_dir=pathlib.Path(output_dir),
                input_template_filled=pathlib.Path(template_path),
                input_parts_files=csv_paths,
                gb_plasmids=list_of_gb_files,
                data_source=insillyclo.data_source.DataSourceHardCodedImplementation(),
                primers_file=None,
                enzyme_names=[enzyme_name],
                default_mass_concentration=200,
                sbol_export=False
            )

            # LECTURE ET PARSING DU CSV
            result_files = os.listdir(output_dir)
            target_csv = None
            for f in result_files:
                if f.endswith('.csv') and 'mapping' not in f.lower():
                    target_csv = os.path.join(output_dir, f)
                    break

            if target_csv:
                with open(target_csv, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    # On extrait la première ligne
                    headers = next(reader, None)
                    # On extrait toutes les autres lignes
                    rows = list(reader)

                    # On envoie ça au HTML
                    context['table_headers'] = headers
                    context['table_rows'] = rows

            context['success'] = True
            context['result_image'] = f"{settings.MEDIA_URL}simulations/result_latest/simulated_gel.png"

        except Exception as e:
            print(f"ERREUR : {e}")
            import traceback
            traceback.print_exc()
            context['error'] = str(e)

    return render(request, 'biolib/simulation.html', context)

# 4. FONCTIONS VIDES (Pour éviter les erreurs dans urls.py)
def create_template(request):
    return HttpResponse("Page de création de template (En construction)")

def search(request):
    return HttpResponse("Page de recherche (En construction)")

def download_empty_template(request):
    return HttpResponse("Téléchargement du template vide (En construction)")

def download_simulation_csv(request):
    # 1. On retrouve le fichier comme avant
    result_dir = os.path.join(settings.MEDIA_ROOT, 'simulations', 'result_latest')
    if not os.path.exists(result_dir):
        raise Http404("Aucune simulation trouvée.")

    files = os.listdir(result_dir)
    target_file = None
    for f in files:
        if f.endswith('.csv') and 'mapping' not in f.lower():
            target_file = f
            break

    if not target_file:
        raise Http404("Fichier CSV introuvable.")

    file_path = os.path.join(result_dir, target_file)

    # 2. On prépare la réponse HTTP (type CSV)
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig') # 'utf-8-sig' aide Excel à lire les accents
    response['Content-Disposition'] = f'attachment; filename="{target_file}"'

    # 3. CONVERSION : On lit avec ',' et on écrit avec ';'
    try:
        # Écrivain CSV configuré pour le format Français (point-virgule)
        writer = csv.writer(response, delimiter=';')

        with open(file_path, 'r', encoding='utf-8') as f:
            # Lecteur qui lit le format original (virgule)
            reader = csv.reader(f, delimiter=',')

            for row in reader:
                # On réécrit chaque ligne dans la réponse, mais avec des points-virgules
                writer.writerow(row)

        return response

    except Exception as e:
        print(f"Erreur lors de la conversion CSV : {e}")
        raise Http404("Erreur lors de la génération du fichier.")
