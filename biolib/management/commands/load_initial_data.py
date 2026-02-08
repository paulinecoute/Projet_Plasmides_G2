import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
from django.contrib.auth import get_user_model
from biolib.models import Plasmid, PlasmidCollection, CampaignTemplate
from Bio import SeqIO  # Import indispensable pour lire le GenBank proprement

User = get_user_model()

class Command(BaseCommand):
    help = 'Charge les plasmides et les templates récursivement depuis le dossier data_web (avec BioPython)'

    def handle(self, *args, **kwargs):
        data_dir = os.path.join(settings.BASE_DIR, 'data_web')

        self.stdout.write("--- Démarrage de l'import Récursif ---")

        if not os.path.exists(data_dir):
            self.stdout.write(self.style.ERROR(f"ERREUR : '{data_dir}' n'existe pas !"))
            return

        admin_user = User.objects.filter(is_superuser=True).first()

        count_plasmids = 0
        count_templates = 0

        for root, dirs, files in os.walk(data_dir):
            folder_name = os.path.basename(root)
            collection = None

            # 1. Gestion des Collections (par dossier)
            if folder_name != 'data_web':
                collection_name = f"Collection {folder_name}"

                # On crée ou récupère la collection publique
                collection, created = PlasmidCollection.objects.get_or_create(
                    name=collection_name,
                    defaults={
                        'owner': admin_user,
                        'publication_status': 'approved',
                        'description': f"Import automatique du dossier {folder_name}"
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f" > Collection créée : {collection_name}"))
            else:
                self.stdout.write(f" > Racine '{folder_name}' : Pas de collection créée.")


            # 2. Filtrage des fichiers valides
            valid_files = [f for f in files if f.lower().endswith(('.gb', '.dna', '.fasta', '.xlsx'))]
            if not valid_files:
                continue

            for filename in valid_files:
                file_path = os.path.join(root, filename)
                identifier = os.path.splitext(filename)[0]

                # --- CAS A : IMPORT DES TEMPLATES (XLSX) ---
                if filename.lower().endswith('.xlsx'):
                    try:
                        template = CampaignTemplate.objects.filter(name=identifier, owner=admin_user).first()
                        action_tpl = ""

                        if template:
                            action_tpl = "Updated"
                        else:
                            action_tpl = "Created"
                            template = CampaignTemplate(
                                name=identifier,
                                owner=admin_user,
                                description="Template importé",
                                visibility='public',
                                is_public=True
                            )

                        # Sauvegarde du fichier Excel
                        with open(file_path, 'rb') as f_byte:
                            template.file.save(filename, File(f_byte), save=True)

                        count_templates += 1
                        self.stdout.write(f"   # Template {action_tpl} : {filename}")

                    except Exception as e:
                         self.stdout.write(self.style.ERROR(f"Erreur Template {filename}: {e}"))

                    continue # On passe au fichier suivant (car c'était un Excel)


                # --- CAS B : IMPORT DES PLASMIDES (.gb, .dna, .fasta) ---
                try:
                    # >>> CORRECTION BIOPYTHON ICI <<<
                    # Au lieu de lire le texte brut, on extrait la vraie séquence
                    seq_str = ""
                    plasmid_name_internal = identifier

                    if filename.lower().endswith(('.gb', '.gbk')):
                        try:
                            record = SeqIO.read(file_path, "genbank")
                            seq_str = str(record.seq).upper()
                            if record.name and record.name != "<unknown name>":
                                plasmid_name_internal = record.name
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f"   ! Lecture BioPython échouée pour {filename}, lecture brute utilisée."))
                            # Fallback lecture brute si BioPython échoue
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                seq_str = f.read()

                    else:
                        # Pour .fasta ou .dna, lecture simple (ou BioPython fasta)
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            seq_str = f.read()

                    # Création ou Mise à jour
                    plasmid = Plasmid.objects.filter(identifier=identifier).first()
                    action = ""

                    if plasmid:
                        action = "Updated"
                        plasmid.name = plasmid_name_internal
                        plasmid.sequence = seq_str  # Mise à jour avec la séquence extraite
                        plasmid.save()
                    else:
                        action = "Created"
                        plasmid = Plasmid.objects.create(
                            identifier=identifier,
                            name=plasmid_name_internal,
                            sequence=seq_str  # Sauvegarde de la séquence
                        )

                    # Sauvegarde du fichier physique
                    with open(file_path, 'rb') as f_byte:
                        plasmid.genbank_file.save(filename, File(f_byte), save=False)
                        plasmid.save()

                    # Liaison à la collection
                    if collection:
                        plasmid.collections.add(collection)
                        collection_msg = f"(dans {collection.name})"
                    else:
                        collection_msg = "(Sans collection)"

                    if action == "Created":
                        self.stdout.write(f"   + Plasmide {filename} {collection_msg} [{len(seq_str)} pb]")
                    else:
                        self.stdout.write(f"   ~ Plasmide MAJ {filename} {collection_msg}")

                    count_plasmids += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Erreur Plasmide {filename}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"--- FINI : {count_plasmids} plasmides traités, {count_templates} templates xlsx importés ---"))
