# biolib/admin.py
from django.contrib import admin
from .models import Collection, Plasmid, Correspondence, CorrespondenceEntry, CampaignTemplate

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Plasmid)
class PlasmidAdmin(admin.ModelAdmin):
    list_display = ('name', 'collection')
    list_filter = ('collection',)
    search_fields = ('name',)

@admin.register(Correspondence)
class CorrespondenceAdmin(admin.ModelAdmin):
    list_display = ('file', 'uploaded_at')

@admin.register(CorrespondenceEntry)
class CorrespondenceEntryAdmin(admin.ModelAdmin):
    list_display = ('id_in_file', 'name', 'type', 'correspondence')
    list_filter = ('correspondence',)
    search_fields = ('id_in_file', 'name')

@admin.register(CampaignTemplate)
class CampaignTemplateAdmin(admin.ModelAdmin):
    list_display = ('file', 'uploaded_at')
