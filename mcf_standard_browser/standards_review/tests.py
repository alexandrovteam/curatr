from django.test import TestCase
from models import Standard, Dataset, Adduct, Xic, FragmentationSpectrum
import numpy as np
# Create your tests here.
class StandardModelTest(TestCase):
    def test_add_standard(self):
        s1 = Standard(name='TestStandard',sum_formula="C1H2O3", MCFID = "0")
        s1.save()
        self.assertEqual(Standard.objects.all().count(),1)
        self.assertAlmostEqual(s1.exact_mass,62.00039,places=4)

    def test_get_mz(self):
        a1=Adduct(nM=1, delta_formula='-H', charge=-1)
        a1.save()
        s1 = Standard(name='TestStandard',sum_formula="C1H2O3", MCFID = "0")
        s1.save()
        self.assertEqual(Standard.objects.all().count(),1)
        self.assertAlmostEqual(s1.get_mz(a1),60.99311,places=4)


class AdductModelTest(TestCase):
    def test_add_standard(self):
        a1=Adduct(nM=1, delta_formula='+H+K', charge=-2)
        a1.save()
        a2=Adduct(nM=1, delta_formula='-Na-P', charge=2)
        a2.save()
        self.assertEqual(a1.delta_atoms,"+H1+K1")
        self.assertEqual(a2.delta_atoms,"-Na1-P1")
        self.assertEqual(Adduct.objects.all().count(), 2)


class DatasetModelTest(TestCase):
    def test_add_dataset(self):
        # create standards
        s1 = Standard(name='TestStandard1',sum_formula="C1H2O3", MCFID = "0")
        s1.save()
        s2 = Standard(name='TestStandard2',sum_formula="C2H2O3", MCFID = "1")
        s2.save()
        # create adduct
        a1=Adduct(nM=1, delta_formula='+H+K', charge=-2)
        a1.save()
        # create a dataset
        d1 = Dataset(name='Dataset1')
        d1.save()
        d1.standards_present.add(s1)
        d1.standards_present.add(s2)
        d1.adducts_present.add(a1)
        self.assertEqual(Dataset.objects.all().count(), 1)
        self.assertEqual(Dataset.objects.all()[0].standards_present.count(),2)

class XicModelTest(TestCase):
    def test_add_xic(self):
        s1 = Standard(name='TestStandard1',sum_formula="C1H2O3", MCFID = "0")
        s1.save()
        a1=Adduct(nM=1, delta_formula='+H+K', charge=-2)
        a1.save()
        d1 = Dataset(name='Dataset1')
        d1.save()
        d1.standards_present.add(s1)
        d1.adducts_present.add(a1)
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
        a1=Adduct(nM=1, delta_formula='-H', charge=-1)
        a1.save()
        s1 = Standard(name='Standard1',sum_formula="C1H2O3", MCFID = "00")
        s1.save()
        # create some xics
        x1 = Xic(mz= 60.993,dataset=d1)
        xic = [1.0,2.0,3.0,4.0,5.0]
        x1.set_xic(xic)
        x1.standard = s1
        x1.adduct = a1
        x1.save()
        self.assertEqual(Xic.objects.all().count(),1)
        self.assertEqual(Dataset.objects.all().count(),1)
        self.assertEqual(Standard.objects.all().count(),1)
        # mass check
        with self.assertRaises(ValueError):
            x1.mz = 123.993
            x1.save()
            x1.check_mass()

        def test_xic_mass_filter(self):
            d1=Dataset(name='dataset')
            d1.save()
            mz = 60.993
            # three larger
            Xic(mz= mz+5.,dataset=d1).save()
            Xic(mz= mz+10.,dataset=d1).save()
            Xic(mz= mz+15.,dataset=d1).save()
            # three approx equal
            Xic(mz= mz+0.005,dataset=d1).save()
            Xic(mz= mz+0.0,dataset=d1).save()
            Xic(mz= mz-0.0015,dataset=d1).save()
            # three smaller
            Xic(mz= mz-5.,dataset=d1).save()
            Xic(mz= mz-10.,dataset=d1).save()
            Xic(mz= mz-15.,dataset=d1).save()
            # three approx equal from another dataset
            d2=Dataset(name='dataset2')
            d2.save()
            Xic(mz= mz+0.005,dataset=d2).save()
            Xic(mz= mz+0.0,dataset=d2).save()
            Xic(mz= mz-0.0015,dataset=d2).save()
            self.assertEqual(Xic.objects.all().count(),12)
            xics=Xic.objects.all().filter(dataset=d1).filter(mz__gte=mz+0.01).filter(mz__lte=mz-0.01)
            self.assertEqual(xics.objects.all().count(),3)


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

