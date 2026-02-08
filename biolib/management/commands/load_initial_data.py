from django.core.management.base import BaseCommand
from biolib.models import User, CampaignTemplate, TemplatePart

class Command(BaseCommand):
    help = 'Crée UNIQUEMENT le Template_Example (3 inputs) manuellement.'

    def handle(self, *args, **kwargs):
        self.stdout.write("--- Création unique du Template_Example ---")

        # 1. Récupération de l'Admin (Propriétaire)
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR("ERREUR : Aucun administrateur trouvé. Créez un superuser d'abord."))
            return

        # 2. Nettoyage : On supprime l'ancien s'il existe pour éviter les doublons
        CampaignTemplate.objects.filter(name="Template_Example", owner=admin_user).delete()

        # 3. Création du Template avec les paramètres demandés
        template = CampaignTemplate.objects.create(
            name="Template_Example",
            owner=admin_user,
            description="Ceci est un exemple de Template vierge. Vous pouvez le modifier.",
            enzyme="BsaI",          # Laisser par défaut
            output_separator="-",   # Laisser par défaut
            visibility="public",    # Public
            is_public=True
        )

        # 4. Création des 3 parties (input Plasmid 1 à 3)
        # - Optionnel = True (donc is_mandatory=False)
        # - Inclus = True
        for i in range(1, 4): # Boucle de 1 à 3
            TemplatePart.objects.create(
                template=template,
                name=f"input Plasmid {i}",  # Nom exact demandé
                type_id="1",                # Type par défaut
                order=i,
                is_mandatory=False,         # Optionnel
                include_in_output=True,     # Inclus dans le nom
                is_separable=False
            )

        self.stdout.write(self.style.SUCCESS(f"OK : Template 'Template_Example' créé avec 3 parties (input Plasmid 1 à 3)."))
