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

from .forms import CampaignTemplateForm, TemplatePartFormSet
from .models import CampaignTemplate

# import insillyclo.data_source
# import insillyclo.observer
# import insillyclo.simulator


def home(request):
    return render(request, 'biolib/home.html')


def template(request):
    templates = CampaignTemplate.objects.all()
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
                # Si pas connecté : forcément privé
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
