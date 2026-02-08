import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
from biolib.models import User, CampaignTemplate, TemplatePart, PublicCampaign

class Command(BaseCommand):
    help = 'Crée le Template_Example et charge UNIQUEMENT Campaign_Venus et Campaign_display_L1'

    def handle(self, *args, **kwargs):
        self.stdout.write("--- Démarrage de l'initialisation ---")

        # 1. Récupération de l'Admin (Propriétaire)
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR("ERREUR : Aucun administrateur trouvé."))
            return

        # ==================================================================
        # ETAPE 1 : CRÉATION DU "Template_Example" (Manuel, 3 inputs)
        # ==================================================================
        self.stdout.write(" > Création du Template_Example...")

        CampaignTemplate.objects.filter(name="Template_Example", owner=admin_user).delete()

        template = CampaignTemplate.objects.create(
            name="Template_Example",
            owner=admin_user,
            description="Ceci est un exemple de Template vierge. Vous pouvez le modifier.",
            enzyme="BsaI",
            output_separator="-",
            visibility="public",
            is_public=True
        )

        for i in range(1, 4): # Boucle de 1 à 3
            TemplatePart.objects.create(
                template=template,
                name=f"input Plasmid {i}",
                type_id="1",
                order=i,
                is_mandatory=False,
                include_in_output=True,
                is_separable=False
            )

        self.stdout.write(self.style.SUCCESS(f"   [OK] Template 'Template_Example' créé."))


        # ==================================================================
        # ETAPE 2 : CHARGEMENT DES 2 CAMPAGNES CIBLES
        # ==================================================================
        
        data_dir = os.path.join(settings.BASE_DIR, 'data_web')
        
        # LISTE STRICTE DES FICHIERS À IMPORTER
        target_files = [
            'Campaign_Venus.xlsx',
            'Campaign_display_L1.xlsx'
        ]

        if os.path.exists(data_dir):
            self.stdout.write(" > Chargement des fichiers spécifiques dans 'Campagnes Publiques'...")
            
            for filename in target_files:
                file_path = os.path.join(data_dir, filename)
                
                if os.path.exists(file_path):
                    try:
                        # 1. Nettoyage si existe déjà
                        PublicCampaign.objects.filter(name=filename).delete()

                        # 2. Création
                        campaign = PublicCampaign(
                            name=filename,
                            description=f"Fichier exemple : {filename}",
                            uploaded_by=admin_user
                        )

                        # 3. Attachement fichier
                        with open(file_path, 'rb') as f:
                            campaign.file.save(filename, File(f), save=True)
                        
                        self.stdout.write(f"   + Campagne ajoutée : {filename}")

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"   ! Erreur sur {filename}: {e}"))
                else:
                    self.stdout.write(self.style.WARNING(f"   ! Fichier introuvable dans data_web : {filename}"))

            self.stdout.write(self.style.SUCCESS(f"--- TERMINE ---"))
        
        else:
            self.stdout.write(self.style.WARNING(" > Dossier 'data_web' introuvable."))
