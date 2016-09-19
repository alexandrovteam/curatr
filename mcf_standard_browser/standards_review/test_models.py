import datetime

import numpy as np
from django.test import TestCase

from models import Molecule, Standard, Dataset, Adduct, Xic, FragmentationSpectrum


# Create your tests here.
class StandardModelTest(TestCase):
    def test_add_molecule(self):
        m1 = Molecule(
            name='test_molecule',
            sum_formula='C1H2O3',
            inchi_code="str",
            solubility="none",
            hmdb_id="000235",
            chebi_id="123456",
            lipidmaps_id="558855",
            cas_id="789456",
            pubchem_id="1235")
        m1.save()
        self.assertEqual(Molecule.objects.all().count(), 1)
        self.assertAlmostEqual(m1.exact_mass, 62.00039, places=4)

    def test_add_standard(self):
        m1 = Molecule(name='test', sum_formula="C1H2O3")
        m1.save()
        s1 = Standard(
            inventory_id=0,
            molecule=m1,
            vendor="sigma",
            vendor_cat="sig0001",
            lot_num="#123456",
            location="fridge",
            purchase_date=datetime.datetime.now(),
        )
        s1.save()
        self.assertEqual(Standard.objects.all().count(), 1)
        self.assertAlmostEqual(s1.molecule.exact_mass, 62.00039, places=4)

    def test_get_mz(self):
        m1 = Molecule(name='test', sum_formula="C1H2O3")
        m1.save()
        a1 = Adduct(nM=1, delta_formula='-H', charge=-1)
        a1.save()
        s1 = Standard(molecule=m1)
        s1.save()
        self.assertEqual(Standard.objects.all().count(), 1)
        self.assertAlmostEqual(s1.molecule.get_mz(a1), 60.99311, places=4)


class AdductModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a1 = Adduct(nM=1, delta_formula='+H+K', charge=-2)
        cls.a2 = Adduct(nM=1, delta_formula='-Na-P', charge=2)
        cls.a1.save()
        cls.a2.save()

    def test_delta_atoms(self):
        self.assertEqual(self.a1.delta_atoms, "+H1+K1")
        self.assertEqual(self.a2.delta_atoms, "-Na1-P1")

    def test_nice_str(self):
        self.assertEqual(self.a1.nice_str(), "[M+H+K]-2")
        self.assertEqual(self.a2.nice_str(), "[M-Na-P]2")


class MoleculeModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Adduct.objects.create(nM=1, delta_formula='-H', charge=1)
        cls.m1 = Molecule(sum_formula="H2O")
        cls.m1.save()

    def test_mass(self):
        self.assertAlmostEqual(self.m1.get_mass(), 18.010564, places=5)
        self.assertAlmostEqual(self.m1.exact_mass, 18.010564, places=5)

    def test_adduct_mzs(self):
        self.assertAlmostEqual(self.m1.adduct_mzs['[1M-H]1'], 17.002191, places=5)


class DatasetModelTest(TestCase):
    def test_add_dataset(self):
        # create standards
        m1 = Molecule(name='TestMolecule1', sum_formula="C1H2O3")
        m1.save()
        m2 = Molecule(name='TestMolecule1', sum_formula="C2H2O3")
        m2.save()
        s1 = Standard(molecule=m1, inventory_id="0")
        s1.save()
        s2 = Standard(molecule=m2, inventory_id="1")
        s2.save()
        # create adduct
        a1 = Adduct(nM=1, delta_formula='+H+K', charge=-2)
        a1.save()
        # create a dataset
        d1 = Dataset(name='Dataset1')
        d1.save()
        d1.standards_present.add(s1)
        d1.standards_present.add(s2)
        d1.adducts_present.add(a1)
        self.assertEqual(Dataset.objects.all().count(), 1)
        self.assertEqual(Dataset.objects.all()[0].standards_present.count(), 2)


class XicModelTest(TestCase):
    def test_add_xic(self):
        m1 = Molecule(name='TestMolecule1', sum_formula="C1H2O3")
        m1.save()
        s1 = Standard(molecule=m1, inventory_id="0")
        s1.save()
        a1 = Adduct(nM=1, delta_formula='+H+K', charge=-2)
        a1.save()
        d1 = Dataset(name='Dataset1')
        d1.save()
        d1.standards_present.add(s1)
        d1.adducts_present.add(a1)
        x1 = Xic(mz='0.0', dataset=d1)
        xic = [1.0, 2.0, 3.0, 4.0, 5.0]
        x1.set_xic(xic)
        x1.save()
        self.assertEqual(Xic.objects.all().count(), 1)
        np.testing.assert_array_almost_equal(xic, x1.xic)

    def test_xic_and_standard_and_adduct(self):
        # create some datasets
        d1 = Dataset(name='Dataset1')
        d1.save()
        a1 = Adduct(nM=1, delta_formula='-H', charge=-1)
        a1.save()
        m1 = Molecule(name='TestMolecule1', sum_formula="C1H2O3")
        m1.save()
        s1 = Standard(molecule=m1, inventory_id="0")
        s1.save()
        # create some xics
        x1 = Xic(mz=60.993, dataset=d1)
        xic = [1.0, 2.0, 3.0, 4.0, 5.0]
        x1.set_xic(xic)
        x1.standard = s1
        x1.adduct = a1
        x1.save()
        self.assertEqual(Xic.objects.all().count(), 1)
        self.assertEqual(Dataset.objects.all().count(), 1)
        self.assertEqual(Standard.objects.all().count(), 1)
        # mass check
        with self.assertRaises(ValueError):
            x1.mz = 123.993
            x1.save()
            x1.check_mass()

        def test_xic_mass_filter(self):
            d1 = Dataset(name='dataset')
            d1.save()
            mz = 60.993
            # three larger
            Xic(mz=mz + 5., dataset=d1).save()
            Xic(mz=mz + 10., dataset=d1).save()
            Xic(mz=mz + 15., dataset=d1).save()
            # three approx equal
            Xic(mz=mz + 0.005, dataset=d1).save()
            Xic(mz=mz + 0.0, dataset=d1).save()
            Xic(mz=mz - 0.0015, dataset=d1).save()
            # three smaller
            Xic(mz=mz - 5., dataset=d1).save()
            Xic(mz=mz - 10., dataset=d1).save()
            Xic(mz=mz - 15., dataset=d1).save()
            # three approx equal from another dataset
            d2 = Dataset(name='dataset2')
            d2.save()
            Xic(mz=mz + 0.005, dataset=d2).save()
            Xic(mz=mz + 0.0, dataset=d2).save()
            Xic(mz=mz - 0.0015, dataset=d2).save()
            self.assertEqual(Xic.objects.all().count(), 12)
            xics = Xic.objects.all().filter(dataset=d1).filter(mz__gte=mz + 0.01).filter(mz__lte=mz - 0.01)
            self.assertEqual(xics.objects.all().count(), 3)


class FragmentationSpectrumModelTest(TestCase):
    def test_make_FragmentationSpectrum(self):
        d1 = Dataset(name='Dataset1')
        d1.save()
        FragmentationSpectrum(precursor_mz='123.456',
                              spec_num=0, dataset=d1).save()
        self.assertEqual(FragmentationSpectrum.objects.all().count(), 1)

    def test_make_FragmentationSpectrum_with_centroids(self):
        d1 = Dataset(name='Dataset1')
        d1.save()
        f1 = FragmentationSpectrum(precursor_mz='123.456',
                                   spec_num=0, dataset=d1)
        mzs = [10., 20, 50]
        ints = [1., 1., 1.]
        f1.set_centroid_mzs(mzs)
        f1.set_centroid_ints(ints)
        f1.save()
        np.testing.assert_array_almost_equal(mzs, f1.centroid_mzs)
        np.testing.assert_array_almost_equal(ints, f1.centroid_ints)


class MoleculeSpectraCountModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        d1 = Dataset(name='Dataset1')
        d1.save()
        m1 = Molecule(sum_formula='H2O')
        m1.save()
        m2 = Molecule(sum_formula='O2')
        m2.save()
        s1 = Standard(molecule=m1)
        s1.save()
        s2 = Standard(molecule=m1)
        s2.save()
        s3 = Standard(molecule=m2)
        s3.save()
        FragmentationSpectrum.objects.create(precursor_mz='123.456', spec_num=0, dataset=d1, standard=s1)
        FragmentationSpectrum.objects.create(precursor_mz='123.45', spec_num=0, dataset=d1, standard=s2)
        FragmentationSpectrum.objects.create(precursor_mz='123.4', spec_num=0, dataset=d1, standard=s3)
        cls.m_onespectrum = m2
        cls.m_twospectra = m1

    def test_counts(self):
        one_countset = self.m_onespectrum.moleculespectracount_set
        two_countset = self.m_twospectra.moleculespectracount_set
        self.assertEqual(one_countset.count(), 1)
        self.assertEqual(two_countset.count(), 1)
        one_count = one_countset.values_list()[0][1]
        two_count = two_countset.values_list()[0][1]
        self.assertEqual(one_count, 1)
        self.assertEqual(two_count, 2)
