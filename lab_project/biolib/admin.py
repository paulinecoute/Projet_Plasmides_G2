from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Team, PlasmidCollection, Plasmid, CorrespondenceTable, CampaignTemplate, Simulation

# Gestion des utilisateurs
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'role', 'is_staff')
    ordering = ('email',)

# Gestion des équipes
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'leader')

# Collections de plasmides (Correction du nom ici)
@admin.register(PlasmidCollection)
class PlasmidCollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'team', 'is_public', 'created_at')
    search_fields = ('name',)
    list_filter = ('is_public', 'team')

# Plasmides individuels
@admin.register(Plasmid)
class PlasmidAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'name', 'collection', 'plasmid_type')
    list_filter = ('collection', 'plasmid_type')
    search_fields = ('identifier', 'name', 'sequence')

# Tables de correspondance (Correction du nom ici)
@admin.register(CorrespondenceTable)
class CorrespondenceTableAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'is_public')

# Templates de campagne
@admin.register(CampaignTemplate)
class CampaignTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'is_public', 'created_at')

# Historique des simulations
@admin.register(Simulation)
class SimulationAdmin(admin.ModelAdmin):
    list_display = ('template', 'user', 'status', 'date_run')
