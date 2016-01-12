from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Dataset(models.Model):
    name = models.TextField(default="")

    def __str__(self):
        return self.name


class Adduct(models.Model):
    formula = models.TextField(default="")
    offset = models.FloatField(default = 0.0)
    charge = models.IntegerField(default=1)
    datasets_present_in = models.ManyToManyField(Dataset)



class Standard(models.Model):
    name = models.TextField(default = "")
    sum_formula = models.TextField(null=True)
    MCFID = models.TextField(default="")
    # todo(An)
    # Inchi, ChEBI
    datasets_present_in = models.ManyToManyField(Dataset)

    def __str__(self):
        return self.name

