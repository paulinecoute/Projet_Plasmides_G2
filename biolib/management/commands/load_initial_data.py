import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
from biolib.models import Plasmid, PlasmidCollection, User, CampaignTemplate

class Command(BaseCommand):
    help = 'Charge les plasmides et les templates récursivement depuis le dossier data_web'

    def handle(self, *args, **kwargs):
        data_dir = os.path.join(settings.BASE_DIR, 'data_web')

        self.stdout.write("--- Démarrage de l'import Récursif ---")

        if not os.path.exists(data_dir):
            self.stdout.write(self.style.ERROR(f"ERREUR : '{data_dir}' n'existe pas !"))
            return

        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR("Erreur : Aucun administrateur trouvé."))
            return

        count_plasmids = 0
        count_templates = 0

        for root, dirs, files in os.walk(data_dir):
            folder_name = os.path.basename(root)

            # --- 1. GESTION DE LA COLLECTION ---
            collection = None

            # On ne crée une collection QUE si on n'est PAS à la racine
            if folder_name != 'data_web':
                collection_name = f"Collection {folder_name}"

                # Création/Récupération de la collection
                collection, created = PlasmidCollection.objects.get_or_create(
                    name=collection_name,
                    defaults={'owner': admin_user}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f" > Collection créée : {collection_name}"))
            else:
                self.stdout.write(f" > Racine '{folder_name}' : Pas de collection créée.")


            # --- 2. FILTRAGE DES FICHIERS ---
            valid_files = [f for f in files if f.lower().endswith(('.gb', '.dna', '.fasta', '.xlsx'))]
            if not valid_files:
                continue

            for filename in valid_files:
                file_path = os.path.join(root, filename)
                identifier = os.path.splitext(filename)[0]

                # ==========================================================
                # BRANCHE A : C'EST UN TEMPLATE EXCEL (.xlsx)
                # ==========================================================
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
                                description=f"Importé automatiquement depuis {folder_name}",
                                visibility='public',
                                is_public=True
                            )

                        with open(file_path, 'rb') as f_byte:
                            template.file.save(filename, File(f_byte), save=True)

                        count_templates += 1
                        self.stdout.write(f"   # Template {action_tpl} : {filename}")

                    except Exception as e:
                         self.stdout.write(self.style.ERROR(f"Erreur Template {filename}: {e}"))

                    continue

                # ==========================================================
                # BRANCHE B : C'EST UN PLASMIDE (.gb, .dna, etc.)
                # ==========================================================
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f_read:
                        content_seq = f_read.read()

                    plasmid = Plasmid.objects.filter(identifier=identifier).first()

                    if plasmid:
                        action = "Updated"
                        plasmid.name = identifier
                        plasmid.sequence = content_seq[:200] + "..."
                    else:
                        action = "Created"
                        plasmid = Plasmid(
                            identifier=identifier,
                            name=identifier,
                            sequence=content_seq[:200] + "..."
                        )

                    with open(file_path, 'rb') as f_byte:
                        plasmid.genbank_file.save(filename, File(f_byte), save=True)

                    # IMPORTANT : On ajoute à la collection SEULEMENT si elle existe (pas à la racine)
                    if collection:
                        plasmid.collections.add(collection)
                        collection_msg = f"(dans {collection.name})"
                    else:
                        collection_msg = "(Sans collection)"

                    if action == "Created":
                        count_plasmids += 1
                        self.stdout.write(f"   + Plasmide {filename} {collection_msg}")
                    else:
                        count_plasmids += 1
                        self.stdout.write(f"   ~ Plasmide {filename} {collection_msg}")

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Erreur Plasmide {filename}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"--- FINI : {count_plasmids} plasmides traités, {count_templates} templates xlsx importés ---"))
