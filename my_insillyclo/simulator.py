#!/usr/bin/env python3
import pathlib
import shutil
import logging
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

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
# LOGIQUE DYNAMIQUE : PATCH DES FICHIERS
# =============================================================================

def _patch_sequence_dynamically(record, target_left, target_right, is_backbone):
    """
    Force les extrémités de la séquence pour matcher les connecteurs demandés.
    """
    original_seq = str(record.seq).upper()

    # 1. Nettoyage : On enlève les anciens sites BsaI
    clean_seq = original_seq.replace("GGTCTC", "GGTCTG").replace("GAGACC", "GAGACG")

    # 2. Construction de la nouvelle séquence
    bsaI = "GGTCTC"
    bsaI_rev = "GAGACC"

    # Structure : BsaI -> Spacer(A) -> Left -> ADN -> Right -> Spacer(T) -> BsaI_Rev
    new_seq = bsaI + "A" + target_left + clean_seq + target_right + "T" + bsaI_rev

    new_record = SeqRecord(
        Seq(new_seq),
        id=record.id,
        name=record.name,
        description=f"Auto-Adapted ({target_left}->{target_right})",
        annotations={"molecule_type": "DNA", "topology": "linear"}
    )
    return new_record

def _dynamic_compatibility_layer(template_path, input_parts_files, gb_files, work_dir, observer):
    """
    Utilise le parser officiel pour comprendre la recette et patche les fichiers.
    """

    # A. Lire le Mapping (Nom -> ID Fichier)
    name_to_filename = {}
    if HAS_PANDAS and input_parts_files:
        try:
            csv_path = input_parts_files[0]
            df_map = pd.read_csv(csv_path, sep=None, engine='python')
            df_map.columns = df_map.columns.str.strip()

            # Recherche des colonnes pID et Name
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

    # B. Lire la recette VIA LE PARSER OFFICIEL
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
            # CORRECTION ICI : On lit 'part_instance' (la valeur) et non 'input_part.name' (la colonne)
            for part_instance, input_part in plasmid.parts:
                if part_instance:
                    val = str(part_instance).strip()
                    if val:
                        current_recipe.append(val)

            if current_recipe:
                print(f"DEBUG: Recette extraite ({plasmid.plasmid_id}) : {current_recipe}")
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
            # Identification du fichier réel via le mapping
            real_id = name_to_filename.get(part_name, part_name)

            # Calcul des liens (i -> i+1)
            link_in = LINKS[i % len(LINKS)]
            link_out = LINKS[(i + 1) % len(LINKS)]

            # Boucle fermée
            if i == count - 1:
                link_out = LINKS[0]

            file_overhangs[real_id] = (link_in, link_out)

    # D. Appliquer les modifications aux fichiers
    ready_files = []

    # Indexation des fichiers sources disponibles
    available_files = {}
    for p in gb_files:
        p_path = pathlib.Path(p)
        available_files[p_path.stem] = p_path
        available_files[p_path.name] = p_path

    processed_stems = set()

    for filename_id, (target_left, target_right) in file_overhangs.items():
        # Recherche flexible du fichier
        src_path = available_files.get(filename_id)
        if not src_path:
            # Tentative de recherche partielle
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

            # Détection Backbone (pour info, mais ici on traite tout le monde pareil)
            is_backbone = "AmpR" in stem or "pMYT" in stem

            # Application du patch
            new_record = _patch_sequence_dynamically(record, target_left, target_right, is_backbone)

            dst_path = work_dir / f"{stem}.gb"
            with open(dst_path, "w") as f:
                SeqIO.write(new_record, f, "genbank")

            ready_files.append(dst_path)
            processed_stems.add(stem)
            print(f"DEBUG: Patché {stem} ({target_left} -> {target_right})")

        except Exception as e:
            print(f"Erreur lors du patch de {stem}: {e}")

    # Copie des fichiers restants (ceux non utilisés dans la recette)
    for stem, path in available_files.items():
        if stem not in processed_stems:
            dst = work_dir / path.name
            shutil.copy(path, dst)
            ready_files.append(dst)

    return ready_files


# =============================================================================
# MAIN WRAPPER
# =============================================================================

def compute_all(
    observer,
    settings,
    input_template_filled,
    input_parts_files,
    gb_plasmids,
    output_dir,
    data_source=None,
    enzyme_names=None,
    **kwargs
):
    work_dir = pathlib.Path(output_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    # 1. Conversion Template (CSV -> Excel)
    template_path = pathlib.Path(input_template_filled)
    if HAS_PANDAS and template_path.suffix.lower() == '.csv':
        try:
            df = pd.read_csv(template_path, header=None, sep=None, engine='python')
            if "Assembly settings" not in df.iloc[:, 0].astype(str).values:
                header = pd.DataFrame([["Assembly settings",""],["assembly_type","Golden Gate"],["",""],["Constructs settings",""]])
                df = pd.concat([header, df], ignore_index=True)
            new_template = template_path.with_suffix('.xlsx')
            df.to_excel(new_template, index=False, header=False, engine='openpyxl')
            template_path = new_template
        except Exception:
            pass

    # 2. APPEL DE LA COUCHE DYNAMIQUE
    print("--- DÉBUT ANALYSE DYNAMIQUE (Corrigée) ---")

    ready_files = _dynamic_compatibility_layer(
        template_path,
        input_parts_files,
        gb_plasmids,
        work_dir,
        observer
    )

    print(f"--- FIN ANALYSE DYNAMIQUE ({len(ready_files)} fichiers prêts) ---")

    # 3. Data Source
    if data_source is None or isinstance(data_source, str):
        real_data_source = insillyclo.data_source.DataSourceHardCodedImplementation()
    else:
        real_data_source = data_source

    real_enzyme = ['BsaI']

    return insillyclo.simulator.compute_all(
        observer=observer,
        settings=settings,
        input_template_filled=template_path,
        input_parts_files=[pathlib.Path(p) for p in input_parts_files] if input_parts_files else [],
        gb_plasmids=ready_files,
        output_dir=work_dir,
        data_source=real_data_source,
        enzyme_names=real_enzyme,
        primers_file=kwargs.get('primers_file', None),
        primer_id_pairs=kwargs.get('primer_id_pairs', []),
        default_mass_concentration=kwargs.get('default_mass_concentration', 200),
        sbol_export=kwargs.get('sbol_export', False),
        concentration_file=kwargs.get('concentration_file', None)
    )
