import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
from biolib.models import User, CampaignTemplate, TemplatePart, PublicCampaign, Correspondence

class Command(BaseCommand):
    help = 'Initialise : Template_Example, Campagnes Publiques (Venus, L1) et Tables de Correspondance (iP_mapping)'

    def handle(self, *args, **kwargs):
        self.stdout.write("--- Démarrage de l'initialisation ---")

        # 1. Récupération de l'Admin (Propriétaire)
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR("ERREUR : Aucun administrateur trouvé. Créez un superuser d'abord."))
            return

        data_dir = os.path.join(settings.BASE_DIR, 'data_web')
        if not os.path.exists(data_dir):
            self.stdout.write(self.style.WARNING(" > Dossier 'data_web' introuvable."))
            return

        # ==================================================================
        # ETAPE 1 : CRÉATION DU "Template_Example" (Manuel, 3 inputs)
        # ==================================================================
        self.stdout.write(" > 1. Création du Template_Example...")

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

        self.stdout.write(self.style.SUCCESS(f"   [OK] Template créé."))


        # ==================================================================
        # ETAPE 2 : CHARGEMENT DES CAMPAGNES PUBLIQUES (Excel)
        # ==================================================================
        self.stdout.write(" > 2. Chargement des Campagnes Publiques...")
        
        target_campaigns = [
            'Campaign_Venus.xlsx',
            'Campaign_display_L1.xlsx'
        ]

        for filename in target_campaigns:
            file_path = os.path.join(data_dir, filename)
            
            if os.path.exists(file_path):
                try:
                    PublicCampaign.objects.filter(name=filename).delete()

                    campaign = PublicCampaign(
                        name=filename,
                        description=f"Fichier exemple : {filename}",
                        uploaded_by=admin_user
                    )

                    with open(file_path, 'rb') as f:
                        campaign.file.save(filename, File(f), save=True)
                    
                    self.stdout.write(f"   + Campagne ajoutée : {filename}")

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"   ! Erreur sur {filename}: {e}"))
            else:
                self.stdout.write(self.style.WARNING(f"   ! Fichier introuvable : {filename}"))


        # ==================================================================
        # ETAPE 3 : CHARGEMENT DES TABLES DE CORRESPONDANCE (CSV)
        # ==================================================================
        self.stdout.write(" > 3. Chargement des Tables de Correspondance Publiques...")

        target_mappings = [
            'iP_mapping_typed.csv',
            'iP_mapping_Simple.csv'
        ]

        for filename in target_mappings:
            file_path = os.path.join(data_dir, filename)

            if os.path.exists(file_path):
                try:
                    # Nettoyage préalable
                    Correspondence.objects.filter(name=filename, owner=admin_user).delete()

                    # Création de l'objet Correspondence
                    mapping = Correspondence(
                        name=filename,
                        description=f"Table de mapping publique importée ({filename})",
                        owner=admin_user,
                        publication_status='approved',
                        team=None
                    )

                    # Attachement du fichier
                    with open(file_path, 'rb') as f:
                        mapping.file.save(filename, File(f), save=True)

                    self.stdout.write(f"   + Table ajoutée : {filename}")

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"   ! Erreur sur {filename}: {e}"))
            else:
                self.stdout.write(self.style.WARNING(f"   ! Fichier introuvable : {filename}"))

        self.stdout.write(self.style.SUCCESS(f"--- INITIALISATION TERMINÉE ---"))