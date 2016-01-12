from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Standard(models.Model):
    name = models.TextField(default = "")
    sum_formula = models.TextField(null=True)
    MCFID = models.TextField(default="")
    # todo(An)
    # Inchi, ChEBI
