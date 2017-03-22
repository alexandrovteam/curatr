from __future__ import unicode_literals
import base64
import datetime
import json
import logging
from urllib2 import Request, urlopen

from django.db.models import Max
from django.utils import safestring
import numpy as np
import re
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from pyMSpec.pyisocalc import pyisocalc

# Create your models here.
class Adduct(models.Model):
    nM = models.IntegerField(default=1)
    delta_formula = models.TextField(default="")  # addition/loss groups per M (sum of +X-Y)
    delta_atoms = models.TextField(default="")  # net atom addition/loss
    charge = models.IntegerField(default=1)  # overall charge after atom change

    def charge_str(self):
        if np.sign(self.charge) == 1:
            c_sign = "+"
        else:
            c_sign = "-"
        n_charges = np.abs(self.charge)
        if n_charges == 1:
            n_charges=""
        return "{}{}".format(n_charges,c_sign)

    def nice_str(self):
        _nM = self.nM
        _charge = self.charge
        if _nM == 1:
            _nM = ""
        if np.abs(_charge) == 1:
            _charge = self.charge_str()
        return "[{}M{}]{}".format(_nM, self.delta_formula, _charge)

    def html_str(self):
        return safestring.mark_safe("[{}M{}]<sup>{}</sup>".format(self.nM, self.delta_formula, self.charge_str()).replace("1", ""))

    def __unicode__(self):
        #!! don't edit this - I'm an idiot so it's used as a key in Molecule!!#
        return "[{}M{}]{}".format(self.nM, self.delta_formula, self.charge)

    def get_delta_atoms(self):
        def addElement(elDict, element, number):
            elDict.setdefault(element, []).append(number)

        self.delta_formula = self.delta_formula.strip()
        if all([self.delta_formula.startswith("+"), self.delta_formula.startswith("-")]):
            self.delta_formula = "+" + self.delta_formula
        formula_split = re.split(u'([+-])', self.delta_formula)
        logging.debug(formula_split)
        el_dict = {}
        for sign, el in zip(formula_split[1::2], formula_split[2::2]):
            this_el_dict = dict([(segment.element().name(), int("{}1".format(sign)) * segment.amount()) for segment in
                                 pyisocalc.parseSumFormula(el).get_segments()])
            for this_el in this_el_dict:
                logging.debug(el_dict)
                addElement(el_dict, this_el, this_el_dict[this_el])
        sign_dict = {1: "+", -1: "-"}
        for this_el in el_dict:
            el_dict[this_el] = sum(el_dict[this_el])
        logging.debug(el_dict)
        el_string = "".join(["{}{}{}".format(sign_dict[np.sign(el_dict[el])], el, abs(el_dict[el])) for el in el_dict if
                             el_dict[el] != 0])
        logging.debug(el_string)
        return el_string

    def save(self, *args, **kwargs):
        self.delta_atoms = self.get_delta_atoms()
        super(Adduct, self).save(*args, **kwargs)


class Molecule(models.Model):
    _adduct_mzs = models.TextField(default="")
    name = models.TextField(default="")
    sum_formula = models.TextField(null=True)
    inchi_code = models.TextField(default="")
    exact_mass = models.FloatField(default=0.0)
    solubility = models.TextField(null=True, blank=True)
    # External reference numbers
    hmdb_id = models.TextField(null=True, blank=True)
    chebi_id = models.TextField(null=True, blank=True)
    lipidmaps_id = models.TextField(null=True, blank=True)
    cas_id = models.TextField(null=True, blank=True)
    pubchem_id = models.TextField(null=True, blank=True)
    tags = models.ManyToManyField('MoleculeTag', blank=True)
    natural_product = models.BooleanField(default=True)

    def get_adduct_mzs(self):
        return json.loads(self._adduct_mzs)

    def set_adduct_mzs(self):
        adduct_dict = {}
        for adduct in Adduct.objects.all():
            adduct_dict[str(adduct)] = self.get_mz(adduct)
        self._adduct_mzs = json.dumps(adduct_dict)

    def get_adduct_mzs_by_pk(self):
        by_str = self.get_adduct_mzs()
        return {add.pk: by_str[str(add)] for add in Adduct.objects.all()}

    adduct_mzs = property(get_adduct_mzs, set_adduct_mzs)
    adduct_mzs_by_pk = property(get_adduct_mzs_by_pk)

    def get_mass(self):
        logging.info(self.sum_formula)
        logging.info(pyisocalc.parseSumFormula(self.sum_formula))
        spec = pyisocalc.perfect_pattern(pyisocalc.parseSumFormula(self.sum_formula), charge=0)
        logging.info(spec)
        mass = spec.get_spectrum(source='centroids')[0][np.argmax(spec.get_spectrum(source='centroids')[1])]
        logging.info(mass)
        return mass

    def __unicode__(self):
        return u"".join([i for i in self.name if ord(i) < 128])

    def html_str(self):
        return safestring.mark_safe("{}".format(self.name))

    def save(self, *args, **kwargs):
        logging.info('starting save')
        self.sum_formula = self.sum_formula.strip()
        logging.info('starting sf')
        self.exact_mass = self.get_mass()
        logging.info('starting adduct')
        self.set_adduct_mzs()
        logging.info('ready to save')
        super(Molecule, self).save(*args, **kwargs)

    def make_ion_formula(self, adduct):
        formula = "({}){}{}".format(self.sum_formula, adduct.nM, adduct.delta_atoms)
        return formula

    def get_mz(self, adduct):
        """
        Calculate the precursor mass for this molecule with a given adduct
        :param adduct: object of class Adduct
        :return: float
        """
        try:
            formula = self.make_ion_formula(adduct)
            spec = pyisocalc.perfect_pattern(pyisocalc.parseSumFormula(formula), charge=adduct.charge)
            mass = spec.get_spectrum(source='centroids')[0][np.argmax(spec.get_spectrum(source='centroids')[1])]
            return mass
        except:
            logging.debug(self.name, adduct)
            return -1.

    def spectra_count(self):
        return FragmentationSpectrum.objects.all().filter(standard__molecule=self).count()

    @property
    def smiles(self):
        import pybel
        try:
            return pybel.readstring(b'inchi', self.inchi_code.encode('ascii')).write(b'smi').strip()
        except IOError:
            logging.error('Could not read InChI code: {}'.format(self.inchi_code))
            return '??'


class Standard(models.Model):
    inventory_id = models.IntegerField(db_column='MCFID', unique=True)
    molecule = models.ForeignKey(Molecule)
    vendor = models.TextField(null=True, blank=True)
    vendor_cat = models.TextField(null=True, blank=True)
    lot_num = models.TextField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    purchase_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.inventory_id is None:
            standards = Standard.objects.all()
            max_ = standards.aggregate(Max('inventory_id'))['inventory_id__max']
            if max_ is None:  # if there are no standards
                max_ = 0
            self.inventory_id = max_ + 1
        super(Standard, self).save(*args, **kwargs)

    def __unicode__(self):
        return "{}: {}".format(self.inventory_id, self.molecule.name)


class LcInfo(models.Model):
    content = models.TextField()

    def __unicode__(self):
        return self.content


class MsInfo(models.Model):
    content = models.TextField()

    def __unicode__(self):
        return self.content


class InstrumentInfo(models.Model):
    content = models.TextField()

    def __unicode__(self):
        return self.content


class Dataset(models.Model):
    processing_finished = models.BooleanField(default=False)
    name = models.TextField(default="")
    path = models.TextField(default="")
    adducts_present = models.ManyToManyField(Adduct, blank=True)
    standards_present = models.ManyToManyField(Standard, blank=True)
    mass_accuracy_ppm = models.FloatField(default=10.0)
    quad_window_mz = models.FloatField(default=1.0)
    lc_info = models.ManyToManyField(to=LcInfo)
    ms_info = models.ManyToManyField(to=MsInfo)
    instrument_info = models.ManyToManyField(to=InstrumentInfo)
    ionization_method = models.TextField(default="")
    ion_analyzer = models.TextField(default="")
    date_added = models.DateTimeField(auto_now_add=True, blank=True)
    date_modified = models.DateTimeField(auto_now=True, blank=True)

    # (for xic search)
    def __unicode__(self):
        return self.name


class Xic(models.Model):
    mz = models.FloatField(default=0.0)
    dataset = models.ForeignKey(Dataset)
    _xic = models.TextField(
        db_column='data',
        blank=True)
    _rt = models.TextField(
        db_column='rt_data',
        blank=True)

    standard = models.ForeignKey(Standard, blank=True, null=True)
    adduct = models.ForeignKey(Adduct, blank=True, null=True)
    collision = models.TextField(default='')

    def set_xic(self, xic):
        xic = np.asarray(xic, dtype=np.float64)
        self._xic = base64.b64encode(xic)

    def set_rt(self, rt):
        rt = np.asarray(rt, dtype=np.float64)
        self._rt = base64.b64encode(rt)

    def get_xic(self):
        r = base64.decodestring(self._xic)
        return np.frombuffer(r, dtype=np.float64)

    def get_rt(self):
        r = base64.decodestring(self._rt)
        return np.frombuffer(r, dtype=np.float64)

    xic = property(get_xic, set_xic)
    rt = property(get_rt, set_rt)

    def check_mass(self, tol_ppm=100):
        tol_mz = self.mz * tol_ppm * 1e-6
        theor_mz = self.standard.molecule.get_mz(self.adduct)
        if np.abs(theor_mz - self.mz) > tol_mz:
            raise ValueError('Mass tolerance not satisfied {} {}'.format(theor_mz, self.mz))
        return True
        # todo(An)
        # extend save to check that standard+adduct mass == precursor


class FragmentationSpectrum(models.Model):
    precursor_mz = models.FloatField(null=True)
    ms1_intensity = models.FloatField(default=0.0)
    _centroid_mzs = models.TextField()
    _centroid_ints = models.TextField()
    collision_energy = models.TextField(default="")
    dataset = models.ForeignKey(Dataset)
    standard = models.ForeignKey(Standard, blank=True, null=True)
    adduct = models.ForeignKey(Adduct, blank=True, null=True)
    spec_num = models.IntegerField(blank=True, null=True)
    rt = models.FloatField(blank=True, null=True)
    precursor_quad_fraction = models.FloatField(blank=True, null=True)
    reviewed = models.BooleanField(default=0)
    date_added = models.DateField(default=timezone.now)
    date_edited = models.DateField(default=timezone.now)
    last_editor = models.ForeignKey(User, blank=True, null=True)
    _splash = models.TextField(default='', null=True)

    def __unicode__(self):
        return "{} {:3.2f}".format(self.spec_num, self.precursor_mz)

    def set_centroid_mzs(self, mzs):
        mzs = np.asarray(mzs, dtype=np.float64)
        self._centroid_mzs = base64.b64encode(mzs)

    def get_centroid_mzs(self):
        r = base64.decodestring(self._centroid_mzs)
        return np.frombuffer(r, dtype=np.float64)

    centroid_mzs = property(get_centroid_mzs, set_centroid_mzs)

    def set_centroid_ints(self, values):
        values = np.asarray(values, dtype=np.float64)
        self._centroid_ints = base64.b64encode(values)

    def get_centroid_ints(self):
        r = base64.decodestring(self._centroid_ints)
        return np.frombuffer(r, dtype=np.float64)

    centroid_ints = property(get_centroid_ints, set_centroid_ints)

    def get_centroids(self):
        return self.centroid_mzs, self.centroid_ints

    def save(self, *args, **kwargs):
        logging.debug(self.pk)
        if not self.pk:
            self.date_added = datetime.datetime.now()
        self.date_edited = datetime.datetime.now()
        super(FragmentationSpectrum, self).save(*args, **kwargs)

    @property
    def base_peak(self):
        spec = self.get_centroids()
        return spec[0][np.argmax(spec[1])]

    @property
    def splash(self):
        if self._splash == "":
            response = self.get_splash()
            if response.startswith('splash'):
                self._splash = response
        return self._splash

    def get_splash(self):
        splash_payload = json.dumps({
            "ions": [{"mass": mz, "intensity": int_} for mz, int_ in zip(self.centroid_mzs, self.centroid_ints)],
            "type": "MS"})
        url = "http://splash.fiehnlab.ucdavis.edu/splash/it"
        request = Request(url, data=splash_payload, headers={'Content-Type': "application/json"})
        response = urlopen(request).read().decode()
        return response

    @property
    def massbank_accession(self): # return a six digit number
        return "{:06.0f}".format(self.id % 999999) #horrible hack


class MoleculeSpectraCount(models.Model):
    molecule = models.ForeignKey(Molecule, primary_key=True, on_delete=models.DO_NOTHING)
    spectra_count = models.IntegerField()

    class Meta:
        managed = False


class ProcessingError(models.Model):
    dataset = models.ForeignKey(Dataset)
    message = models.TextField()


class MoleculeTag(models.Model):
    name = models.TextField()

    def __unicode__(self):
        return self.name
