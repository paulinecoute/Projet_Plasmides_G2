import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
from biolib.models import Plasmid, PlasmidCollection, User

class Command(BaseCommand):
    help = 'Charge les plasmides récursivement depuis le dossier data_web'

    def handle(self, *args, **kwargs):
        data_dir = os.path.join(settings.BASE_DIR, 'data_web')

        self.stdout.write("--- Démarrage de l'import Récursif ---")

        if not os.path.exists(data_dir):
            self.stdout.write(self.style.ERROR(f"ERREUR : '{data_dir}' n'existe pas !"))
            return

        # 1. On récupère l'admin
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR("Erreur : Aucun administrateur trouvé."))
            return

        count_success = 0
        count_updated = 0

        for root, dirs, files in os.walk(data_dir):
            folder_name = os.path.basename(root)

            # Nom de la collection basé sur le dossier
            if folder_name == 'data_web':
                collection_name = "Import Racine"
            else:
                collection_name = f"Collection {folder_name}"

            valid_files = [f for f in files if f.lower().endswith(('.gb', '.dna', '.fasta'))]
            if not valid_files:
                continue

            # 2. Création/Récupération Collection
            collection, created = PlasmidCollection.objects.get_or_create(
                name=collection_name,
                defaults={'owner': admin_user}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f" > Collection créée : {collection_name}"))

            # 3. Traitement des fichiers
            for filename in valid_files:
                file_path = os.path.join(root, filename)

                # On nettoie le nom (ex: pYTK001)
                identifier = os.path.splitext(filename)[0]

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f_read:
                        content_seq = f_read.read()

                    # On cherche si le plasmide existe déjà
                    plasmid = Plasmid.objects.filter(identifier=identifier).first()

                    if plasmid:
                        # CAS A : MISE À JOUR
                        action = "Updated"
                        plasmid.name = identifier
                        plasmid.sequence = content_seq[:200] + "..."
                        # On ne save() pas encore, on attend le fichier
                    else:
                        # CAS B : CRÉATION
                        action = "Created"
                        plasmid = Plasmid(
                            identifier=identifier,
                            name=identifier,
                            sequence=content_seq[:200] + "..."
                        )

                    # Gestion du fichier physique
                    with open(file_path, 'rb') as f_byte:
                        # CORRECTION : On passe juste 'filename' !
                        # Django utilisera son 'upload_to' défini dans le modèle pour le placer au bon endroit.
                        plasmid.genbank_file.save(filename, File(f_byte), save=True)

                    # Gestion Many-to-Many
                    # On l'ajoute à la collection du dossier en cours
                    plasmid.collections.add(collection)

                    if action == "Created":
                        count_success += 1
                        self.stdout.write(f"   + {filename} (Créé dans {collection_name})")
                    else:
                        count_updated += 1
                        self.stdout.write(f"   ~ {filename} (Mis à jour dans {collection_name})")

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Erreur sur {filename}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"--- FINI : {count_success} créés, {count_updated} mis à jour ---"))
