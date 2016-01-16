from __future__ import unicode_literals
from django.db import models
import base64
import numpy as np
import sys
sys.path.append("//Users/palmer/Documents/python_codebase/")
from pyMS.pyisocalc import pyisocalc


# Create your models here.
class Dataset(models.Model):
    name = models.TextField(default="")

    def __str__(self):
        return self.name


class Adduct(models.Model):
    formula = models.TextField(default="")
    offset = models.FloatField(default = 0.0)
    charge = models.IntegerField(default=1)

    def __str__(self):
        return self.formula

class Standard(models.Model):
    name = models.TextField(default = "")
    sum_formula = models.TextField(null=True)
    MCFID = models.TextField(default="")
    # todo(An)
    # Inchi, ChEBI
    datasets_present_in = models.ManyToManyField(Dataset,null=True,blank=True)

    def __str__(self):
        return self.name

    def get_mass(self):
        spec = pyisocalc.isodist(self.sum_formula,charges=0,do_centroid=False)
        mass = spec.get_spectrum(source='centroids')[0][np.argmax(spec.get_spectrum(source='centroids')[1])]
        return mass


class Xic(models.Model):
    mz = models.FloatField(default=0.0)
    dataset = models.ForeignKey(Dataset)
    _xic = models.TextField(
            db_column='data',
            blank=True)
    standard = models.ForeignKey(Standard,blank=True, null=True)
    adduct = models.ForeignKey(Adduct,blank=True, null=True)

    def set_xic(self, xic):
        xic = np.asarray(xic,dtype=np.float64)
        self._xic  = base64.b64encode(xic)

    def get_xic(self):
        r = base64.decodestring(self._xic)
        return np.frombuffer(r, dtype=np.float64)

    xic = property(get_xic, set_xic)

    def check_mass(self,tol_ppm=100):
        tol_mz = self.mz*tol_ppm*1e-6
        theor_mz = self.standard.get_mass() + self.adduct.offset
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
    spec_num = models.IntegerField()

    def __str__(self):
        return "{} {:3.2f}".format(self.spec_num, self.precursor)

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
