from django.contrib import admin
from .models import User, Team, PlasmidCollection, Plasmid, CampaignTemplate, Simulation, CorrespondenceTable


admin.site.register(User)
admin.site.register(Team)
admin.site.register(PlasmidCollection)
admin.site.register(Plasmid)
admin.site.register(CorrespondenceTable)
admin.site.register(CampaignTemplate)
admin.site.register(Simulation)
