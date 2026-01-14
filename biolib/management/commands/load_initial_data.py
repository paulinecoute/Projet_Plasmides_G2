# biolib/management/commands/load_initial_data.py
from django.core.management.base import BaseCommand
from biolib.models import Collection, Plasmid, Correspondence, CorrespondenceEntry, CampaignTemplate
import os
import csv
from Bio import SeqIO


class Command(BaseCommand):
    help = "Charge les données initiales depuis le dossier data_web/"

    def handle(self, *args, **options):
        data_dir = "data_web"
        if not os.path.exists(data_dir):
            self.stdout.write(self.style.ERROR(f"Le dossier {data_dir} n'existe pas !"))
            return

        # Exemple : Créer une collection par défaut
        collection, created = Collection.objects.get_or_create(name="Default Collection")
        self.stdout.write(self.style.SUCCESS(f"Collection '{collection.name}' {'créée' if created else 'existante'}"))

        # Charger les fichiers GenBank
        for genbank_file in [f for f in os.listdir(data_dir) if f.endswith(".gb")]:
            record = SeqIO.read(os.path.join(data_dir, genbank_file), "genbank")
            Plasmid.objects.create(
                name=genbank_file,
                sequence=str(record.seq),
                collection=collection
            )
            self.stdout.write(self.style.SUCCESS(f"Plasmide {genbank_file} chargé !"))

        # Charger les fichiers CSV
        for csv_file in [f for f in os.listdir(data_dir) if f.endswith(".csv")]:
            correspondence = Correspondence.objects.create(file=f"correspondences/{csv_file}")
            with open(os.path.join(data_dir, csv_file), "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    CorrespondenceEntry.objects.create(
                        correspondence=correspondence,
                        id_in_file=row.get("ID", ""),
                        name=row.get("Nom", ""),
                        type=row.get("Type", "")
                    )
            self.stdout.write(self.style.SUCCESS(f"Fichier CSV {csv_file} chargé !"))

        self.stdout.write(self.style.SUCCESS("CHARGEMENT TERMINE"))
