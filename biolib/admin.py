from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Team,
    PlasmidCollection, Plasmid,
    Correspondence, CorrespondenceEntry,
    CampaignTemplate, TemplatePart,
    Simulation
)

# ==============================================================================
# GESTION UTILISATEURS & EQUIPES (Base AGASH)
# ==============================================================================

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """ Gestion des utilisateurs personnalisés avec rôles """
    list_display = ('email', 'username', 'role', 'is_staff', 'is_active')
    ordering = ('email',)
    list_filter = ('role', 'is_staff')

    # Configuration des champs affichés dans le formulaire d'édition
    fieldsets = UserAdmin.fieldsets + (
        ('Informations Complémentaires', {'fields': ('role',)}),
    )

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'leader')
    search_fields = ('name', 'leader__email')
    # Permet une interface à deux colonnes pour sélectionner les membres (très pratique)
    filter_horizontal = ('members',)

# ==============================================================================
# BIOLOGIE & PLASMIDES (Fusion)
# ==============================================================================

@admin.register(PlasmidCollection)
class PlasmidCollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'team', 'is_public')
    list_filter = ('is_public', 'team')
    search_fields = ('name', 'description')

@admin.register(Plasmid)
class PlasmidAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'name', 'collection')
    list_filter = ('collection',)
    search_fields = ('identifier', 'name', 'sequence')

# ==============================================================================
# CORRESPONDANCE (Structure MAIN + UX AGASH)
# ==============================================================================

# Permet de voir les entrées directement dans la page de la Correspondance
class CorrespondenceEntryInline(admin.TabularInline):
    model = CorrespondenceEntry
    extra = 0 # N'affiche pas de lignes vides par défaut
    can_delete = True

@admin.register(Correspondence)
class CorrespondenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'uploaded_at')
    inlines = [CorrespondenceEntryInline] # Liaison Parent-Enfant

@admin.register(CorrespondenceEntry)
class CorrespondenceEntryAdmin(admin.ModelAdmin):
    """ Utile pour faire des recherches précises sur un ID """
    list_display = ('id_in_file', 'name', 'type', 'correspondence')
    search_fields = ('id_in_file', 'name')
    list_filter = ('correspondence',)

# ==============================================================================
# TEMPLATES & SIMULATIONS (Le cœur du système)
# ==============================================================================

# Permet d'éditer les parties (Parts) directement dans le Template
class TemplatePartInline(admin.TabularInline):
    model = TemplatePart
    extra = 1
    classes = ['collapse'] # Permet de replier cette section si elle est longue

@admin.register(CampaignTemplate)
class CampaignTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'enzyme', 'output_separator', 'is_public')
    list_filter = ('enzyme', 'is_public', 'owner')
    search_fields = ('name', 'description')
    inlines = [TemplatePartInline] # Liaison Parent-Enfant indispensable pour MAIN

@admin.register(Simulation)
class SimulationAdmin(admin.ModelAdmin):
    list_display = ('template', 'user', 'status', 'date_run')
    list_filter = ('status', 'date_run')
    search_fields = ('user__email', 'template__name')
