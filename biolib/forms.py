from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import CampaignTemplate, TemplatePart, Simulation, Team
from django.forms import inlineformset_factory

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """
    Formulaire d'inscription compatible avec biolib.User
    (CustomUser avec email comme identifiant)
    """
    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'password1',
            'password2',
        )

class CampaignTemplateForm(forms.ModelForm):
    class Meta:
        model = CampaignTemplate
        fields = ['name', 'description', 'enzyme', 'output_separator', 'visibility', 'team']

        labels = {
            'team': 'Choisir l\'équipe'
        }

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: YTK_Assembly'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),

            'enzyme': forms.Select(attrs={'class': 'form-select'}),
            'output_separator': forms.Select(attrs={'class': 'form-select'}),
            # IDs importants pour le JavaScript
            'visibility': forms.Select(attrs={'class': 'form-select', 'id': 'id_visibility'}),
            'team': forms.Select(attrs={'class': 'form-select', 'id': 'id_team'}),
        }

    def __init__(self, *args, **kwargs):

        user = kwargs.pop('user', None)
        super(CampaignTemplateForm, self).__init__(*args, **kwargs)

        # si utilisateur connecté
        if user:
            # que les equipes dans lesquelles on est
            self.fields['team'].queryset = Team.objects.filter(members=user)

            # si l'utilisateur n'est PAS Admin (Staff), on retire l'option 'Public'
            if not user.is_staff:
                self.fields['visibility'].choices = [
                    ('private', 'Privé (Moi uniquement)'),
                    ('team', 'Visible par mon équipe'),
                ]

        # Le champ équipe est optionnel
        self.fields['team'].required = False
        self.fields['team'].empty_label = "--- Sélectionner une équipe ---"

class TemplatePartForm(forms.ModelForm):
    class Meta:
        model = TemplatePart
        fields = ['name', 'type_id', 'order', 'is_mandatory', 'include_in_output', 'is_separable']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'type_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Type'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'style': 'width: 80px'}),

            # Les checkbox stylisées
            'is_mandatory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'include_in_output': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_separable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

TemplatePartFormSet = inlineformset_factory(
    CampaignTemplate,
    TemplatePart,
    form=TemplatePartForm,
    extra=1,
    can_delete=True
)


# biolib/forms.py

class SimulationForm(forms.ModelForm):
    # --- 1. DEFINITION DES CHOIX (Enzymes Avancées) ---
    GEL_ENZYME_CHOICES = [
        ('BsaI', 'BsaI (Golden Gate)'),
        ('BsmBI', 'BsmBI (Golden Gate)'),
        ('BbsI', 'BbsI (Golden Gate)'),
        ('SapI', 'SapI'),
        ('NotI', 'NotI (BioBrick)'),
    ]

    # --- 2. CHAMPS SUPPLEMENTAIRES (Hors Modèle direct ou Widgets Spéciaux) ---

    # Cases à cocher pour le Gel (Options avancées)
    custom_enzymes = forms.MultipleChoiceField(
        choices=GEL_ENZYME_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Enzymes pour le gel"
    )

    class Meta:
        model = Simulation
        # --- 3. LISTE DE TOUS LES CHAMPS A AFFICHER ---
        # C'est ici que l'erreur se situait. On remet tout le monde !
        fields = [
            'name',           # Le nom (si ajouté au modèle)
            'template_file',  # L'upload du template CSV
            'enzyme',         # L'enzyme principale
            'campaign_file',  # L'upload de la campagne XLSX
            'custom_enzymes', # Nos cases à cocher
            'pcr_primers'     # La zone de texte pour les amorces
        ]

        # --- 4. STYLES (Bootstrap) ---
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de la simulation'
            }),

            # Restauration des styles pour les fichiers
            'template_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.csv, .xlsx, .xls'
            }),
            'enzyme': forms.Select(attrs={
                'class': 'form-select'
            }),
            'campaign_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.csv, .xls, .xlsx'
            }),

            # Style pour les amorces
            'pcr_primers': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Format: Nom: SEQUENCE (ou juste la séquence)'
            }),
        }
