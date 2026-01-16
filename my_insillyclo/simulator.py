import os
import csv
import random

# On essaie d'importer matplotlib pour générer une image de Gel.
# Si l'installation a échoué, on fera sans.
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

def compute_all(observer, settings, input_template_filled, input_parts_files,
                gb_plasmids, output_dir, data_source,
                primers_file=None, primer_id_pairs=None, enzyme_names=None,
                default_mass_concentration=None, plasmid_concentration_file=None,
                sbol_export=False, **kwargs):
    """
    Version 'Mock' (Simulation factice) pour faire fonctionner l'interface Web.
    Génère des fichiers de résultats réalistes sans faire le calcul biologique complexe.
    """

    # 1. Notification via l'observer (pour le log)
    if observer:
        try:
            observer.notify_message(f"Démarrage de la simulation dans {output_dir}")
            observer.notify_message(f"Template utilisé : {os.path.basename(str(input_template_filled))}")
            observer.notify_message(f"Enzyme sélectionnée : {enzyme_names}")
        except:
            print("Log observer failed")

    # 2. Création du dossier de sortie s'il n'existe pas
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 3. GÉNÉRATION 1 : Fichier de dilutions (CSV)
    # On simule un tableau de calcul de volumes
    dilution_path = os.path.join(output_dir, 'dilutions_calculated.csv')
    with open(dilution_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(['Plasmid_ID', 'Concentration', 'Volume_Requis (uL)', 'H2O (uL)'])
        simulated_plasmids = gb_plasmids if gb_plasmids else ['Plasmid_A', 'Plasmid_B', 'Backbone_X']

        for p_name in simulated_plasmids:
            name = str(p_name) if isinstance(p_name, str) else "Plasmid_Input"
            conc = random.randint(50, 200)
            vol = round(random.uniform(1.0, 3.0), 1)
            water = round(10 - vol, 1)

            # ASTUCE SUPPLÉMENTAIRE : Remplacer le point par une virgule pour les chiffres
            # Si votre Excel est en français, il ne comprend pas "2.9", il veut "2,9"
            vol_str = str(vol).replace('.', ',')
            water_str = str(water).replace('.', ',')

            # On écrit la ligne avec les nouvelles variables
            writer.writerow([name, f'{conc} ng/uL', vol_str, water_str])

    # 4. GÉNÉRATION 2 : Image du Gel d'Électrophorèse (PNG)
    # C'est ce que l'utilisateur veut voir à l'écran.
    image_path = os.path.join(output_dir, 'simulated_gel.png')

    if MATPLOTLIB_AVAILABLE:
        try:
            plt.figure(figsize=(6, 8), facecolor='black')
            ax = plt.gca()
            ax.set_facecolor('black')

            # Dessin des bandes (simulation visuelle)
            # Colonne 1 : Ladder (échelle)
            ladder_y = [1000, 800, 600, 400, 200]
            for y in ladder_y:
                plt.hlines(y, 0.5, 1.5, colors='white', linewidth=2)

            # Colonne 2 : Résultat simulé
            sample_y = [950, 420] # Deux bandes fictives
            for y in sample_y:
                plt.hlines(y, 1.5, 2.5, colors='white', linewidth=3, alpha=0.9)

            plt.title("Simulation InSillyClo (GEL)", color='white')
            plt.ylabel("Base Pairs (bp)", color='white')
            plt.xticks([1, 2], ['Ladder', 'Assembly'], color='white')
            plt.yticks(color='white')
            plt.grid(False)

            plt.savefig(image_path)
            plt.close()
            print(f"Image générée : {image_path}")

        except Exception as e:
            print(f"Erreur lors de la génération de l'image : {e}")
            _create_dummy_text_file(image_path)
    else:
        # Si pas de matplotlib, on crée un fichier vide pour éviter le crash
        print("Matplotlib non installé : Impossible de générer l'image.")
        _create_dummy_text_file(image_path)

    # 5. Fin
    if observer:
        try: observer.notify_message("Simulation terminée avec succès.")
        except: pass

def _create_dummy_text_file(path):
    """Crée un fichier texte renommé en .png juste pour éviter une erreur 404"""
    with open(path + ".txt", 'w') as f:
        f.write("Image non disponible (Matplotlib manquant)")
