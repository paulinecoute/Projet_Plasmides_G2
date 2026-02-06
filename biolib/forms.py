from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import CampaignTemplate, TemplatePart, Simulation, Team, PlasmidCollection
from django.forms import inlineformset_factory
from django.db.models import Q

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


class SimulationForm(forms.ModelForm):

    # Cases à cocher pour le Gel (Options avancées)
    custom_enzymes = forms.MultipleChoiceField(
        choices=[], # On remplit ça dynamiquement dans le __init__
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Enzymes pour le gel"
    )

    collections = forms.ModelMultipleChoiceField(
        queryset=PlasmidCollection.objects.none(), # Vide par défaut, rempli dans __init__
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
        label="Utiliser des collections existantes"
    )

    pcr_primers = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Ex: FWD: ATGC...\nREV: CGTA...'
        }),
        required=False,
        label="Amorces PCR (Optionnel)"
    )
    save_to_library = forms.BooleanField(
        required=False,
        label="Sauvegarder ces fichiers dans ma bibliothèque ?",
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    new_collection_name = forms.CharField(
        required=False,
        label="Nom de la collection (si sauvegarde)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Mes Plasmides Projet A'
        })
    )

    campaign_save_name = forms.CharField(
        required=False,
        label="Nom pour sauvegarder le fichier de campagne",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Ma Campagne Vaccin'
        })
    )
    template_save_name = forms.CharField(
        required=False,
        label="Nom pour sauvegarder le fichier modèle",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Modèle Vaccin'
        })
    )

    class Meta:
        model = Simulation
        fields = [
            'name',
            'template_file',
            'enzyme',
            'campaign_file',
            'custom_enzymes',
            'pcr_primers',
            'visibility',
            'team'        ,
            'zip_file',
            'default_concentration',
            'concentration_file',
            'collections'
        ]

        labels = {
            'team': 'Choisir l\'équipe'
        }

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de la simulation'}),
            'template_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv, .xlsx, .xls'}),
            'enzyme': forms.Select(attrs={'class': 'form-select'}),
            'campaign_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv, .xls, .xlsx'}),

            # IDs SPÉCIAUX POUR LE JAVASCRIPT (Comme pour Templates)
            'visibility': forms.Select(attrs={'class': 'form-select', 'id': 'id_sim_visibility'}),
            'team': forms.Select(attrs={'class': 'form-select', 'id': 'id_sim_team'}),
            'zip_file': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.zip,application/zip,application/x-zip,application/x-zip-compressed',
            'default_concentration': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': '200.0'}),
            'concentration_file': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.csv'})
            })
        }

    def __init__(self, *args, **kwargs):
        # On récupère l'utilisateur
        user = kwargs.pop('user', None)
        super(SimulationForm, self).__init__(*args, **kwargs)

        # 1. Remplissage des enzymes (Logique Biopython ou Fallback)
        #try:
        #    from Bio.Restriction import AllEnzymes
        #    enz_list = sorted([str(e) for e in AllEnzymes])
        #    self.fields['custom_enzymes'].choices = [(e, e) for e in enz_list]
        #except ImportError:
        #    # Fallback simple si Biopython manque
        #    self.fields['custom_enzymes'].choices = [
        #        ('BsaI', 'BsaI'), ('BsmBI', 'BsmBI'), ('NotI', 'NotI')
        #    ]
        self.fields['custom_enzymes'].choices = [
                ('BsaI', 'BsaI'), ('BsmBI', 'BsmBI'), ('NotI', 'NotI'), ('BbsI', 'BbsI'), ('SapI', 'SapI')
            ]

        # 2. Gestion de l'équipe (Sécurité)
        if user and user.is_authenticated:
            # On ne montre que les équipes de l'utilisateur
            self.fields['team'].queryset = Team.objects.filter(members=user)
            self.fields['collections'].queryset = PlasmidCollection.objects.filter(
                Q(owner=user) |
                Q(publication_status='approved') | Q(team__members=user)
            ).distinct()
        else:
            # Si pas connecté, pas d'équipe possible
            self.fields['team'].queryset = Team.objects.none()
            self.fields['collections'].queryset = PlasmidCollection.objects.filter(
                is_public='True'
            )
        self.fields['visibility'].required = False
        self.fields['team'].required = False
        self.fields['team'].empty_label = "--- Sélectionner une équipe ---"
