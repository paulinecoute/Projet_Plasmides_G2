from django.db import models
from django.contrib.auth.models import User

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
    
    ENZYME_CHOICES = [
        ('BsaI', 'BsaI'),
        ('BbsI', 'BbsI'),
        ('NotI', 'NotI'),
    ]
    enzyme = models.CharField(max_length=50, choices=ENZYME_CHOICES, verbose_name="Enzyme de restriction")
    
    file = models.FileField(upload_to="templates/", blank=True, null=True)
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    is_public = models.BooleanField(default=False, verbose_name="Est public ?")
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
    is_separable = models.BooleanField(default=False, verbose_name="Séparable")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.template.name} - {self.name} ({self.order})"
