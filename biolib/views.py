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
from .models import CampaignTemplate, Plasmid, Team, User # Ajout Team/User ici pour être propre

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
        templates = CampaignTemplate.objects.filter(
            Q(owner=request.user) | 
            Q(visibility='team') | 
            Q(visibility='public')
        ).distinct().order_by('-id')
    else:
        anon_ids = request.session.get('anon_templates', [])
        templates = CampaignTemplate.objects.filter(
            Q(id__in=anon_ids) |
            Q(visibility='public')
        ).distinct().order_by('-id')

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
                template.owner = None
                template.visibility = 'private' # On force en privé pour ne pas polluer le public

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

    for index, part in enumerate(parts):
        col_num = 2 + index # Colonne B = 2

        c1 = ws.cell(row=base_row, column=col_num, value=part.name)
        c1.fill = green_fill
        c1.alignment = center_align

        c2 = ws.cell(row=base_row + 1, column=col_num, value=part.type_id)
        c2.fill = green_fill
        c2.alignment = center_align

        is_optional_str = "False" if part.is_mandatory else "True"
        c3 = ws.cell(row=base_row + 2, column=col_num, value=is_optional_str)
        c3.fill = green_fill
        c3.alignment = center_align

        in_output_str = "True" if part.include_in_output else "False"
        c4 = ws.cell(row=base_row + 3, column=col_num, value=in_output_str)
        c4.fill = green_fill
        c4.alignment = center_align

        c5 = ws.cell(row=base_row + 4, column=col_num, value="↓")
        c5.fill = blue_fill
        c5.alignment = center_align

    ws.column_dimensions['A'].width = 35
    for col in range(2, 2 + len(parts)):
        col_letter = openpyxl.utils.get_column_letter(col)
        ws.column_dimensions[col_letter].width = 20

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
        #
