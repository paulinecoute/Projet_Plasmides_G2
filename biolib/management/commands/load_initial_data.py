import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
from biolib.models import Plasmid, PlasmidCollection, User

class Command(BaseCommand):
    help = 'Charge les plasmides récursivement depuis le dossier data_web et ses sous-dossiers'

    def handle(self, *args, **kwargs):
        data_dir = os.path.join(settings.BASE_DIR, 'data_web')

        self.stdout.write(f"--- Démarrage de l'import Récursif ---")
        self.stdout.write(f"Racine de recherche : {data_dir}")

        if not os.path.exists(data_dir):
            self.stdout.write(self.style.ERROR(f"ERREUR : Le dossier '{data_dir}' n'existe pas !"))
            return

        # 1. On récupère l'administrateur
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR("Erreur : Aucun administrateur trouvé."))
            return

        # 2. On parcourt tout l'arbre de dossiers (os.walk)
        count_success = 0
        count_ignored = 0

        for root, dirs, files in os.walk(data_dir):
            # 'root' est le chemin du sous-dossier actuel (ex: .../data_web/pMISC)
            # On utilise le nom du sous-dossier comme nom de Collection !
            folder_name = os.path.basename(root)

            # Si on est à la racine 'data_web', on donne un nom générique
            if folder_name == 'data_web':
                collection_name = "Import Racine"
            else:
                collection_name = f"Collection {folder_name}"

            # On cherche les fichiers valides dans ce sous-dossier
            valid_files = [f for f in files if f.lower().endswith(('.gb', '.dna', '.fasta'))]

            if not valid_files:
                continue

            # 3. Création/Récupération de la collection pour ce sous-dossier
            collection, created = PlasmidCollection.objects.get_or_create(
                name=collection_name,
                defaults={'owner': admin_user}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f" > Nouvelle collection créée : {collection_name}"))

            # 4. Traitement des fichiers
            for filename in valid_files:
                file_path = os.path.join(root, filename)
                identifier = os.path.splitext(filename)[0]

                if Plasmid.objects.filter(identifier=identifier).exists():
                    count_ignored += 1
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f_read:
                        content = f_read.read()

                        plasmid = Plasmid(
                            collection=collection,
                            identifier=identifier,
                            name=identifier,
                            sequence=content[:200] + "..."
                        )

                        # Mode binaire pour le fichier
                        with open(file_path, 'rb') as f_byte:
                            plasmid.genbank_file.save(filename, File(f_byte), save=True)

                        count_success += 1
                        self.stdout.write(f"   + {filename} (dans {collection_name})")

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Erreur sur {filename}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"--- Bilan : {count_success} importés, {count_ignored} ignorés (déjà existants) ---"))
