from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import CampaignTemplate, TemplatePart, Simulation, Team, PlasmidCollection, Correspondence, Plasmid
from django.forms import inlineformset_factory
from django.db.models import Q
import os
from django.core.exceptions import ValidationError

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
            'visibility': forms.Select(attrs={'class': 'form-select', 'id': 'id_visibility'}),
            'team': forms.Select(attrs={'class': 'form-select', 'id': 'id_team'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(CampaignTemplateForm, self).__init__(*args, **kwargs)

        # si utilisateur connecté
        if user:
            self.fields['team'].queryset = Team.objects.filter(members=user)

            if not user.is_staff:
                self.fields['visibility'].choices = [
                    ('private', 'Privé (Moi uniquement)'),
                    ('team', 'Visible par mon équipe'),
                ]

        self.fields['team'].required = False
        self.fields['team'].empty_label = "--- Sélectionner une équipe ---"

class CorrespondenceForm(forms.ModelForm):
    class Meta:
        model = Correspondence
        fields = ['name', 'description', 'file']

        labels = {
            'name': 'Nom de la table',
            'description': 'Description',
            'file': 'Fichier de correspondance (.csv, .xlsx)'
        }

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Table conversion A'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),

            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.csv, .xlsx, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, text/csv'
            }),
        }

    # 3. Validation de sécurité (Backend)
    def clean_file(self):
        file = self.cleaned_data.get('file')

        if file:
            ext = os.path.splitext(file.name)[1].lower()
            valid_extensions = ['.csv', '.xlsx']

            if ext not in valid_extensions:
                raise ValidationError("Format non supporté. Veuillez utiliser uniquement .csv ou .xlsx")

        return file

class TemplatePartForm(forms.ModelForm):
    class Meta:
        model = TemplatePart
        fields = ['name', 'type_id', 'order', 'is_mandatory', 'include_in_output', 'is_separable']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'type_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Type'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'style': 'width: 80px'}),

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

class PlasmidForm(forms.ModelForm):
    class Meta:
        model = Plasmid
        fields = ['name', 'description', 'genbank_file']

        labels = {
            'name': 'Nom du plasmide',
            'description': 'Annotations / Notes',
            'genbank_file': 'Fichier de séquence (.gb, .fasta)'
        }

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: pYTK001_Promoteur'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Décrivez les annotations, les gènes présents...'}),
            'genbank_file': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_genbank_file(self):
        file = self.cleaned_data.get('genbank_file')

        if file:
            if not hasattr(file, 'name'):
                return file

            ext = os.path.splitext(file.name)[1].lower()
            valid_extensions = ['.gb', '.gbk', '.fasta', '.fa', '.dna', '.zip']

            if ext not in valid_extensions:
                raise ValidationError("Format non supporté. Utilisez : .gb, .fasta ou .zip")

        return file
class SimulationForm(forms.ModelForm):

    custom_enzymes = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Enzymes pour le gel"
    )

    collections = forms.ModelMultipleChoiceField(
        queryset=PlasmidCollection.objects.none(),
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

            'visibility': forms.Select(attrs={'class': 'form-select', 'id': 'id_sim_visibility'}),
            'team': forms.Select(attrs={'class': 'form-select', 'id': 'id_sim_team'}),
            'zip_file': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.zip,application/zip,application/x-zip,application/x-zip-compressed',
            'default_concentration': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': '200.0'}),
            'concentration_file': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.csv'})
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(SimulationForm, self).__init__(*args, **kwargs)
        self.fields['custom_enzymes'].choices = [
                ('BsaI', 'BsaI'), ('BsmBI', 'BsmBI'), ('NotI', 'NotI'), ('BbsI', 'BbsI'), ('SapI', 'SapI')
            ]

        # 2. Gestion de l'équipe (Sécurité)
        if user and user.is_authenticated:
            self.fields['team'].queryset = Team.objects.filter(members=user)
            self.fields['collections'].queryset = PlasmidCollection.objects.filter(
                Q(owner=user) |
                Q(publication_status='approved') | Q(team__members=user)
            ).distinct()
        else:
            self.fields['team'].queryset = Team.objects.none()
            self.fields['collections'].queryset = PlasmidCollection.objects.filter(
                publication_status='approved'
            )
        self.fields['visibility'].required = False
        self.fields['team'].required = False
        self.fields['team'].empty_label = "--- Sélectionner une équipe ---"


class FeatureEditForm(forms.Form):
    feature_identifier = forms.CharField(widget=forms.HiddenInput())

    feature_type = forms.CharField(
        label="Type",
        required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext fw-bold'})
    )
    feature_location = forms.CharField(
        label="Position",
        required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext btn-sm'})
    )

    feature_name = forms.CharField(
        label="Nom / Label",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

FeatureFormSet = forms.formset_factory(FeatureEditForm, extra=0)
