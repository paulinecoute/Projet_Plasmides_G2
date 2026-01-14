# biolib/models.py
from django.db import models


class Collection(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Plasmid(models.Model):
    name = models.CharField(max_length=255)
    sequence = models.TextField()  # Pour stocker la séquence ADN
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
    file = models.FileField(upload_to="templates/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name
