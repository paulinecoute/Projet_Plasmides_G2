from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse, Http404
from django.conf import settings
from django.db.models import Q
from .forms import CustomUserCreationForm, SimulationForm, CampaignTemplateForm, TemplatePartFormSet
from .models import Simulation, CampaignTemplate, Plasmid, Team, User, Correspondence, PlasmidCollection
import traceback
import pathlib
import glob
import os
import csv
import zipfile
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment
import pandas as pd

# Import Insillyclo
#try:
#    import insillyclo.observer
#    import insillyclo.simulator
#    from insillyclo.simulator import compute_all
#except ImportError:
#    class BaseObserver: pass
#    def compute_all(*args, **kwargs): pass
#
## Observer pour la console Django
#class DjangoConsoleObserver(insillyclo.observer.InSillyCloCliObserver if 'insillyclo.observer' in locals() else object):
#    def __init__(self):
#        if hasattr(insillyclo.observer, 'InSillyCloCliObserver'):
#            super().__init__(debug=False, fail_on_error=True)
#
#    def notify_message(self, message):
#        print(f"[INSILLYCLO] {message}")
#    def notify_progress(self, val): pass
#    def notify_missing_sequence_for_input_part(self, *args, **kwargs): pass
#    def assembly_start(self, *args, **kwargs): pass
#    def __getattr__(self, name):
#        # Sécurité ultime : si le simulateur appelle une méthode inconnue, on ne plante pas
#        def _missing(*args, **kwargs): return None
#        return _missing


import insillyclo.data_source
try:
    import insillyclo.observer
    BaseObserver = insillyclo.observer.InSillyCloObserver
except ImportError:
    class BaseObserver: pass
import insillyclo.simulator
try:
    from my_insillyclo.simulator import compute_all
except ImportError:
    def compute_all(*args, **kwargs): pass

class ConsoleObserver:
    def notify_message(self, message):
        print(f"[SIMULATION] {message}")
    def notify_progress(self, value):
        pass

class DjangoConsoleObserver(insillyclo.observer.InSillyCloCliObserver):
    def __init__(self):
        super().__init__(debug=False, fail_on_error=True)

    def notify_message(self, message):
        print(f"[INSILLYCLO] {message}")


# ==============================================================================
# 1. PAGES GÉNÉRALES
# ==============================================================================

def home(request):
    return render(request, 'biolib/home.html')

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'biolib/signup.html', {'form': form})

@login_required
def dashboard(request):
    collections_count = PlasmidCollection.objects.filter(owner=request.user).count()
    correspondences_count = Correspondence.objects.filter(owner=request.user).count()
    teams_count = request.user.teams.count()

    return render(request, "biolib/dashboard.html", {
        "collections_count": collections_count,
        "correspondences_count": correspondences_count,
        "teams_count": teams_count,
    })

# ==============================================================================
# 2. GESTION DES TEMPLATES
# ==============================================================================

def template(request):
    view_type = request.GET.get('view', 'recent')
    templates = CampaignTemplate.objects.none()
    title = "Templates récents"

    if request.user.is_authenticated:
        if view_type == 'private':
            templates = CampaignTemplate.objects.filter(owner=request.user, visibility='private').order_by('-created_at')
            title = "Mes templates privés"
        elif view_type == 'team':
            templates = CampaignTemplate.objects.filter(visibility='team', team__members=request.user).distinct().order_by('-created_at')
            title = "Templates d'équipe"
        elif view_type == 'public':
            templates = CampaignTemplate.objects.filter(visibility='public').order_by('-created_at')
            title = "Templates publics"
        else: # recent
            templates = CampaignTemplate.objects.filter(
                Q(owner=request.user) |
                Q(visibility='team', team__members=request.user) |
                Q(visibility='public')
            ).distinct().order_by('-id')[:5]
            title = "Templates récents"
    else:
        # Invité
        anon_ids = request.session.get('anon_templates', [])
        if view_type == 'public':
            templates = CampaignTemplate.objects.filter(visibility='public').order_by('-id')
            title = "Templates publics"
        else:
            templates = CampaignTemplate.objects.filter(
                Q(id__in=anon_ids) | Q(visibility='public')
            ).distinct().order_by('-id')[:5]
            title = "Templates récents"

    return render(request, 'biolib/template.html', {
        'templates': templates,
        'current_view': view_type,
        'page_title': title
    })

def create_template(request):
    # On définit proprement l'utilisateur à passer au formulaire
    # Si connecté -> request.user
    # Si invité -> None (pour éviter le crash "AnonymousUser")
    form_user = request.user if request.user.is_authenticated else None

    if request.method == 'POST':
        # On utilise form_user au lieu de request.user
        form = CampaignTemplateForm(request.POST, request.FILES, user=form_user)
        formset = TemplatePartFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            template = form.save(commit=False)

            if request.user.is_authenticated:
                template.owner = request.user
            else:
                template.owner = None
                template.visibility = 'private'

            # Sécurité : Si Team choisi mais pas d'équipe sélectionnée -> Force Privé
            if template.visibility == 'team' and not template.team:
                template.visibility = 'private'

            template.save()

            parts = formset.save(commit=False)
            for part in parts:
                part.template = template
                part.save()

            if not request.user.is_authenticated:
                session_templates = request.session.get('anon_templates', [])
                session_templates.append(template.id)
                request.session['anon_templates'] = session_templates
                request.session.modified = True

            return redirect('template')

    else:
        clone_id = request.GET.get('clone_from')

        if clone_id:
            original = get_object_or_404(CampaignTemplate, pk=clone_id)

            # Pré-remplissage (avec form_user)
            form = CampaignTemplateForm(user=form_user, initial={
                'name': f"{original.name} (Copie)",
                'enzyme': original.enzyme,
                'output_separator': original.output_separator,
                'description': original.description,
                'visibility': 'private', # Reset visibilité par sécurité
                'team': None             # Reset équipe
            })

            original_parts = original.parts.all().order_by('order')
            parts_data = []
            for part in original_parts:
                parts_data.append({
                    'name': part.name,
                    'type_id': part.type_id,
                    'order': part.order,
                    'is_mandatory': part.is_mandatory,
                    'include_in_output': part.include_in_output,
                    'is_separable': part.is_separable
                })

            formset = TemplatePartFormSet(initial=parts_data)
            formset.extra = len(parts_data)

        else:
            # Formulaire vide (avec form_user)
            form = CampaignTemplateForm(user=form_user)
            formset = TemplatePartFormSet()

    return render(request, 'biolib/create_template.html', {
        'form': form,
        'formset': formset
    })
def template_detail(request, pk):
    template = get_object_or_404(CampaignTemplate, pk=pk)
    return render(request, 'biolib/template_detail.html', {'template': template})

@login_required
def delete_template(request, pk):
    template = get_object_or_404(CampaignTemplate, pk=pk)

    if template.visibility == 'public':
        if not request.user.is_staff:
            return HttpResponse("Accès refusé.", status=403)
    elif template.visibility == 'team':
        is_team_leader = (template.team and template.team.leader == request.user)
        if request.user != template.owner and not is_team_leader:
             return HttpResponse("Accès refusé.", status=403)
    else:
        if request.user != template.owner:
            return HttpResponse("Accès refusé.", status=403)

    if request.method == 'POST':
        template.delete()
        return redirect('template')

    return render(request, 'biolib/template_confirm_delete.html', {'template': template})

def export_template_excel(request, template_id):
    template = get_object_or_404(CampaignTemplate, id=template_id)
    parts = template.parts.all().order_by('order')
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Assembly Template"

    blue_fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")
    green_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    bold_font = Font(bold=True)
    center_align = Alignment(horizontal="center", vertical="center")

    ws['A1'] = "Assembly settings"; ws['A1'].font = bold_font; ws['A1'].fill = blue_fill
    ws['A2'] = "Restriction enzyme"; ws['A2'].font = bold_font; ws['A2'].fill = blue_fill
    ws['B2'] = template.enzyme; ws['B2'].fill = green_fill
    ws['A3'] = "Name"; ws['A3'].font = bold_font; ws['A3'].fill = blue_fill
    ws['B3'] = template.name; ws['B3'].fill = green_fill
    ws['A4'] = "Output separator"; ws['A4'].font = bold_font; ws['A4'].fill = blue_fill
    ws['B4'] = template.output_separator; ws['B4'].fill = green_fill

    base_row = 8
    headers = ["Assembly composition", "Part types ->", "Is optional part ->", "Part name should be in output name ->", "Output plasmid id ↓"]
    for i, text in enumerate(headers):
        cell = ws.cell(row=base_row + i, column=1, value=text)
        cell.font = bold_font; cell.fill = blue_fill

    for index, part in enumerate(parts):
        col_num = 2 + index
        c1 = ws.cell(row=base_row, column=col_num, value=part.name); c1.fill = green_fill; c1.alignment = center_align
        c2 = ws.cell(row=base_row + 1, column=col_num, value=part.type_id); c2.fill = green_fill; c2.alignment = center_align
        c3 = ws.cell(row=base_row + 2, column=col_num, value="False" if part.is_mandatory else "True"); c3.fill = green_fill; c3.alignment = center_align
        c4 = ws.cell(row=base_row + 3, column=col_num, value="True" if part.include_in_output else "False"); c4.fill = green_fill; c4.alignment = center_align
        c5 = ws.cell(row=base_row + 4, column=col_num, value="↓"); c5.fill = blue_fill; c5.alignment = center_align

    ws.column_dimensions['A'].width = 35
    for col in range(2, 2 + len(parts)):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 20

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    clean_name = template.name.replace(" ", "_")
    response['Content-Disposition'] = f'attachment; filename="Campaign_{clean_name}.xlsx"'
    wb.save(response)
    return response


def simulation_list(request):
    view_type = request.GET.get('view', 'recent')
    simulations = Simulation.objects.none()
    title = "Simulations récentes"

    if request.user.is_authenticated:
        # CAS CONNECTÉ : On prend tout depuis la BDD liée à l'user
        source_qs = Simulation.objects.filter(user=request.user)
        team_qs = Simulation.objects.filter(visibility='team', team__members=request.user)
    else:
        # CAS INVITÉ : On prend tout depuis la Session
        sim_ids = request.session.get('anonymous_simulations', [])
        source_qs = Simulation.objects.filter(id__in=sim_ids)
        team_qs = Simulation.objects.none() # Un invité n'a pas d'équipe

    if view_type == 'recent':
        # On affiche les 5 dernières (BDD ou Session)
        simulations = source_qs.order_by('-date_run')[:5]
        title = "Simulations récentes"

    elif view_type == 'team':
        # Uniquement si connecté, sinon vide (mais la page reste la même)
        simulations = team_qs.distinct().order_by('-date_run')
        title = "Simulations d'équipe"

    else: # view == 'mine'
        # Tout l'historique (BDD ou Session)
        simulations = source_qs.order_by('-date_run')
        title = "Mes simulations"

    return render(request, 'biolib/simulation_list.html', {
        'simulations': simulations,
        'current_view': view_type,
        'page_title': title
    })

def create_simulation(request):
    if request.method == 'POST':
        form = SimulationForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            simulation = form.save(commit=False)

            if request.user.is_authenticated:
                simulation.user = request.user
            else:
                simulation.user = None

            simulation.status = 'RUNNING'

            selected_enzymes = form.cleaned_data.get('custom_enzymes')
            simulation.custom_enzymes = ",".join(selected_enzymes) if selected_enzymes else ""
            simulation.pcr_primers = form.cleaned_data.get('pcr_primers')

            if simulation.visibility == 'team' and not simulation.team:
                simulation.visibility = 'private'

            simulation.save()

            if not request.user.is_authenticated:
                anon_sims = request.session.get('anonymous_simulations', [])
                anon_sims.append(simulation.id)
                request.session['anonymous_simulations'] = anon_sims
                request.session.modified = True

            output_folder = os.path.join(settings.MEDIA_ROOT, 'simulations', str(simulation.id))
            os.makedirs(output_folder, exist_ok=True)

            path_xlsx = simulation.template_file.path
            path_csv_list = [simulation.campaign_file.path] if simulation.campaign_file else []

            gb_plasmids_paths = []
            all_parts = Plasmid.objects.all()
            for p in all_parts:
                if p.genbank_file:
                    try:
                        file_path = p.genbank_file.path
                        if os.path.exists(file_path):
                            gb_plasmids_paths.append(file_path)
                    except ValueError:
                        pass
            if simulation.zip_file:
                try:
                    zip_path = simulation.zip_file.path
                    extract_path = os.path.join(output_folder, 'extracted_parts')
                    os.makedirs(extract_path, exist_ok=True)

                    print(f"DEBUG: Extraction du ZIP {zip_path} vers {extract_path}")

                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_path)

                    # On parcourt le dossier extrait pour trouver tous les .gb
                    count_zip = 0
                    for root, dirs, files in os.walk(extract_path):
                        for file in files:
                            if file.lower().endswith(".gb") or file.lower().endswith(".gbk"):
                                full_path = os.path.join(root, file)
                                gb_plasmids_paths.append(full_path)
                                count_zip += 1

                    print(f"DEBUG: {count_zip} fichiers .gb ajoutés depuis le ZIP.")

                except Exception as e:
                    print(f"ERREUR ZIP: {e}")

            try:
                observer = DjangoConsoleObserver()
                compute_all(
                    observer=observer,
                    settings=None,
                    input_template_filled=path_xlsx,
                    input_parts_files=path_csv_list,
                    gb_plasmids=gb_plasmids_paths,
                    output_dir=output_folder,
                    data_source="Django",
                    assembly_enzyme=simulation.enzyme,
                    gel_enzymes=selected_enzymes if selected_enzymes else [],
                    user_primers=simulation.pcr_primers,
                    default_mass_concentration=200
                )

                # Correction séparateurs CSV
                tous_les_csv = glob.glob(os.path.join(output_folder, "*.csv"))
                for csv_path in tous_les_csv:
                    try:
                        df_temp = pd.read_csv(csv_path, sep=None, engine='python')
                        df_temp.to_csv(csv_path, sep=';', decimal=',', index=False)
                    except Exception:
                        pass

                creer_archive_resultats_seulement(dossier_source=output_folder, simulation_id=simulation.id)

                simulation.status = 'COMPLETED'

                path_png = os.path.join(output_folder, 'digestion.png')
                path_svg = os.path.join(output_folder, 'digestion.svg')
                if os.path.exists(path_png):
                       simulation.result_file = f"simulations/{simulation.id}/digestion.png"
                elif os.path.exists(path_svg):
                       simulation.result_file = f"simulations/{simulation.id}/digestion.svg"

                simulation.save()
                return redirect('simulation_result', pk=simulation.id)

            except Exception as e:
                print(f"Erreur simulation: {e}")
                traceback.print_exc()
                simulation.status = 'FAILED'
                simulation.save()
                return redirect('simulation_list')
    else:
        form = SimulationForm(user=request.user)

    return render(request, 'biolib/create_simulation.html', {'form': form})

def simulation_result(request, pk=None):
    simulation = get_object_or_404(Simulation, pk=pk)

    # Sécurité : Si privé, vérifier user. Si session, vérifier session.
    if simulation.visibility == 'private' and simulation.user and simulation.user != request.user:
        return HttpResponse("Accès refusé", status=403)

    output_folder = os.path.join(settings.BASE_DIR, 'media', 'simulations', str(pk))
    csv_path = os.path.join(output_folder, 'dilutions.csv')

    if not os.path.exists(csv_path):
        found_csvs = list(pathlib.Path(output_folder).glob("*.csv"))
        valid_csvs = [f for f in found_csvs if "concentration" not in f.name.lower()]
        if valid_csvs:
            csv_path = str(valid_csvs[0])

    csv_data = []
    if os.path.exists(csv_path):
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                content = f.read()
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(content[:1024])
                    reader = csv.reader(f, dialect)
                except:
                    reader = csv.reader(f, delimiter=',')
                csv_data = list(reader)
        except Exception:
            pass

    return render(request, 'biolib/simulation_result.html', {'simulation': simulation, 'csv_data': csv_data})

def update_simulation_gel(request, pk):
    simulation = get_object_or_404(Simulation, pk=pk)

    if request.method == 'POST':
        new_enzymes = request.POST.getlist('gel_enzymes')
        simulation.custom_enzymes = ",".join(new_enzymes) if new_enzymes else ""
        simulation.save()

        output_folder = os.path.join(settings.BASE_DIR, 'media', 'simulations', str(simulation.id))
        path_xlsx = simulation.template_file.path
        path_csv_list = [simulation.campaign_file.path] if simulation.campaign_file else []

        gb_plasmids_paths = []
        all_parts = Plasmid.objects.all()
        for p in all_parts:
            if p.genbank_file and os.path.exists(p.genbank_file.path):
                gb_plasmids_paths.append(p.genbank_file.path)

        try:
            observer = DjangoConsoleObserver()
            compute_all(
                observer=observer,
                settings=None,
                input_template_filled=path_xlsx,
                input_parts_files=path_csv_list,
                gb_plasmids=gb_plasmids_paths,
                output_dir=output_folder,
                data_source="Django",
                assembly_enzyme=simulation.enzyme,
                gel_enzymes=new_enzymes,
                user_primers=simulation.pcr_primers,
                default_mass_concentration=200
            )

            tous_les_csv = glob.glob(os.path.join(output_folder, "*.csv"))
            for csv_path in tous_les_csv:
                try:
                    df_temp = pd.read_csv(csv_path, sep=None, engine='python')
                    df_temp.to_csv(csv_path, sep=';', decimal=',', index=False)
                except Exception:
                    pass

            path_png = os.path.join(output_folder, 'digestion.png')
            path_svg = os.path.join(output_folder, 'digestion.svg')
            if os.path.exists(path_png):
                   simulation.result_file = f"simulations/{simulation.id}/digestion.png"
            elif os.path.exists(path_svg):
                   simulation.result_file = f"simulations/{simulation.id}/digestion.svg"
            simulation.save()
        except Exception:
            pass

    return redirect('simulation_result', pk=simulation.id)

# ==============================================================================
# 4. FICHIERS ET DOWNLOADS
# ==============================================================================

def creer_archive_resultats_seulement(dossier_source, simulation_id, fichiers_a_exclure=None):
    if fichiers_a_exclure is None: fichiers_a_exclure = []
    nom_zip = f"simulation_{simulation_id}_archive.zip"
    chemin_zip = os.path.join(dossier_source, nom_zip)

    candidats = glob.glob(os.path.join(dossier_source, "*.gb")) + glob.glob(os.path.join(dossier_source, "*.csv")) + glob.glob(os.path.join(dossier_source, "*.png"))

    noms_exclus = set(os.path.basename(f) for f in fichiers_a_exclure)
    fichiers_finaux = [f for f in candidats if os.path.basename(f) not in noms_exclus]

    if not fichiers_finaux: return None

    try:
        with zipfile.ZipFile(chemin_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for fichier in fichiers_finaux:
                zipf.write(fichier, arcname=os.path.basename(fichier))
        return chemin_zip
    except Exception:
        return None

def download_specific_file(request, pk, filename):
    if ".." in filename or "/" in filename: raise Http404
    file_path = os.path.join(settings.BASE_DIR, 'media','simulations', str(pk), filename)
    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    raise Http404

def download_simulation_zip(request, pk):
    zip_filename = f"simulation_{pk}_archive.zip"
    path_to_zip = os.path.join(settings.BASE_DIR, 'media', 'simulations', str(pk), zip_filename)
    if os.path.exists(path_to_zip):
        response = FileResponse(open(path_to_zip, 'rb'), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
        return response
    raise Http404

def download_simulation_csv(request, pk):
    # Backward compatibility
    return download_specific_file(request, pk, 'dilutions.csv')

# ==============================================================================
# 5. GESTION DES ÉQUIPES ET COLLECTIONS
# ==============================================================================

@login_required
def team_list(request):
    teams = Team.objects.filter(Q(leader=request.user) | Q(members=request.user)).distinct()
    for team in teams:
        team.tables_count = Correspondence.objects.filter(team=team).count()
        team.campaigns_count = Simulation.objects.filter(team=team).count()
        team.plasmids_count = Plasmid.objects.filter(collection__team=team).count()
    return render(request, 'biolib/teams.html', {'teams': teams})

@login_required
def team_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            team = Team.objects.create(name=name, description=request.POST.get('description', ''), purpose=request.POST.get('purpose'), leader=request.user)
            team.members.add(request.user)
            return redirect('teams')
    return render(request, 'biolib/team_create.html')

@login_required
def team_detail(request, team_id):
    team = get_object_or_404(Team, id=team_id, members=request.user)
    return render(request, 'biolib/team_detail.html', {
        'team': team,
        'is_leader': team.leader == request.user,
        'collections_count': team.plasmidcollection_set.count(),
        'tables_count': team.correspondence_set.count(),
        'campaigns_count': team.simulation_set.count(),
        'plasmids_count': Plasmid.objects.filter(collection__team=team).count(),
    })

@login_required
def team_manage_members(request, team_id):
    team = get_object_or_404(Team, id=team_id, members=request.user)
    if team.leader != request.user: return HttpResponse("Accès refusé", status=403)
    if request.method == 'POST':
        try:
            user = User.objects.get(email=request.POST.get('email'))
            team.members.add(user)
        except User.DoesNotExist: pass
    return render(request, 'biolib/team_manage_members.html', {'team': team})

@login_required
def team_change_leader(request, team_id, user_id):
    team = get_object_or_404(Team, id=team_id, members=request.user)
    if team.leader != request.user: return HttpResponse("Accès refusé", status=403)
    new_leader = get_object_or_404(User, id=user_id)
    if new_leader in team.members.all():
        team.leader = new_leader
        team.save()
    return redirect('team_detail', team_id=team.id)

@login_required
def team_remove_member(request, team_id, user_id):
    team = get_object_or_404(Team, id=team_id, members=request.user)
    if team.leader != request.user: return HttpResponse("Accès refusé", status=403)
    user = get_object_or_404(User, id=user_id)
    if user != team.leader:
        team.members.remove(user)
    return redirect('team_manage_members', team_id=team.id)

@login_required
def team_leave(request, team_id):
    team = get_object_or_404(Team, id=team_id, members=request.user)
    if request.user != team.leader:
        team.members.remove(request.user)
        return redirect('teams')
    return HttpResponse("Le chef ne peut pas quitter.", status=400)

@login_required
def team_delete(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    if team.leader == request.user:
        if request.method == 'POST':
            team.delete()
            return redirect('teams')
        return render(request, 'biolib/team_confirm_delete.html', {'team': team})
    return HttpResponse("Accès refusé", status=403)

@login_required
def collections_view(request):
    collections = PlasmidCollection.objects.filter(owner=request.user)
    return render(request, "biolib/collections.html", {"collections": collections})

@login_required
def collection_create(request):
    if request.method == "POST":
        collection = PlasmidCollection.objects.create(name=request.POST["name"], description=request.POST.get("description", ""), owner=request.user)
        return redirect("collection_detail", collection.id)
    return render(request, "biolib/collection_create.html")

@login_required
def collection_detail(request, collection_id):
    collection = get_object_or_404(PlasmidCollection, id=collection_id)
    return render(request, "biolib/collection_detail.html", {"collection": collection, "is_owner": collection.owner == request.user})

@login_required
def plasmid_upload(request, collection_id):
    collection = get_object_or_404(PlasmidCollection, id=collection_id, owner=request.user)
    if request.method == "POST":
        for f in request.FILES.getlist("files"):
            Plasmid.objects.create(collection=collection, identifier=f.name, name="", genbank_file=f, sequence="")
        return redirect("collection_detail", collection.id)
    return render(request, "biolib/plasmid_upload.html", {"collection": collection})

@login_required
def plasmid_delete(request, plasmid_id):
    plasmid = get_object_or_404(Plasmid, id=plasmid_id, collection__owner=request.user)
    if request.method == "POST":
        col_id = plasmid.collection.id
        plasmid.delete()
        return redirect("collection_detail", col_id)

@login_required
def collection_delete(request, collection_id):
    collection = get_object_or_404(PlasmidCollection, id=collection_id, owner=request.user)
    if request.method == "POST":
        collection.delete()
        return redirect("collections")

@login_required
def correspondences_view(request):
    return render(request, "biolib/correspondences.html", {"correspondences": Correspondence.objects.filter(owner=request.user)})

@login_required
def correspondence_upload(request):
    if request.method == "POST":
        Correspondence.objects.create(name=request.POST["name"], file=request.FILES["file"], owner=request.user)
        return redirect("correspondences")
    return render(request, "biolib/correspondence_upload.html")

@login_required
def correspondence_detail(request, correspondence_id):
    return render(request, "biolib/correspondence_detail.html", {"table": get_object_or_404(Correspondence, id=correspondence_id, owner=request.user)})

@login_required
def correspondence_delete(request, correspondence_id):
    table = get_object_or_404(Correspondence, id=correspondence_id, owner=request.user)
    if request.method == "POST":
        table.delete()
        return redirect("correspondences")

@login_required
def correspondence_view_file(request, correspondence_id):
    table = get_object_or_404(Correspondence, id=correspondence_id, owner=request.user)
    try:
        with open(table.file.path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        content = "Erreur lecture."
    return render(request, "biolib/correspondence_view_file.html", {"table": table, "content": content})
