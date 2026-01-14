# Projet_Plasmides_G2 – Gestion de Plasmides et Données Biologiques
**Auteurs** : Groupe 2 (Master AMI2B - Université Paris Saclay)
**Contexte** : Conception d’une application web pour aider à l’assemblage de plasmides en utilisant des techniques de MoClo et de Golden Gate Assembly

---

## Prérequis

- **Python 3.13.5**
- **Dossier `data_web/`** (à télécharger sur Ecampus)

---

## Installation

### 1. Cloner le répertoire
```bash
git clone https://github.com/Ange-Louis/Projet_Plasmides_G2.git
cd Projet_Plasmides_G2
```

### 2. Créer un environnement virtuel
Sur Linux & Mac :
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```
Sur Mac, il faut éventuellement télécharger préalablement des bibliothèques avec Homebrew : 
```bash
brew install pkg-config cairo cmake
```
(je ne sais pas comment ça fonctionne sur linux ou windows à vérifier)

### 4. Appliquer les migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Créer un superutilisateur (admin)
```bash
python manage.py createsuperuser
```
(Suivre les instructions pour définir un nom d’utilisateur, email, et mot de passe.)

### 6. Importer les données 
Copier le dossier `data_web/` dans le répertoire du projet puis
```bash
python manage.py load_initial_data
```

### 7. Lancer l'application
#### A. Démarrer le serveur : 
```bash
python manage.py runserver
```
#### B. Accéder à l'interface
- Site : http://127.0.0.1:8000/
- Admin : http://127.0.0.1:8000/admin/ (Se connecter avec le compte admin créé précédemment.)

### 8. Vérifier les données
Dans l'interface admin, nous devrions voir les bases de données.

---

## Structure du projet
```
Projet_Plasmides_G2/
├── data_web/               # Dossier des données à importer
├── biolib/                 # Application Django
│   ├── management/         # Commandes personnalisées
│   │   └── commands/
│   │       └── load_initial_data.py
│   ├── migrations/         # Migrations de la base de données
│   ├── admin.py            # Configuration de l’admin
│   ├── models.py           # Modèles de données
│   ├── apps.py
|   ├── templates/          # pages web
│   └── ...
├── my_insillyclo/              # Configuration du projet Django
├── manage.py               # Script de gestion
└── README.md               
```

