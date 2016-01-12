from django.test import TestCase
from models import Standard, Dataset
import unittest
# Create your tests here.

class DatasetModelTest(TestCase):
    def test_add_dataset(self):
        Dataset(name='TestDataset').save()
        self.assertEqual(Dataset.objects.all().count(),1)


class StandardModelTest(TestCase):
    def test_add_standard(self):
        Standard(name='TestStandard',sum_formula="C1H2O3", MCFID = "0").save()
        self.assertEqual(Standard.objects.all().count(),1)

    def test_standard_and_dataset(self):
        # create some datasets
        d1 = Dataset(name='Dataset1')
        d1.save()
        d2 = Dataset(name='Dataset1')
        d2.save()
        # create some standards
        s1 = Standard(name='Standard1',sum_formula="C1H2O3", MCFID = "00")
        s1.save()
        s1.datasets_present_in.add(d1)
        s1.datasets_present_in.add(d2)
        s2 = Standard(name='Standard2',sum_formula="C1H2O3", MCFID = "000")
        s2.save()
        s2.datasets_present_in.add(d2)
        s2.datasets_present_in.create(name='Dataset3')
        s1.save()
        s2.save()
        self.assertEqual(Standard.objects.all().count(),2)
        self.assertEqual(Dataset.objects.all().count(),3)
        self.assertEqual(d2.standard_set.all().count(),2)