from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.conf import settings
from Bio.Restriction import AllEnzymes # Nécessite Biopython installé
from django.core.validators import FileExtensionValidator

# ==============================================================================
# 1. GESTION UTILISATEURS (Branche AGASH)
# ==============================================================================

class CustomUserManager(BaseUserManager):
    """ Gestionnaire pour créer des utilisateurs avec l'email comme identifiant. """
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
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Administrateur'),
        ('USER', 'Utilisateur'),
        ('READER', 'Lecteur'),
    )
    email = models.EmailField(unique=True, verbose_name="Adresse email")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='USER')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = CustomUserManager()

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='biolib_user_set',  # Nom unique pour éviter le clash
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='biolib_user_set',  # Nom unique pour éviter le clash
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.email

class Team(models.Model):
    """ Branche AGASH : Hiérarchie Équipes """

    TEAM_PURPOSE_CHOICES = [
        ('research', 'Recherche scientifique'),
        ('campaigns', 'Gestion de campagnes expérimentales'),
        ('analysis', 'Analyse et exploration de données'),
        ('teaching', 'Enseignement / travaux pratiques'),
        ('methods', 'Développement de méthodes / protocoles'),
        ('collaboration', 'Projet collaboratif inter-équipes'),
        ('testing', 'Tests / validation technique'),
        ('archival', 'Archivage et partage de résultats'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    purpose = models.CharField(
        max_length=30,
        choices=TEAM_PURPOSE_CHOICES,
        blank=True
    )

    visibility = models.CharField(
        max_length=10,
        choices=[('private', 'Privée'), ('public', 'Publique')],
        default='private'
    )

    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='led_teams'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='teams', blank=True
    )

    def __str__(self):
        return self.name


# ==============================================================================
# 2. DONNÉES BIOLOGIQUES (Fusion AGASH + MAIN)
# ==============================================================================

class PlasmidCollection(models.Model):
    """ Fusion : On garde le nom 'PlasmidCollection' d'Agash. """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True) # Vient de Main
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Plasmid(models.Model):
    """ Fusion : On garde la branche d'AGASH pour les fichier + on conserve la simplicité de MAIN """
    collection = models.ForeignKey(PlasmidCollection, on_delete=models.CASCADE, related_name='plasmids')
    identifier = models.CharField(max_length=100, help_text="Code labo (ex: pYTK045)")
    name = models.CharField(max_length=200, blank=True)

    # AGASH : Fichier source
    genbank_file = models.FileField(upload_to='plasmids/', verbose_name="Fichier GenBank", null=True, blank=True)

    # MAIN/AGASH : Séquence brute (utile pour recherche rapide)
    sequence = models.TextField(help_text="Séquence nucléotidique")

    def __str__(self):
        return f"{self.identifier} - {self.name}"

# ==============================================================================
# 3. MAPPING & CORRESPONDANCE (Version MAIN améliorée)
# ==============================================================================

class Correspondence(models.Model):
    name = models.CharField(max_length=200, default="Table de correspondance")
    file = models.FileField(upload_to="correspondences/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name

class CorrespondenceEntry(models.Model):
    """ Vient de le branche MAIN : Permet de stocker le contenu du fichier Excel en base """
    correspondence = models.ForeignKey(Correspondence, on_delete=models.CASCADE, related_name="entries")
    id_in_file = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=100)

# ==============================================================================
# 4. TEMPLATES & SIMULATIONS (Fusion Totale des deux branches)
# ==============================================================================

class CampaignTemplate(models.Model):
    """ Fusion : Fichiers (branche Agash) + Paramètres Bio ( branche Main) """

    ALL_ENZYMES_LIST = sorted([str(e) for e in AllEnzymes])
    ENZYME_CHOICES = [(e, e) for e in ALL_ENZYMES_LIST]
    SEPARATOR_CHOICES = [('-', 'Tiret (-)'), ('_', 'Underscore (_)'), ('', 'Aucun')]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    enzyme = models.CharField(max_length=50, choices=ENZYME_CHOICES, default='BsaI')
    output_separator = models.CharField(max_length=5, choices=SEPARATOR_CHOICES, default='-')

    VISIBILITY_CHOICES = [
        ('private', 'Privé (Moi uniquement)'),
        ('team', 'Visible par mon équipe'),
        ('public', 'Public (Tout le monde)'),
    ]
    visibility = models.CharField(
        max_length=20, 
        choices=VISIBILITY_CHOICES, 
        default='private', 
        verbose_name="Visibilité"
    )
    
    # --- AJOUT DU LIEN VERS L'ÉQUIPE ---
    team = models.ForeignKey(
        Team, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='templates',
        verbose_name="Équipe associée"
    )
    # -----------------------------------

    # -- Partie AGASH (Fichiers & Droits) --
    file = models.FileField(upload_to="templates/", blank=True, null=True, help_text="Fichier modèle Excel")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class TemplatePart(models.Model):
    """ Vient de MAIN : Structure interne du template (Fusionnée avec les champs manquants) """
    template = models.ForeignKey(CampaignTemplate, on_delete=models.CASCADE, related_name="parts")
    name = models.CharField(max_length=100, verbose_name="Nom de la partie")

    type_id = models.CharField(max_length=50, verbose_name="Type (ex: 1, 3a)", default="1")
    description = models.CharField(max_length=255, blank=True)

    order = models.PositiveIntegerField(default=0, verbose_name="Ordre")
    is_mandatory = models.BooleanField(default=True, verbose_name="Obligatoire")

    include_in_output = models.BooleanField(
        default=True,
        verbose_name="Inclure dans le nom ?",
        help_text="Si coché, ce nom apparaîtra dans le nom du plasmide final."
    )

    is_separable = models.BooleanField(default=False, verbose_name="Séparable")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.template.name} - {self.name} ({self.order})"

class Simulation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='PENDING')
    date_run = models.DateTimeField(auto_now_add=True)
    result_file = models.CharField(max_length=255, blank=True, null=True)

    # --- MODIFICATIONS ---

    # 1. Le lien vers CampaignTemplate devient optionnel ou obsolète
    # (On le garde en null=True au cas où vous changeriez d'avis, sinon on peut le supprimer)
    template = models.ForeignKey('CampaignTemplate', on_delete=models.SET_NULL, null=True, blank=True)

    # 2. Le fichier Template (XLSX) uploadé directement
    template_file = models.FileField(
        upload_to='simulation_templates/',
        verbose_name="Fichier Template (Excel)",
        validators=[FileExtensionValidator(allowed_extensions=['csv', 'xls', 'xlsx'])],
        null=True, blank=False # Obligatoire
    )

    # 3. L'enzyme (Puisqu'on n'a plus l'objet Template pour nous le dire, il faut le demander)
    ENZYME_CHOICES = [
        ('BsaI', 'BsaI (Golden Gate)'),
        ('BsmBI', 'BsmBI (Golden Gate)'),
        ('BbsI', 'BbsI (Golden Gate)'),
        ('SapI', 'SapI'),
        ('NotI', 'NotI (BioBrick)'),
    ]
    enzyme = models.CharField(max_length=50, choices=ENZYME_CHOICES, default='BsaI')

    # 4. Le fichier Campagne (CSV) - Déjà fait avant
    campaign_file = models.FileField(
        upload_to='campaigns_inputs/',
        verbose_name="Fichier Campagne (CSV)",
        validators=[FileExtensionValidator(allowed_extensions=['xls', 'xlsx', 'csv'])],
        null=True, blank=False
    )

    def __str__(self):
        return f"Simu #{self.id} ({self.date_run})"
