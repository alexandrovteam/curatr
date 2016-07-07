__author__ = 'palmer'
import logging

from django.contrib.auth.models import User

from .models import FragmentationSpectrum, Molecule, Standard, ProcessingError


def update_fragSpec(frag_spec_id, response, standard, adduct, username):
    fs = FragmentationSpectrum.objects.get(pk=frag_spec_id)
    logging.debug(fs.dataset)
    if response == '0':
        fs.standard = None
        fs.adduct = None
        fs.reviewed = True
    elif response == '1':
        fs.standard = standard
        fs.adduct = adduct
        fs.reviewed = True
    else:
        fs.standard = None
        fs.adduct = None
        fs.reviewed = False
    fs.last_editor = User.objects.get(username=username)
    fs.save()


def clear_molecules_without_standard():
    clean_count = 0
    remove_name = []
    for molecule in Molecule.objects.all():
        if not Standard.objects.all().filter(molecule=molecule):
            remove_name.append(molecule.name)
            molecule.delete()
            clean_count += 1
    return clean_count, remove_name


def update_mzs():
    molecules = Molecule.objects.all()
    for molecule in molecules:
        molecule.set_adduct_mzs()
        molecule.save()


class DatabaseLogHandler(logging.Handler):
    def __init__(self, dataset, level=logging.ERROR):
        super(DatabaseLogHandler, self).__init__(level=level)
        self.dataset = dataset

    def emit(self, record):
        err = ProcessingError(dataset=self.dataset, message=record.getMessage())
        err.save()
