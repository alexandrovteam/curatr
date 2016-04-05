__author__ = 'palmer'
import logging

import numpy as np
from django.contrib.auth.models import User

from .models import FragmentationSpectrum, Molecule


class ChartData(object):
    @classmethod
    def get_avg_by_day(cls,):
        data = {'dates': range(20), 'values': np.random.rand(20)}
        return data

def update_fragSpec(fragSpecId,response, standard, adduct, username):
    fs = FragmentationSpectrum.objects.get(pk=fragSpecId)
    logging.debug(fs.dataset)
    if response == '0':
        fs.standard = None
        fs.adduct = None
        fs.reviewed = True
    elif response == '1':
        fs.standard=standard
        fs.adduct=adduct
        fs.reviewed = True
    else:
        fs.standard = None
        fs.adduct = None
        fs.reviewed = False
    fs.last_editor = User.objects.get(username=username)
    fs.save()


def pipe_file_to_disk(filename, file):
    with open(filename, 'w') as destination:
        for chunk in file.chunks():
            destination.write(chunk)


def to_unicode(s):
    return s.encode("utf-8", errors="ignore")


def update_mzs():
    molecules = Molecule.objects.all()
    for molecule in molecules:
        molecule.set_adduct_mzs()
        molecule.save()
