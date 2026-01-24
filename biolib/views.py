# biolib/views.py
from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime
from .forms import CustomUserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse, Http404
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db.models import Q 
from .forms import SimulationForm
from .models import Simulation
from types import SimpleNamespace
import traceback
import glob
import os
import pathlib
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from .forms import CampaignTemplateForm, TemplatePartFormSet
from .models import CampaignTemplate, Plasmid, Team, User

import insillyclo.data_source
try:
    import insillyclo.observer
    BaseObserver = insillyclo.observer.InSillyCloObserver
except ImportError:
    class BaseObserver: pass
import insillyclo.simulator


def home(request):
    return render(request, 'biolib/home.html')

def template(request):
    if request.user.is_authenticated:
        # Si connecté : nos templates + ceux de l'équipe + publics
        templates = CampaignTemplate.objects.filter(
            Q(owner=request.user) | 
            Q(visibility='team') | 
            Q(visibility='public')
        ).distinct().order_by('-id')
    else:
        # Si invité : ceux de la session + publics
        anon_ids = request.session.get('anon_templates', [])
        templates = CampaignTemplate.objects.filter(
            Q(id__in=anon_ids) |
            Q(visibility='public')
        ).distinct().order_by('-id')

    return render(request, 'biolib/template.html', {'templates': templates})


def create_template(request):

    if request.method == 'POST':
        form = CampaignTemplateForm(request.POST, request.FILES)
        formset = TemplatePartFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            template = form.save(commit=False)

            if request.user.is_authenticated:
                template.owner = request.user
            else:
                template.owner = None
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
        # Affichage du formulaire vide
        form = CampaignTemplateForm()
        formset = TemplatePartFormSet()

    # On envoie les formulaires au bon fichier HTML
    return render(request, 'biolib/create_template.html', {
        'form': form,
        'formset': formset
    })

def simulation(request):
    return render(request, 'biolib/simulation.html')

def simulation_result(request):
    return render(request, 'biolib/simulation_result.html')

def template_detail(request):
    return render(request, 'biolib/template_detail.html')

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


# DASHBOARD

@login_required
def dashboard(request):
    teams_count = Team.objects.filter(
        Q(leader=request.user) | Q(members=request.user)
    ).distinct().count()

    return render(request, 'biolib/dashboard.html', {
        'teams_count': teams_count
    })


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

    # Assembly Settings
    ws['A1'] = "Assembly settings"; ws['A1'].font = bold_font; ws['A1'].fill = blue_fill
    ws['A2'] = "Restriction enzyme"; ws['A2'].font = bold_font; ws['A2'].fill = blue_fill
    ws['B2'] = template.enzyme; ws['B2'].fill = green_fill
    ws['A3'] = "Name"; ws['A3'].font = bold_font; ws['A3'].fill = blue_fill
    ws['B3'] = template.name; ws['B3'].fill = green_fill
    ws['A4'] = "Output separator"; ws['A4'].font = bold_font; ws['A4'].fill = blue_fill
    ws['B4'] = template.output_separator; ws['B4'].fill = green_fill

    # Assembly Composition
    base_row = 8
    headers = [
        "Assembly composition", "Part types ->", "Is optional part ->",
        "Part name should be in output name ->", "Output plasmid id ↓"
    ]
    for i, text in enumerate(headers):
        cell = ws.cell(row=base_row + i, column=1, value=text)
        cell.font = bold_font; cell.fill = blue_fill

    for index, part in enumerate(parts):
        col_num = 2 + index
        c1 = ws.cell(row=base_row, column=col_num, value=part.name); c1.fill = green_fill; c1.alignment = center_align
        c2 = ws.cell(row=base_row + 1, column=col_num, value=part.type_id); c2.fill = green_fill; c2.alignment = center_align
        
        is_optional_str = "False" if part.is_mandatory else "True"
        c3 = ws.cell(row=base_row + 2, column=col_num, value=is_optional_str); c3.fill = green_fill; c3.alignment = center_align
        
        in_output_str = "True" if part.include_in_output else "False"
        c4 = ws.cell(row=base_row + 3, column=col_num, value=in_output_str); c4.fill = green_fill; c4.alignment = center_align
        
        c5 = ws.cell(row=base_row + 4, column=col_num, value="↓"); c5.fill = blue_fill; c5.alignment = center_align

    ws.column_dimensions['A'].width = 35
    for col in range(2, 2 + len(parts)):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 20

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    clean_name = template.name.replace(" ", "_")
    response['Content-Disposition'] = f'attachment; filename="Campaign_{clean_name}.xlsx"'
    wb.save(response)
    return response

try:
    from my_insillyclo.simulator import compute_all
except ImportError:
    print("ATTENTION : my_insillyclo.simulator non trouvé.")
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

@login_required
def simulation_list(request):
    simulations = Simulation.objects.filter(user=request.user).order_by('-date_run')
    return render(request, 'biolib/simulation_list.html', {'simulations': simulations})

@login_required
def create_simulation(request):
    if request.method == 'POST':
        form = SimulationForm(request.POST, request.FILES)
        if form.is_valid():
            simulation = form.save(commit=False)
            simulation.user = request.user
            simulation.status = 'RUNNING'
            simulation.save()

            output_folder = os.path.join(settings.MEDIA_ROOT, 'simulations', str(simulation.id))
            path_xlsx = simulation.template_file.path
            path_csv_list = [simulation.campaign_file.path] if simulation.campaign_file else []
            
            gb_plasmids_paths = []
            all_parts = Plasmid.objects.all()
            for p in all_parts:
                if p.genbank_file: 
                    file_path = p.genbank_file.path
                    if os.path.exists(file_path):
                        gb_plasmids_paths.append(file_path)

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
                    enzyme_names=simulation.enzyme,
                    default_mass_concentration=200
                )
                simulation.status = 'COMPLETED'
                if os.path.exists(os.path.join(output_folder, 'digestion.svg')):
                      simulation.result_file = f"simulations/{simulation.id}/digestion.svg"
                elif os.path.exists(os.path.join(output_folder, 'dilutions_calculated.csv')):
                      simulation.result_file = f"simulations/{simulation.id}/dilutions_calculated.csv"
                simulation.save()
                return redirect('simulation_result', pk=simulation.id)

            except Exception as e:
                print("\n!!! ERREUR INSILLYCLO !!!")
                traceback.print_exc()
                simulation.status = 'FAILED'
                simulation.save()
                return redirect('simulation_list')
    else:
        form = SimulationForm()
    return render(request, 'biolib/create_simulation.html', {'form': form})

def simulation_result(request, pk=None):
    if pk is not None:
        simulation = get_object_or_404(Simulation, pk=pk, user=request.user)
    else:
        simulation = SimpleNamespace(id=0, status='COMPLETED', date_run=datetime.now(), template=SimpleNamespace(name="DÉMO", enzyme="BsaI"), user=request.user)
    return render(request, 'biolib/simulation_result.html', {'simulation': simulation})

def download_simulation_csv(request, pk):
    simulation = get_object_or_404(Simulation, pk=pk)
    output_folder = os.path.join(settings.MEDIA_ROOT, 'simulations', str(pk))
    file_path = os.path.join(output_folder, 'dilutions_calculated.csv')
    if not os.path.exists(file_path): raise Http404("Fichier CSV introuvable")
    with open(file_path, 'rb') as fh:
        response = HttpResponse(fh.read(), content_type="text/csv")
        response['Content-Disposition'] = 'attachment; filename="dilutions.csv"'
        return response

def download_simulation_zip(request, pk):
    nom_dossier = f"simulation_{pk}"
    nom_fichier_zip = f"{nom_dossier}_archive.zip"
    chemin_complet = os.path.join(settings.BASE_DIR, 'simulation', nom_dossier, nom_fichier_zip)
    if os.path.exists(chemin_complet):
        response = FileResponse(open(chemin_complet, 'rb'), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{nom_fichier_zip}"'
        return response
    else:
        raise Http404(f"Fichier ZIP introuvable.")

#équipes
@login_required
def team_list(request):
    teams = Team.objects.filter(Q(leader=request.user) | Q(members=request.user)).distinct()
    return render(request, 'biolib/teams.html', {'teams': teams})

@login_required
def team_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            team = Team.objects.create(name=name, leader=request.user)
            team.members.add(request.user)
            return redirect('teams')
    return render(request, 'biolib/team_create.html')

@login_required
def team_detail(request, team_id):
    team = get_object_or_404(Team, id=team_id, members=request.user)
    return render(request, 'biolib/team_detail.html', {'team': team, 'is_leader': team.leader == request.user})

@login_required
def team_manage_members(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    if team.leader != request.user: return HttpResponse("Accès refusé", status=403)
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                team.members.add(user)
            except User.DoesNotExist: pass
    return render(request, 'biolib/team_manage_members.html', {'team': team})

@login_required
def team_remove_member(request, team_id, user_id):
    team = get_object_or_404(Team, id=team_id)
    if team.leader != request.user: return HttpResponse("Accès refusé", status=403)
    user = get_object_or_404(User, id=user_id)
    if user == team.leader: return HttpResponse("Impossible de retirer la cheffe", status=400)
    if request.method == 'POST': team.members.remove(user)
    return redirect('team_manage_members', team_id=team.id)

@login_required
def team_delete(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    if team.leader != request.user: return HttpResponse("Accès refusé", status=403)
    if request.method == 'POST':
        team.delete()
        return redirect('teams')
    return render(request, 'biolib/team_confirm_delete.html', {'team': team})
