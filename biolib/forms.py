from django import forms
from django.forms import inlineformset_factory
from .models import CampaignTemplate, TemplatePart


class CampaignTemplateForm(forms.ModelForm):
    class Meta:
        model = CampaignTemplate
        fields = ['name', 'description', 'enzyme', 'visibility']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'enzyme': forms.Select(attrs={'class': 'form-select'}),
            'visibility': forms.Select(attrs={'class': 'form-select'}),
        }

class TemplatePartForm(forms.ModelForm):
    class Meta:
        model = TemplatePart
        fields = ['name', 'type_id', 'order', 'is_mandatory', 'is_separable', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'type_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Type'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Desc.'}),
            'is_mandatory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_separable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

TemplatePartFormSet = inlineformset_factory(
    CampaignTemplate,
    TemplatePart,
    form=TemplatePartForm,
    extra=1,
    can_delete=True
)
