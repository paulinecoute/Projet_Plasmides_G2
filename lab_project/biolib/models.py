from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings



from django.contrib.auth.base_user import BaseUserManager

# Définir le Manager
class CustomUserManager(BaseUserManager):
    """
    Gestionnaire pour créer des utilisateurs avec l'email comme identifiant.
    """
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Le superuser doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Le superuser doit avoir is_superuser=True.')

        return self.create_user(email, password, **extra_fields)



# ==============================================================================
# GESTION UTILISATEURS ET HIERARCHIE (Authentication & Access Control)
# ==============================================================================

class User(AbstractUser):
    """
    Modèle d'utilisateur personnalisé.

    Modifications principales :
    - L'authentification se fait via 'email' et non 'username'.
    - Ajout d'un système de 'role' pour gérer les permissions (RBAC) au niveau applicatif.
    """

    # Définition des rôles pour restreindre l'accès aux vues et aux fonctionnalités
    ROLE_CHOICES = (
        ('ADMIN', 'Administratrice - Accès total'),
        ('LEADER', 'Cheffe d\'équipe - Gestion de son équipe et ses projets'),
        ('USER', 'Utilisateur - Création et édition de ses propres données'),
        ('READER', 'Lecteur - Accès en lecture seule'),
    )

    # Contrainte unique sur l'email car il sert d'identifiant de connexion
    email = models.EmailField(unique=True, verbose_name="Adresse email")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='USER')

    # Configuration Django pour utiliser l'email comme login principal
    USERNAME_FIELD = 'email'
    # Champs obligatoires lors de la création d'un superuser via le terminal (en plus de l'email)
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    # NOTE SUR LE MOT DE PASSE :
    # Le champ 'password' est hérité de AbstractUser.

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

class Team(models.Model):
    """
    Représente un groupe de recherche ou une unité de laboratoire.
    Structure hiérarchique : 1 Leader  <-> N Membres.
    """
    name = models.CharField(max_length=100, verbose_name="Nom de l'équipe")

    # Le leader a des droits d'administration sur l'équipe.
    # 'related_name' permet d'accéder aux équipes dirigées via user.led_teams.
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='led_teams',
        verbose_name="Responsable d'équipe"
    )

    # Relation Many-to-Many : un user peut appartenir à plusieurs équipes.
    # 'blank=True' permet de créer une équipe sans membres initiaux.
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='teams',
        blank=True,
        verbose_name="Membres de l'équipe"
    )

    def __str__(self):
        return self.name

# ==============================================================================
# DONNÉES BIOLOGIQUES (Banque de Plasmides & Parsing)
# ==============================================================================

class PlasmidCollection(models.Model):
    """
    Conteneur pour organiser les plasmides (ex: "Projet Vaccin X", "Bibliothèque 2024").
    Gère la visibilité des données : Privé (Owner) / Partagé (Team) / Public.
    """
    name = models.CharField(max_length=200)

    # Créateur de la collection
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True, blank=True
    )

    # Si renseigné, tous les membres de cette équipe ont accès à la collection.
    # on_delete=SET_NULL : Si l'équipe est supprimée, la collection reste mais n'est plus partagée.
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="Lier à une équipe pour partager la collection avec ses membres."
    )

    # Si True, accessible à tous les utilisateurs enregistrés de la plateforme.
    is_public = models.BooleanField(default=False, verbose_name="Est public ?")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Plasmid(models.Model):
    """
    Représente l'entité biologique. Les métadonnées sont extraites du fichier GenBank associé.


[Image of DNA plasmid map]

    """
    collection = models.ForeignKey(
        PlasmidCollection,
        on_delete=models.CASCADE,
        related_name='plasmids'
    )

    # Identifiant unique de laboratoire (ex: pYTK045)
    identifier = models.CharField(max_length=100, help_text="Code unique du laboratoire")

    # Nom commun ou descriptif (ex: Venus-Promoter-X)
    name = models.CharField(max_length=200, blank=True)

    # Fichier source (.gb ou .dna) contenant les annotations
    genbank_file = models.FileField(upload_to='plasmids/', verbose_name="Fichier GenBank")

    # Séquence brute (ATGC...) stockée en texte pour permettre les recherches BLAST/alignements
    # sans devoir rouvrir le fichier à chaque fois.
    sequence = models.TextField(help_text="Séquence nucléotidique extraite")

    # Classification (ex: Backbone, Promoteur, CDS, terminateur) utile pour le filtrage
    plasmid_type = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.identifier} ({self.name})"

class CorrespondenceTable(models.Model):
    """
    Fichier de mapping (CSV/Excel) utilisé lors des imports en masse.
    Permet d'associer des noms de fichiers GenBank à des identifiants de laboratoire spécifiques.
    Exemple: "raw_data_01.gb" -> "pLAB-102"
    """
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to='correspondence/')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)

# ==============================================================================
# WORKFLOW DE SIMULATION (Templates & Exécutions)
# ==============================================================================

class CampaignTemplate(models.Model):
    """
    Modèle de simulation (fichier Excel .xlsx).
    Définit la structure attendue (colonnes, paramètres) pour lancer un script de simulation.
    Sert de 'recette' réutilisable.
    """
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to='templates/', help_text="Fichier modèle Excel vide ou pré-rempli")

    # Propriétaire du template. Si Null, peut être considéré comme un template système.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Simulation(models.Model):
    """
    Historique d'exécution d'une simulation.
    Lie un utilisateur à un template et stocke le résultat du calcul.
    """
    STATUS_CHOICES = (
        ('PENDING', 'En attente'),
        ('RUNNING', 'En cours de traitement'),
        ('COMPLETED', 'Terminé avec succès'),
        ('FAILED', 'Échec / Erreur'),
    )

    # L'utilisateur qui a lancé la simulation.
    # Null=True permet de garder l'historique même si l'user est supprimé (si on change on_delete)
    # ou pour des tâches automatiques (cron jobs).
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )

    template = models.ForeignKey(CampaignTemplate, on_delete=models.CASCADE)
    date_run = models.DateTimeField(auto_now_add=True, verbose_name="Date de lancement")

    # Artefact produit par la simulation (ZIP contenant des rapports, JSON, ou Excel modifié)
    result_file = models.FileField(upload_to='simulations/', blank=True, null=True)

    # État de la machine à états (State Machine) pour le suivi des tâches asynchrones (Celery/Redis)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"Simu #{self.id} - {self.template.name} ({self.status})"
