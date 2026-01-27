from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import CampaignTemplate, TemplatePart, Simulation, Team
from django.forms import inlineformset_factory


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
