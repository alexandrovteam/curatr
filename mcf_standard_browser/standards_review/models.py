from __future__ import unicode_literals
from django.db import models
import logging
import base64
import numpy as np
import sys
import re
sys.path.append("//Users/palmer/Documents/python_codebase/")
from pyMS.pyisocalc import pyisocalc
import json

# Create your models here.
class Adduct(models.Model):
    nM = models.IntegerField(default=1)
    delta_formula = models.TextField(default="")# addition/loss groups per M (sum of +X-Y)
    delta_atoms = models.TextField(default="") #net atom addition/loss
    charge = models.IntegerField(default=1)#overall charge after atom change

    def __str__(self):
        return "[{}M {}]{}".format(self.nM, self.delta_formula, self.charge)

    def get_delta_atoms(self):
        self.delta_formula = self.delta_formula.strip()
        if all([self.delta_formula.startswith("+"),self.delta_formula.startswith("-")]):
            self.delta_formula = "+"+self.delta_formula
        formula_split = re.split(u'([+-])',self.delta_formula)
        el_dict = {}
        for sign,el in zip(formula_split[1::2],formula_split[2::2]):
            el_dict.update(pyisocalc.process_sf(sign+el))
        sign_dict = {1:"+",-1:"-"}
        return "".join(["{}{}{}".format(sign_dict[np.sign(el_dict[el])],el,abs(el_dict[el])) for el in el_dict if el_dict[el]!=0])

    def save(self,*args,**kwargs):
        self.delta_atoms = self.get_delta_atoms()
        super(Adduct, self).save(*args, **kwargs)

class Standard(models.Model):
    _adduct_mzs = models.TextField(default="")
    name = models.TextField(default = "")
    sum_formula = models.TextField(null=True)
    MCFID = models.TextField(default="")
    inchi_code = models.TextField(default="")
    exact_mass = models.FloatField(default=0.0)
    solubility = models.TextField(null=True, blank=True)
    # External reference numbers
    hmdb_id = models.TextField(null=True, blank=True)
    chebi_id = models.TextField(null=True, blank=True)
    lipidmaps_id = models.TextField(null=True, blank=True)
    cas_id = models.TextField(null=True, blank=True)
    pubchem_id = models.TextField(null=True, blank=True)
    vendor = models.TextField(null=True, blank=True)
    vendor_cat = models.TextField(null=True, blank=True)


    def get_adduct_mzs(self):
        return json.loads(self._adduct_mzs)

    def set_adduct_mzs(self):
        adduct_dict = {}
        for adduct in Adduct.objects.all():
            adduct_dict[str(adduct)] = self.get_mz(adduct)
        self._adduct_mzs = json.dumps(adduct_dict)

    adduct_mzs = property(get_adduct_mzs, set_adduct_mzs)


    def get_mass(self):
        spec = pyisocalc.isodist(self.sum_formula,charges=0,do_centroid=False)
        mass = spec.get_spectrum(source='centroids')[0][np.argmax(spec.get_spectrum(source='centroids')[1])]
        return mass

    def __str__(self):
        return "{} {}".format(self.MCFID,self.name)

    def save(self,*args,**kwargs):
        self.sum_formula=self.sum_formula.strip()
        self.exact_mass = self.get_mass()
        self.set_adduct_mzs()
        super(Standard, self).save(*args, **kwargs)

    def make_ion_formula(self, adduct):
        formula = "({}){}{}".format(self.sum_formula,adduct.nM,adduct.delta_atoms)
        return formula

    def get_mz(self, adduct):
        """
        Calculate the precursor mass for this standard with a given adduct
        :param adduct: object of class Adduct
        :return: float
        """
        try:
            formula = pyisocalc.complex_to_simple(self.make_ion_formula(adduct))
            spec = pyisocalc.isodist(formula,charges=adduct.charge,do_centroid=False)
            mass = spec.get_spectrum(source='centroids')[0][np.argmax(spec.get_spectrum(source='centroids')[1])]
            return mass
        except:
            logging.debug(self.name, adduct)
            return -1.




class Dataset(models.Model):
    name = models.TextField(default="")
    adducts_present = models.ManyToManyField(Adduct,blank=True)
    standards_present = models.ManyToManyField(Standard,blank=True)
    mass_accuracy_ppm = models.FloatField(default=10.0)
    quad_window_mz = models.FloatField(default=1.0)
    #(for xic search)
    def __str__(self):
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

    standard = models.ForeignKey(Standard,blank=True, null=True)
    adduct = models.ForeignKey(Adduct,blank=True, null=True)

    def set_xic(self, xic):
        xic = np.asarray(xic,dtype=np.float64)
        self._xic = base64.b64encode(xic)

    def set_rt(self,rt):
        rt = np.asarray(rt,dtype=np.float64)
        self._rt  = base64.b64encode(rt)

    def get_xic(self):
        r = base64.decodestring(self._xic)
        return np.frombuffer(r, dtype=np.float64)

    def get_rt(self):
        r = base64.decodestring(self._rt)
        return np.frombuffer(r, dtype=np.float64)

    xic = property(get_xic, set_xic)
    rt = property(get_rt, set_rt)

    def check_mass(self,tol_ppm=100):
        tol_mz = self.mz*tol_ppm*1e-6
        theor_mz = self.standard.get_mz(self.adduct)
        if np.abs(theor_mz - self.mz) > tol_mz:
            raise ValueError('Mass tolerance not satisfied {} {}'.format(theor_mz,self.mz))
        return True
        #todo(An)
    #extend save to check that standard+adduct mass == precursor




class FragmentationSpectrum(models.Model):
    precursor_mz = models.FloatField(null=True)
    _centroid_mzs = models.TextField()
    _centroid_ints = models.TextField()
    dataset = models.ForeignKey(Dataset)
    standard = models.ForeignKey(Standard,blank=True, null=True)
    adduct = models.ForeignKey(Adduct,blank=True, null=True)
    spec_num = models.IntegerField(blank=True, null=True)
    rt = models.FloatField(blank=True, null=True)
    precursor_quad_fraction = models.FloatField(blank=True, null=True)
    reviewed = models.BooleanField(default=0)

    def __str__(self):
        return "{} {:3.2f}".format(self.spec_num, self.precursor_mz)

    def set_centroid_mzs(self, mzs):
        mzs = np.asarray(mzs,dtype=np.float64)
        self._centroid_mzs = base64.b64encode(mzs)

    def get_centroid_mzs(self):
        r = base64.decodestring(self._centroid_mzs)
        return np.frombuffer(r, dtype=np.float64)

    centroid_mzs = property(get_centroid_mzs, set_centroid_mzs)

    def set_centroid_ints(self, values):
        values = np.asarray(values,dtype=np.float64)
        self._centroid_ints =  base64.b64encode(values)

    def get_centroid_ints(self):
        r = base64.decodestring(self._centroid_ints)
        return np.frombuffer(r, dtype=np.float64)

    centroid_ints = property(get_centroid_ints, set_centroid_ints)

    def get_centroids(self):
        return self.centroid_mzs, self.centroid_ints
