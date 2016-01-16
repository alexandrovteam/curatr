__author__ = 'palmer'
from django import forms
from .models import Standard

class MCFStandardForm(forms.ModelForm):
    class Meta:
        model = Standard
        fields = ('MCFID','name', 'sum_formula',)