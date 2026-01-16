from django import forms
from .models import CampaignTemplate, TemplatePart, Simulation


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
        fields = ['template']

    def __init__(self, *args, **kwargs):
        super(SimulationForm, self).__init__(*args, **kwargs)
        self.fields['template'].widget.attrs.update({'class': 'form-select form-select-lg'})
