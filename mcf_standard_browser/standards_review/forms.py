__author__ = 'palmer'
from django import forms
from .models import Standard, Adduct
import os

class MCFStandardForm(forms.ModelForm):
    class Meta:
        model = Standard
        fields = ('MCFID','name', 'sum_formula',)


class ExtFileField(forms.FileField):
    """
    Same as forms.FileField, but you can specify a file extension whitelist.
    expects ext_whitelist in kwargs
    """
    def __init__(self, *args, **kwargs):
        ext_whitelist = kwargs.pop("ext_whitelist")
        self.ext_whitelist = [i.lower() for i in ext_whitelist]
        super(ExtFileField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super(ExtFileField, self).clean(*args, **kwargs)
        filename = data.name
        ext = os.path.splitext(filename)[1]
        ext = ext.lower()
        if ext not in self.ext_whitelist:
            raise forms.ValidationError("Not allowed filetype!")


class UploadFileForm(forms.Form):
    mzml_file = forms.FileField()
    adduct_choices = [(adduct.pk, adduct) for adduct in Adduct.objects.all()]
    adducts = forms.MultipleChoiceField(choices=adduct_choices, widget=forms.CheckboxSelectMultiple())
    standard_choices = [(standard.pk, standard) for standard in Standard.objects.all()]
    standards = forms.MultipleChoiceField(choices=standard_choices, widget=forms.CheckboxSelectMultiple())
    mass_accuracy_ppm = forms.FloatField(min_value=0.000001)
    quad_window_mz = forms.FloatField(min_value=0.000001)

