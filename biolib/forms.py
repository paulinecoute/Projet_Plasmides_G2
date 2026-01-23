from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import CampaignTemplate, TemplatePart, Simulation


# FORMULAIRE D'INSCRIPTION

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
        fields = [
            'name',
            'description',
            'enzyme',
            'output_separator',
            'file',
            'is_public'  # On remplace 'visibility' par 'is_public'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }


# Cela permet d'ajouter/supprimer des parties dynamiquement
TemplatePartFormSet = forms.inlineformset_factory(
    CampaignTemplate,
    TemplatePart,
    fields=['name', 'type_id', 'order', 'is_mandatory', 'include_in_output', 'is_separable'],
    extra=1,  # Affiche une ligne vide par défaut
    can_delete=True
)

class SimulationForm(forms.ModelForm):
    class Meta:
        model = Simulation
        fields = ['template_file', 'enzyme', 'campaign_file']

    def __init__(self, *args, **kwargs):
        super(SimulationForm, self).__init__(*args, **kwargs)

        # Template -> CSV
        self.fields['template_file'].widget.attrs.update({
            'class': 'form-control',
            'accept': '.csv, .xlsx, .xls'
        })

        self.fields['enzyme'].widget.attrs.update({'class': 'form-select'})

        # Campagne -> Excel
        self.fields['campaign_file'].widget.attrs.update({
            'class': 'form-control',
            'accept': '.csv, .xls, .xlsx'
        })
