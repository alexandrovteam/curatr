from django.test import TestCase
from models import Standard, Dataset, Adduct, Xic, FragmentationSpectrum
import numpy as np
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


class AdductModelTest(TestCase):
    def test_add_standard(self):
        Adduct(formula='-H',offset=-1.0003, charge=-1).save()
        self.assertEqual(Adduct.objects.all().count(),1)

    def test_standard_and_dataset(self):
        # create some datasets
        d1 = Dataset(name='Dataset1')
        d1.save()
        d2 = Dataset(name='Dataset1')
        d2.save()
        # create some standards
        a1 = Adduct(formula='-2H',offset=-2.0006, charge=-2)
        a1.save()
        a1.datasets_present_in.add(d1)
        a1.datasets_present_in.add(d2)
        a2 = Adduct(formula='-3H',offset=-3.0009, charge=-3)
        a2.save()
        a2.datasets_present_in.add(d2)
        a2.datasets_present_in.create(name='Dataset3')
        a1.save()
        a2.save()
        self.assertEqual(Adduct.objects.all().count(),2)
        self.assertEqual(Dataset.objects.all().count(),3)
        self.assertEqual(d2.adduct_set.all().count(),2)

class XicModelTest(TestCase):
    def test_add_xic(self):
        d1 = Dataset(name='Dataset1')
        d1.save()
        x1 = Xic(mz='0.0',dataset=d1)
        xic = [1.0,2.0,3.0,4.0,5.0]
        x1.set_xic(xic)
        x1.save()
        self.assertEqual(Xic.objects.all().count(),1)
        np.testing.assert_array_almost_equal(xic,x1.xic)

    def test_xic_and_standard_and_adduct(self):
        # create some datasets
        d1 = Dataset(name='Dataset1')
        d1.save()
        a1 = Adduct(formula='-H',offset=-1.007, charge=-1)
        a1.save()
        a1.datasets_present_in.add(d1)
        s1 = Standard(name='Standard1',sum_formula="C1H2O3", MCFID = "00")
        s1.save()
        # create some xics
        x1 = Xic(mz= 60.993,dataset=d1)
        xic = [1.0,2.0,3.0,4.0,5.0]
        x1.set_xic(xic)
        x1.standard = s1
        x1.adduct = a1
        x1.save()
        self.assertEqual(x1.check_mass(),True)
        self.assertEqual(Xic.objects.all().count(),1)
        self.assertEqual(Dataset.objects.all().count(),1)
        self.assertEqual(Standard.objects.all().count(),1)
        # mass check
        with self.assertRaises(ValueError):
            x1.mz = 123.993
            x1.save()
            x1.check_mass()

class FragmentationSpectrumModelTest(TestCase):
    def test_make_FragmentationSpectrum(self):
        d1 = Dataset(name='Dataset1')
        d1.save()
        FragmentationSpectrum(precursor_mz='123.456',
                              spec_num = 0, dataset=d1).save()
        self.assertEqual(FragmentationSpectrum.objects.all().count(),1)

    def test_make_FragmentationSpectrum_with_centroids(self):
        d1 = Dataset(name='Dataset1')
        d1.save()
        f1 = FragmentationSpectrum(precursor_mz='123.456',
                              spec_num = 0, dataset=d1)
        mzs = [10.,20,50]
        ints = [1.,1.,1.]
        f1.set_centroid_mzs(mzs)
        f1.set_centroid_ints(ints)
        f1.save()
        np.testing.assert_array_almost_equal(mzs,f1.centroid_mzs)
        np.testing.assert_array_almost_equal(ints,f1.centroid_ints)

