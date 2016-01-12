from django.test import TestCase
from models import Standard
import unittest
# Create your tests here.
class StandardModel(TestCase):
    def test_add_standard(self):
        Standard(name='TestStandard',sum_formula="C1H2O3", MCFID = "000").save()
        self.assertEqual(Standard.objects.all().count(),1)