import itertools

__author__ = 'palmer'
import logging

from django.contrib.auth.models import User

from standards_review.models import FragmentationSpectrum, Molecule, Standard, ProcessingError


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


def sum_of_2_perms(vals):
    return list(itertools.chain(iter(vals), map(''.join, itertools.product(vals, repeat=2))))


def update_spectrum_from_file(dataset, mzml_filepath):
    import pymzml
    import numpy as np

    if not mzml_filepath.endswith('mzML'):
        raise ValueError('wrong file extension for {}'.format(mzml_filepath))
    msrun = pymzml.run.Reader(mzml_filepath)
    for current_spectrum in FragmentationSpectrum.objects.all().filter(dataset=dataset):
        new_spectrum = msrun[current_spectrum.spec_num]
        mzs = new_spectrum.mz
        ints = new_spectrum.i
        pre_mz = float(new_spectrum['precursors'][0]['mz'])
        #
        logging.debug(current_spectrum)
        logging.debug(current_spectrum.standard)
        mz_tol_this_adduct = pre_mz * dataset.mass_accuracy_ppm * 1e-6
        mz_tol_quad = dataset.quad_window_mz
        #
        quad_ints = [ii for m, ii in zip(mzs, ints) if
                     all((m >= pre_mz - mz_tol_quad, m <= pre_mz + mz_tol_quad))]
        ppm_ints = [ii for m, ii in zip(mzs, ints) if
                    all((m >= pre_mz - mz_tol_this_adduct, m <= pre_mz + mz_tol_this_adduct))]
        if np.sum(ppm_ints) == 0:
            pre_fraction = 0
        else:
            pre_fraction = np.sum(ppm_ints) / np.sum(quad_ints)
        #
        current_spectrum.set_centroid_mzs(mzs)
        current_spectrum.set_centroid_ints(ints)
        current_spectrum.precursor_quad_fraction = pre_fraction
        current_spectrum.save()
    return 0