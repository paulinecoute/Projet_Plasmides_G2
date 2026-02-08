import os
import openpyxl  
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
from biolib.models import Plasmid, PlasmidCollection, User, CampaignTemplate, TemplatePart

class Command(BaseCommand):
    help = 'Charge les plasmides et les templates récursivement et parse les fichiers Excel'

    def handle(self, *args, **kwargs):
        data_dir = os.path.join(settings.BASE_DIR, 'data_web')

        self.stdout.write("--- Démarrage de l'import  ---")

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

            collection = None
            if folder_name != 'data_web':
                collection_name = f"Collection {folder_name}"
                collection, created = PlasmidCollection.objects.get_or_create(
                    name=collection_name,
                    defaults={'owner': admin_user, 'publication_status': 'approved'}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f" > Collection créée : {collection_name}"))
            else:
                self.stdout.write(f" > Racine '{folder_name}' : Pas de collection créée.")

            valid_files = [f for f in files if f.lower().endswith(('.gb', '.dna', '.fasta', '.xlsx'))]
            
            for filename in valid_files:
                file_path = os.path.join(root, filename)
                identifier = os.path.splitext(filename)[0]

                if filename.lower().endswith('.xlsx'):
                    try:

                        template = CampaignTemplate.objects.filter(name=identifier, owner=admin_user).first()
                        
                        action_tpl = "Updated" if template else "Created"
                        
                        if not template:
                            template = CampaignTemplate(
                                name=identifier,
                                owner=admin_user,
                                description="", # Description vide comme demandé
                                visibility='public',
                                is_public=True
                            )

                        with open(file_path, 'rb') as f_byte:
                            template.file.save(filename, File(f_byte), save=True)

                        wb = openpyxl.load_workbook(file_path, data_only=True)
                        ws = wb.active

                        enzyme_val = ws['B2'].value
                        separator_val = ws['B4'].value

                        if enzyme_val:
                            template.enzyme = str(enzyme_val).strip()
                        if separator_val:
                            template.output_separator = str(separator_val).strip()
                        
                        template.save()

                        template.parts.all().delete()

                        col_idx = 2 
                        order_counter = 1

                        while True:
                            part_name = ws.cell(row=9, column=col_idx).value

                            if not part_name or "output" in str(part_name).lower() or "↓" in str(part_name):
                                break

                            part_type = ws.cell(row=10, column=col_idx).value or "1"
                            
                            is_optional_val = str(ws.cell(row=11, column=col_idx).value).lower()
           
                            is_mandatory = False if is_optional_val == 'true' else True

                            in_output_val = str(ws.cell(row=12, column=col_idx).value).lower()
                            include_in_output = True if in_output_val == 'true' else False

                            TemplatePart.objects.create(
                                template=template,
                                name=str(part_name),
                                type_id=str(part_type),
                                order=order_counter,
                                is_mandatory=is_mandatory,
                                include_in_output=include_in_output
                            )

                            col_idx += 1
                            order_counter += 1

                        count_templates += 1
                        self.stdout.write(f"   

                    except Exception as e:
                         self.stdout.write(self.style.ERROR(f"Erreur Template {filename}: {e}"))
                    
                    continue

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

        self.stdout.write(self.style.SUCCESS(f"--- FINI : {count_plasmids} plasmides, {count_templates} templates parsés ---"))
