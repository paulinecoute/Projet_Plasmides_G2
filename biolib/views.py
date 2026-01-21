# biolib/views.py
from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime
from .forms import CustomUserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import Http404
from .forms import SimulationForm
from .models import Simulation
from types import SimpleNamespace

import os
import pathlib

from .forms import CampaignTemplateForm, TemplatePartFormSet
from .models import CampaignTemplate

import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side


#import insillyclo.data_source
#import insillyclo.observer
#import insillyclo.simulator


def home(request):
    return render(request, 'biolib/home.html')

def template(request):
    templates = CampaignTemplate.objects.order_by('-id') # ceux créés récemment apparaissent en haut
    return render(request, 'biolib/template.html', {'templates': templates})

def create_template(request):
    return render(request, 'biolib/create_template.html')

def template_create_view(request):

    if request.method == 'POST':
        form = CampaignTemplateForm(request.POST, request.FILES)
        formset = TemplatePartFormSet(request.POST)

        if form.is_valid() and formset.is_valid():

            template = form.save(commit=False)

            if request.user.is_authenticated:
                template.owner = request.user
            else:
                # si pas connecté : forcément privé
                template.owner = None
                template.visibility = 'private'

            template.save()

            parts = formset.save(commit=False)
            for part in parts:
                part.template = template
                part.save()

            return redirect('template')
    else:
        form = CampaignTemplateForm()
        formset = TemplatePartFormSet()

    return render(request, 'biolib/template_form.html', {
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


# ESPACE PERSONNEL (DASHBOARD)

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

    # Titre
    ws['A1'] = "Assembly settings"
    ws['A1'].font = bold_font
    ws['A1'].fill = blue_fill

    # Enzyme
    ws['A2'] = "Restriction enzyme"
    ws['A2'].font = bold_font
    ws['A2'].fill = blue_fill
    ws['B2'] = template.enzyme
    ws['B2'].fill = green_fill

    # Nom
    ws['A3'] = "Name"
    ws['A3'].font = bold_font
    ws['A3'].fill = blue_fill
    ws['B3'] = template.name
    ws['B3'].fill = green_fill

    # Séparateur
    ws['A4'] = "Output separator"
    ws['A4'].font = bold_font
    ws['A4'].fill = blue_fill
    ws['B4'] = template.output_separator
    ws['B4'].fill = green_fill

    # Assembly Composition
    base_row = 8

    headers = [
        "Assembly composition",
        "Part types ->",
        "Is optional part ->",
        "Part name should be in output name ->",
        "Output plasmid id ↓"
    ]

    for i, text in enumerate(headers):
        cell = ws.cell(row=base_row + i, column=1, value=text)
        cell.font = bold_font
        cell.fill = blue_fill

    # Boucle pour créer les colonnes (B, C, D...) selon tes parties
    for index, part in enumerate(parts):
        col_num = 2 + index # Colonne B = 2

        # 1. Nom de la partie (ex: Promoter)
        c1 = ws.cell(row=base_row, column=col_num, value=part.name)
        c1.fill = green_fill
        c1.alignment = center_align

        # 2. Type ID (ex: 1)
        c2 = ws.cell(row=base_row + 1, column=col_num, value=part.type_id)
        c2.fill = green_fill
        c2.alignment = center_align

        # 3. Est optionnel ? (Logique inversée : Mandatory=True -> Optional=False)
        is_optional_str = "False" if part.is_mandatory else "True"
        c3 = ws.cell(row=base_row + 2, column=col_num, value=is_optional_str)
        c3.fill = green_fill
        c3.alignment = center_align

        # 4. Dans le nom ? (Ta nouvelle case à cocher)
        in_output_str = "True" if part.include_in_output else "False"
        c4 = ws.cell(row=base_row + 3, column=col_num, value=in_output_str)
        c4.fill = green_fill
        c4.alignment = center_align

        # 5. La petite flèche du bas
        c5 = ws.cell(row=base_row + 4, column=col_num, value="↓")
        c5.fill = blue_fill
        c5.alignment = center_align

    # Ajustement automatique des largeurs
    ws.column_dimensions['A'].width = 35
    for col in range(2, 2 + len(parts)):
        col_letter = openpyxl.utils.get_column_letter(col)
        ws.column_dimensions[col_letter].width = 20

    # Envoi du fichier au navigateur
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    clean_name = template.name.replace(" ", "_")
    response['Content-Disposition'] = f'attachment; filename="Campaign_{clean_name}.xlsx"'

    wb.save(response)
    return response



# Import de votre script de simulation
try:
    from my_insillyclo.simulator import compute_all
except ImportError:
    print("ATTENTION : my_insillyclo.simulator non trouvé.")
    def compute_all(*args, **kwargs): pass

# Observateur simple pour les logs
class ConsoleObserver:
    def notify_message(self, message):
        print(f"[SIMULATION] {message}")
    def notify_progress(self, value):
        pass

# ==============================================================================
# 1. LISTE DES SIMULATIONS (C'est celle-ci qui vous manquait !)
# ==============================================================================
def simulation_list(request):
    """ Affiche le tableau de toutes les simulations de l'utilisateur """
    simulations = Simulation.objects.filter(user=request.user).order_by('-date_run')
    return render(request, 'biolib/simulation_list.html', {'simulations': simulations})

# ==============================================================================
# 2. CRÉATION D'UNE SIMULATION
# ==============================================================================
def create_simulation(request):
    """ Gère le formulaire et lance le script de simulation """
    if request.method == 'POST':
        form = SimulationForm(request.POST)

        if form.is_valid():
            # A. Création en base
            simulation = form.save(commit=False)
            simulation.user = request.user
            simulation.status = 'RUNNING'
            simulation.save()

            # B. Dossiers
            output_folder = os.path.join(settings.MEDIA_ROOT, 'simulations', str(simulation.id))
            template = simulation.template
            gb_plasmids = []

            # C. Lancement du script
            try:
                observer = ConsoleObserver()
                print(f"Lancement de la simulation #{simulation.id}...")

                compute_all(
                    observer=observer,
                    settings=None,
                    input_template_filled=template.file.path if template.file else "No_File",
                    input_parts_files=[],
                    gb_plasmids=gb_plasmids,
                    output_dir=output_folder,
                    data_source="Django",
                    enzyme_names=template.enzyme
                )

                # D. Succès
                simulation.status = 'COMPLETED'
                simulation.result_file = f"simulations/{simulation.id}/simulated_gel.png"
                simulation.save()

                return redirect('simulation_result', pk=simulation.id)

            except Exception as e:
                print(f"ERREUR PENDANT LA SIMULATION : {e}")
                simulation.status = 'FAILED'
                simulation.save()
                return redirect('simulation_list')

    else:
        form = SimulationForm()

    return render(request, 'biolib/create_simulation.html', {'form': form})

# ==============================================================================
# 3. RÉSULTAT D'UNE SIMULATION
# ==============================================================================
def simulation_result(request, pk=None):
    """ Affiche les résultats (pk=None permet l'affichage démo) """

    if pk is not None:
        # Vraie simulation
        simulation = get_object_or_404(Simulation, pk=pk, user=request.user)
    else:
        # Démo (Objet factice)
        simulation = SimpleNamespace(
            id=0,
            status='COMPLETED',
            date_run=datetime.now(),
            template=SimpleNamespace(name="DÉMO - Simulation Publique", enzyme="BsaI"),
            user=request.user
        )

    return render(request, 'biolib/simulation_result.html', {
        'simulation': simulation
    })

def download_simulation_csv(request, pk):
    """ Permet de télécharger le fichier CSV de dilutions de manière sécurisée """
    # 1. On vérifie que la simulation appartient bien à l'utilisateur
    simulation = get_object_or_404(Simulation, pk=pk, user=request.user)

    # 2. On construit le chemin du fichier
    file_path = os.path.join(settings.MEDIA_ROOT, 'simulations', str(simulation.id), 'dilutions_calculated.csv')

    # 3. On vérifie si le fichier existe physiquement
    if os.path.exists(file_path):
        # On renvoie le fichier en forçant le téléchargement (as_attachment=True)
        response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=f"Dilutions_Simulation_{simulation.id}.csv")
        return response
    else:
        raise Http404("Le fichier CSV n'a pas été trouvé sur le serveur.")

# ==============================================================================
# GESTION DES ÉQUIPES
# ==============================================================================

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Q

from .models import Team, User


@login_required
def team_list(request):
    """
    Page : Mes équipes
    Affiche toutes les équipes dont l'utilisateur est membre ou cheffe.
    """
    teams = Team.objects.filter(
        Q(leader=request.user) | Q(members=request.user)
    ).distinct()

    return render(request, 'biolib/teams.html', {
        'teams': teams
    })


@login_required
def team_create(request):
    """
    Page : Créer une équipe
    """
    if request.method == 'POST':
        name = request.POST.get('name')

        if name:
            team = Team.objects.create(
                name=name,
                leader=request.user
            )
            team.members.add(request.user)
            return redirect('teams')

    return render(request, 'biolib/team_create.html')


@login_required
def team_detail(request, team_id):
    """
    Page : Détail d'une équipe
    Accessible uniquement aux membres.
    """
    team = get_object_or_404(
        Team,
        id=team_id,
        members=request.user
    )

    is_leader = team.leader == request.user

    return render(request, 'biolib/team_detail.html', {
        'team': team,
        'is_leader': is_leader
    })


@login_required
def team_manage_members(request, team_id):
    """
    Page : Gestion des membres d'une équipe
    Accessible uniquement à la cheffe.
    """
    team = get_object_or_404(Team, id=team_id)

    if team.leader != request.user:
        return HttpResponse("Accès refusé", status=403)

    if request.method == 'POST':
        email = request.POST.get('email')

        if email:
            try:
                user = User.objects.get(email=email)
                team.members.add(user)
            except User.DoesNotExist:
                pass

    return render(request, 'biolib/team_manage_members.html', {
        'team': team
    })


@login_required
def team_remove_member(request, team_id, user_id):
    """
    Retirer un membre d'une équipe (cheffe uniquement).
    """
    team = get_object_or_404(Team, id=team_id)

    if team.leader != request.user:
        return HttpResponse("Accès refusé", status=403)

    user = get_object_or_404(User, id=user_id)

    if user == team.leader:
        return HttpResponse("Impossible de retirer la cheffe", status=400)

    if request.method == 'POST':
        team.members.remove(user)

    return redirect('team_manage_members', team_id=team.id)


@login_required
def team_delete(request, team_id):
    """
    Supprimer une équipe (cheffe uniquement).
    """
    team = get_object_or_404(Team, id=team_id)

    if team.leader != request.user:
        return HttpResponse("Accès refusé", status=403)

    if request.method == 'POST':
        team.delete()
        return redirect('teams')

    return render(request, 'biolib/team_confirm_delete.html', {
        'team': team
    })
