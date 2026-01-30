#!/usr/bin/env python3
import pathlib
import shutil
import logging
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
import zipfile
import os
import glob
from django.conf import settings

# Imports InSillyClo
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import insillyclo.data_source
    import insillyclo.observer
    import insillyclo.simulator
    import insillyclo.conf
    import insillyclo.digestion
    import insillyclo.parser
    import insillyclo.models
except ImportError as e:
    raise ImportError(f"Le package 'insillyclo' est introuvable. Erreur : {e}")

# =============================================================================
# DEFINITION DES ENZYMES (Séquences de reconnaissance)
# =============================================================================

# Dictionnaire pour mapper le nom de l'enzyme à ses sites de coupure (Forward et Reverse)
# Pour le Golden Gate (Type IIS), le site est asymétrique.
ENZYME_SITES = {
    'BsaI':  {'fwd': 'GGTCTC', 'rev': 'GAGACC'},
    'BsmBI': {'fwd': 'CGTCTC', 'rev': 'GAGACG'},
    'BbsI':  {'fwd': 'GAAGAC', 'rev': 'GTCTTC'},
    'SapI':  {'fwd': 'GCTCTTC', 'rev': 'GAAGAGC'},
    # NotI est Type IIP (Palindromique), souvent moins utilisé pour l'assemblage pur Golden Gate
    # mais on le met au cas où pour la compatibilité.
    'NotI':  {'fwd': 'GCGGCCGC', 'rev': 'GCGGCCGC'},
}

# =============================================================================
# LOGIQUE DYNAMIQUE : PATCH DES FICHIERS
# =============================================================================

def _patch_sequence_dynamically(record, target_left, target_right, enzyme_sites):
    """
    Force les extrémités de la séquence pour matcher les connecteurs demandés
    en utilisant l'enzyme fournie (enzyme_sites).
    """
    original_seq = str(record.seq).upper()

    site_fwd = enzyme_sites['fwd']
    site_rev = enzyme_sites['rev']

    # 1. Nettoyage : On enlève les anciens sites (pour éviter les coupures internes)
    # On remplace par une mutation silencieuse basique (ex: C->G à la fin) pour "casser" le site
    clean_seq = original_seq.replace(site_fwd, site_fwd[:-1] + "G").replace(site_rev, site_rev[:-1] + "G")

    # 2. Construction de la nouvelle séquence dynamique
    # Structure : Site_Enzyme -> Spacer(A) -> Left -> ADN -> Right -> Spacer(T) -> Site_Enzyme_Rev
    new_seq = site_fwd + "A" + target_left + clean_seq + target_right + "T" + site_rev

    new_record = SeqRecord(
        Seq(new_seq),
        id=record.id,
        name=record.name,
        description=f"Auto-Adapted ({target_left}->{target_right}) via {site_fwd}",
        annotations={"molecule_type": "DNA", "topology": "linear"}
    )
    return new_record

def _dynamic_compatibility_layer(template_path, input_parts_files, gb_files, work_dir, observer, assembly_enzyme_name):
    """
    Utilise le parser officiel pour comprendre la recette et patche les fichiers
    en utilisant l'enzyme d'assemblage spécifiée.
    """

    # Récupération des sites pour l'enzyme choisie (Défaut: BsaI)
    enzyme_sites = ENZYME_SITES.get(assembly_enzyme_name, ENZYME_SITES['BsaI'])
    print(f"DEBUG: Assemblage configuré avec l'enzyme {assembly_enzyme_name} (Site: {enzyme_sites['fwd']})")

    # A. Lire le Mapping (Nom -> ID Fichier)
    name_to_filename = {}
    if HAS_PANDAS and input_parts_files:
        try:
            csv_path = input_parts_files[0]
            df_map = pd.read_csv(csv_path, sep=None, engine='python')
            df_map.columns = df_map.columns.str.strip()

            col_id = next((c for c in df_map.columns if c.lower() == 'pid'), None)
            col_name = next((c for c in df_map.columns if c.lower() == 'name'), None)

            if col_id and col_name:
                for _, row in df_map.iterrows():
                    pid = str(row[col_id]).strip()
                    name = str(row[col_name]).strip()
                    name_to_filename[name] = pid
                    name_to_filename[pid] = pid

        except Exception as e:
            print(f"DEBUG: Erreur lecture mapping: {e}")

    # B. Lire la recette
    recipes = []
    try:
        assembly, plasmids = insillyclo.parser.parse_assembly_and_plasmid_from_template(
            template_path,
            input_part_factory=insillyclo.models.InputPartDataClassFactory(),
            assembly_factory=insillyclo.models.AssemblyDataClassFactory(),
            plasmid_factory=insillyclo.models.PlasmidDataClassFactory(),
            observer=observer,
        )

        for plasmid in plasmids:
            current_recipe = []
            for part_instance, input_part in plasmid.parts:
                if part_instance:
                    val = str(part_instance).strip()
                    if val:
                        current_recipe.append(val)

            if current_recipe:
                recipes.append(current_recipe)

    except Exception as e:
        print(f"DEBUG: Erreur Parser Officiel: {e}")
        return []

    # C. Calculer les connecteurs (Overhangs)
    file_overhangs = {}
    LINKS = ["GGAG", "AATG", "GCTT", "CGCT", "TGCC", "GGAA", "TTCC", "ACGT"]

    for recipe in recipes:
        count = len(recipe)
        for i, part_name in enumerate(recipe):
            real_id = name_to_filename.get(part_name, part_name)
            link_in = LINKS[i % len(LINKS)]
            link_out = LINKS[(i + 1) % len(LINKS)]

            if i == count - 1:
                link_out = LINKS[0]

            file_overhangs[real_id] = (link_in, link_out)

    # D. Appliquer les modifications aux fichiers
    ready_files = []
    available_files = {}
    for p in gb_files:
        p_path = pathlib.Path(p)
        available_files[p_path.stem] = p_path
        available_files[p_path.name] = p_path

    processed_stems = set()

    for filename_id, (target_left, target_right) in file_overhangs.items():
        src_path = available_files.get(filename_id)
        if not src_path:
            for s, p in available_files.items():
                if filename_id in s:
                    src_path = p
                    break

        if not src_path:
            print(f"DEBUG: Fichier introuvable pour la pièce '{filename_id}'")
            continue

        stem = src_path.stem
        if stem in processed_stems: continue

        try:
            record = SeqIO.read(src_path, "genbank")

            # --- CORRECTION : On passe l'enzyme dynamique ici ---
            new_record = _patch_sequence_dynamically(record, target_left, target_right, enzyme_sites)
            # ----------------------------------------------------

            dst_path = work_dir / f"{stem}.gb"
            with open(dst_path, "w") as f:
                SeqIO.write(new_record, f, "genbank")

            ready_files.append(dst_path)
            processed_stems.add(stem)

        except Exception as e:
            print(f"Erreur lors du patch de {stem}: {e}")

    for stem, path in available_files.items():
        if stem not in processed_stems:
            dst = work_dir / path.name
            shutil.copy(path, dst)
            ready_files.append(dst)

    return ready_files

def creer_archive_zip(simulation_id, noms_fichiers_gb=None):
    # (Pas de changement ici, c'est identique à ton code)
    dossier_simu = os.path.join(settings.BASE_DIR, 'simulation', f"simulation_{simulation_id}")
    nom_zip = f"simulation_{simulation_id}_archive.zip"
    chemin_zip_final = os.path.join(dossier_simu, nom_zip)

    if not os.path.exists(dossier_simu): return None

    fichiers_a_zipper = glob.glob(os.path.join(dossier_simu, "*.csv"))

    if noms_fichiers_gb:
        for nom in noms_fichiers_gb:
            if not nom.endswith('.gb'): nom += '.gb'
            chemin_complet = os.path.join(dossier_simu, nom)
            if os.path.exists(chemin_complet):
                fichiers_a_zipper.append(chemin_complet)

    if not fichiers_a_zipper: return None

    try:
        with zipfile.ZipFile(chemin_zip_final, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for fichier in fichiers_a_zipper:
                zipf.write(fichier, arcname=os.path.basename(fichier))
        return chemin_zip_final
    except Exception as e:
        print(f"Erreur ZIP : {e}")
        return None

# =============================================================================
# MAIN FONCTION DE SIMULATION
# =============================================================================

def compute_all(
    observer,
    settings,
    input_template_filled,
    input_parts_files,
    gb_plasmids,
    output_dir,
    data_source=None,
    gel_enzymes=None,       # Liste des cases à cocher (ou None)
    assembly_enzyme='BsaI', # Enzyme du menu déroulant
    **kwargs
):
    work_dir = pathlib.Path(output_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    # 1. Gestion de l'enzyme d'assemblage (Prioritaire)
    main_assembly_enzyme = assembly_enzyme if assembly_enzyme else 'BsaI'

    # 2. Gestion des enzymes du Gel (Avec Fallback)
    if not gel_enzymes:
        print(f"DEBUG: Pas d'enzyme de gel choisie. Utilisation de l'enzyme d'assemblage ({main_assembly_enzyme}) par défaut.")
        # C'est ici que la magie opère : on force l'affichage avec l'enzyme d'assemblage
        real_gel_enzymes = [main_assembly_enzyme]
    elif isinstance(gel_enzymes, str):
        real_gel_enzymes = [gel_enzymes]
    else:
        real_gel_enzymes = gel_enzymes

    # Petite correction cosmétique ici pour le log
    print(f"DEBUG: Enzymes pour le gel -> {', '.join(real_gel_enzymes)}")

    # 3. Préparation du Template (Excel) et INJECTION DE L'ENZYME D'ASSEMBLAGE
    template_path = pathlib.Path(input_template_filled)

    # On force la conversion/lecture via Pandas pour modifier l'enzyme
    if HAS_PANDAS:
        try:
            # A. Lecture du fichier (CSV ou Excel)
            if template_path.suffix.lower() == '.csv':
                df = pd.read_csv(template_path, header=None, sep=None, engine='python')
            else:
                # Si c'est déjà un Excel, on le lit pour le modifier
                df = pd.read_excel(template_path, header=None)

            # B. Vérification/Création de l'en-tête "Assembly settings"
            col0_str = df.iloc[:, 0].astype(str).values

            if "Assembly settings" not in col0_str:
                # Si l'en-tête n'existe pas, on le crée avec l'enzyme d'assemblage
                header = pd.DataFrame([
                    ["Assembly settings", ""],
                    ["assembly_type", "Golden Gate"],
                    ["enzyme", main_assembly_enzyme], # <--- IMPORTANT : On force l'enzyme d'assemblage
                    ["", ""],
                    ["Constructs settings", ""]
                ])
                df = pd.concat([header, df], ignore_index=True)
            else:
                # C. Si l'en-tête existe, on cherche la ligne "enzyme" pour la mettre à jour
                enzyme_row_index = -1
                for idx, val in enumerate(df.iloc[:, 0]):
                    if str(val).strip().lower() == "enzyme":
                        enzyme_row_index = idx
                        break

                if enzyme_row_index != -1:
                    df.iloc[enzyme_row_index, 1] = main_assembly_enzyme
                    print(f"DEBUG: Enzyme mise à jour dans le template -> {main_assembly_enzyme}")
                else:
                    pass

            # D. Sauvegarde du fichier modifié
            new_template = work_dir / "processed_template.xlsx"
            df.to_excel(new_template, index=False, header=False, engine='openpyxl')
            template_path = new_template

        except Exception as e:
            print(f"ATTENTION: Erreur lors de la modification du template Excel : {e}")
            pass

    # 4. APPEL DE LA COUCHE DYNAMIQUE (Patch avec l'enzyme d'assemblage)
    print(f"--- DÉBUT ANALYSE DYNAMIQUE (Assemblage avec {main_assembly_enzyme}) ---")

    ready_files = _dynamic_compatibility_layer(
        template_path,
        input_parts_files,
        gb_plasmids,
        work_dir,
        observer,
        main_assembly_enzyme # <--- On patche les bouts collants pour CETTE enzyme
    )

    print(f"--- FIN ANALYSE DYNAMIQUE ({len(ready_files)} fichiers prêts) ---")

    # 5. Data Source
    if data_source is None or isinstance(data_source, str):
        real_data_source = insillyclo.data_source.DataSourceHardCodedImplementation()
    else:
        real_data_source = data_source

    # 6. Gestion des amorces
    user_primers_text = kwargs.get('user_primers', None)
    primers_file_path = kwargs.get('primers_file', None)

    if user_primers_text:
        custom_primers_path = work_dir / "user_primers.fasta"
        try:
            with open(custom_primers_path, "w") as f:
                lines = user_primers_text.split('\n')
                counter = 1
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    if ":" in line:
                        p_name, p_seq = line.split(":", 1)
                        f.write(f">{p_name.strip()}\n{p_seq.strip().upper()}\n")
                    else:
                        f.write(f">Primer_{counter}\n{line.strip().upper()}\n")
                        counter += 1
            primers_file_path = str(custom_primers_path)
        except Exception as e:
            print(f"Erreur amorces : {e}")

    # 7. APPEL FINAL À INSILLYCLO
    return insillyclo.simulator.compute_all(
        observer=observer,
        settings=settings,
        input_template_filled=template_path, # Fichier Excel modifié
        input_parts_files=[pathlib.Path(p) for p in input_parts_files] if input_parts_files else [],
        gb_plasmids=ready_files,
        output_dir=work_dir,
        data_source=real_data_source,

        enzyme_names=real_gel_enzymes, # <--- Liste (soit cases cochées, soit [assemblage])

        primers_file=primers_file_path,
        primer_id_pairs=kwargs.get('primer_id_pairs', []),
        default_mass_concentration=kwargs.get('default_mass_concentration', 200),
        sbol_export=kwargs.get('sbol_export', False),
        concentration_file=kwargs.get('concentration_file', None)
    )
