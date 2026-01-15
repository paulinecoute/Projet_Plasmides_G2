from django.db import models
from django.contrib.auth.models import User
from Bio.Restriction import AllEnzymes # pour avoir toutes les enzymes

# liste complète des enzymes via BioPython 
ALL_ENZYMES_LIST = sorted([str(e) for e in AllEnzymes])
ENZYME_CHOICES = [(e, e) for e in ALL_ENZYMES_LIST]


SEPARATOR_CHOICES = [
    ('-', 'Tiret (-)'),
    ('_', 'Underscore (_)'),
    ('.', 'Point (.)'),
    ('', 'Aucun'),
]


class Collection(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Plasmid(models.Model):
    name = models.CharField(max_length=255)
    sequence = models.TextField()
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="plasmids")

    def __str__(self):
        return self.name

class Correspondence(models.Model):
    file = models.FileField(upload_to="correspondences/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

class CorrespondenceEntry(models.Model):
    correspondence = models.ForeignKey(Correspondence, on_delete=models.CASCADE, related_name="entries")
    id_in_file = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.id_in_file} - {self.name}"


class CampaignTemplate(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nom du template")
    description = models.TextField(blank=True, verbose_name="Description")
    
    output_separator = models.CharField(
        max_length=5, 
        choices=SEPARATOR_CHOICES, 
        default='-', 
        verbose_name="Séparateur (Output)"
    )

    enzyme = models.CharField(
        max_length=50, 
        choices=ENZYME_CHOICES, 
        default='BsaI',
        verbose_name="Enzyme de restriction"
    )
    
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

    is_public = models.BooleanField(default=False, verbose_name="Validé Public (Admin)")
    
    file = models.FileField(upload_to="templates/", blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class TemplatePart(models.Model):
    template = models.ForeignKey(CampaignTemplate, on_delete=models.CASCADE, related_name="parts")
    name = models.CharField(max_length=100, verbose_name="Nom de la partie")
    type_id = models.CharField(max_length=50, verbose_name="Type (ex: 1, 3a)")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre")
    description = models.CharField(max_length=255, blank=True)
    
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
