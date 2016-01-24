__author__ = 'palmer'
from django import forms
from .models import Standard, Adduct, FragmentationSpectrum
import os
import logging
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
    adducts = forms.ModelMultipleChoiceField(queryset=Adduct.objects.all())
    standards = forms.ModelMultipleChoiceField(queryset=Standard.objects.all().order_by('MCFID'))
    mass_accuracy_ppm = forms.FloatField(min_value=0.000001)
    quad_window_mz = forms.FloatField(min_value=0.000001)


class FragSpecReview(forms.Form):
    def __init__(self,*args,**kwargs):
        fragSpecId = kwargs.pop('extra')
        self.user = kwargs.pop('user', None)

        super(FragSpecReview, self).__init__(*args, **kwargs)
        for i in fragSpecId:

            logging.debug(i)
            fs = FragmentationSpectrum.objects.get(pk=i)
            logging.debug(fs.dataset)
            initial = 2
            if fs.reviewed:
                if fs.standard:
                    initial = 1
                else:
                    initial = 0


            self.fields['yesno_%s' % i] = forms.ChoiceField(choices=((1, 'Accept'), (0, 'Reject'), (2, 'Unrated')), widget=forms.RadioSelect, label=i, initial=initial)

    def get_response(self):
        for name, value in self.cleaned_data.items():
            if name.startswith('yesno_'):
                yield (self.fields[name].label, value)




