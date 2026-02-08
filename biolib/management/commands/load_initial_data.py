import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
from biolib.models import User, CampaignTemplate, TemplatePart, PublicCampaign, Correspondence, Plasmid, PlasmidCollection
from Bio import SeqIO

class Command(BaseCommand):
    help = 'Initialise : Template_Example, Campagnes Publiques, Tables de Correspondance et Collections Publiques (pYTK, pYS)'

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
        # ETAPE 1 : CRÉATION DU "Template_Example"
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

        for i in range(1, 4):
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

        target_campaigns = ['Campaign_Venus.xlsx', 'Campaign_display_L1.xlsx']

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

        target_mappings = ['iP_mapping_typed.csv', 'iP_mapping_Simple.csv']

        for filename in target_mappings:
            file_path = os.path.join(data_dir, filename)

            if os.path.exists(file_path):
                try:
                    Correspondence.objects.filter(name=filename, owner=admin_user).delete()
                    mapping = Correspondence(
                        name=filename,
                        description=f"Table de mapping publique importée ({filename})",
                        owner=admin_user,
                        publication_status='approved',
                        team=None
                    )
                    with open(file_path, 'rb') as f:
                        mapping.file.save(filename, File(f), save=True)
                    self.stdout.write(f"   + Table ajoutée : {filename}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"   ! Erreur sur {filename}: {e}"))
            else:
                self.stdout.write(self.style.WARNING(f"   ! Fichier introuvable : {filename}"))


        # ==================================================================
        # ETAPE 4 : CHARGEMENT DES COLLECTIONS DE PLASMIDES (pYTK, pYS)
        # ==================================================================
        self.stdout.write(" > 4. Chargement des Collections Publiques (pYTK, pYS)...")

        target_folders = ['pYTK', 'pYS']

        for folder_name in target_folders:
            folder_path = os.path.join(data_dir, folder_name)

            if not os.path.exists(folder_path):
                self.stdout.write(self.style.WARNING(f"   ! Dossier introuvable : {folder_name}"))
                continue

            # 1. Création de la Collection
            col_name = f"Collection {folder_name}"
            # Nettoyage si existe déjà pour éviter doublons
            PlasmidCollection.objects.filter(name=col_name, owner=admin_user).delete()

            collection = PlasmidCollection.objects.create(
                name=col_name,
                owner=admin_user,
                description=f"Collection publique importée automatiquement ({folder_name})",
                publication_status='approved' # Rends la collection publique
            )

            self.stdout.write(f"   > Collection créée : {col_name}")

            # 2. Parcours des fichiers .gb dans le dossier
            count_files = 0
            for filename in os.listdir(folder_path):
                if filename.lower().endswith(('.gb', '.gbk', '.dna', '.fasta')):
                    file_path = os.path.join(folder_path, filename)

                    try:
                        # Lecture de la séquence avec BioPython pour l'extraire
                        seq_str = ""
                        try:
                            record = SeqIO.read(file_path, "genbank")
                            seq_str = str(record.seq).upper()
                        except Exception:
                            # Fallback si lecture BioPython échoue ou si pas genbank
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                seq_str = f.read()

                        # Création du Plasmide
                        # On utilise get_or_create sur l'identifiant pour ne pas recréer le plasmide s'il existe déjà
                        # (par exemple s'il est utilisé ailleurs), mais on met à jour la séquence.
                        plasmid, created = Plasmid.objects.get_or_create(
                            identifier=filename,
                            defaults={
                                'name': filename,
                                'sequence': seq_str
                            }
                        )

                        # Si le plasmide existait déjà, on met à jour sa séquence au cas où
                        if not created:
                            plasmid.sequence = seq_str
                            plasmid.save()

                        # Attachement du fichier physique (Important pour la simulation)
                        with open(file_path, 'rb') as f:
                            plasmid.genbank_file.save(filename, File(f), save=False)
                            plasmid.save()

                        # Ajout à la collection
                        plasmid.collections.add(collection)
                        count_files += 1

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"     ! Erreur fichier {filename}: {e}"))

            self.stdout.write(f"     + {count_files} plasmides ajoutés dans {col_name}")

        self.stdout.write(self.style.SUCCESS(f"--- INITIALISATION TERMINÉE ---"))
