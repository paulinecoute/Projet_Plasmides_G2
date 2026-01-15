# biolib/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage

import os
import pathlib

from .forms import CampaignTemplateForm, TemplatePartFormSet
from .models import CampaignTemplate

import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side


# import insillyclo.data_source
# import insillyclo.observer
# import insillyclo.simulator


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


