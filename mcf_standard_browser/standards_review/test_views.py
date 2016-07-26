import datetime

from django.conf import settings
from django.test import Client
from django.test import TestCase
from os.path import join

from models import Molecule, FragmentationSpectrum, Dataset
from models import Standard
from tasks import add_batch_standard


class StandardListTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        cls.csv_filepath = join(settings.MEDIA_ROOT, "Standard_Library_MCF_Inhouse_metabolites.csv")

    def test_empty(self):
        standard_table = self.client.get('/inventory/').context['standard_list']
        self.assertEqual(len(standard_table.rows), 0)

    def test_single(self):
        m1 = Molecule(name='test', sum_formula="C1H2O3")
        m1.save()
        s1 = Standard(
            MCFID=0,
            molecule=m1,
            vendor="sigma",
            vendor_cat="sig0001",
            lot_num="#123456",
            location="fridge",
            purchase_date=datetime.datetime.now(),
        )
        s1.save()
        standard_table = self.client.get('/inventory/').context['standard_list']
        self.assertEqual(len(standard_table.rows), 1)

    def test_all(self):
        add_batch_standard({}, open(self.csv_filepath, 'r'))
        standard_table = self.client.get('/inventory/').context['standard_list']
        self.assertEqual(len(standard_table.rows), Standard.objects.count())


class MoleculeListTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        cls.csv_filepath = join(settings.MEDIA_ROOT, "Standard_Library_MCF_Inhouse_metabolites.csv")

    def get_table_and_count(self):
        context = self.client.get('/molecule/').context
        molecule_table = context['molecule_list']
        molecules_with_spectra = context['molecules_with_spectra']
        return molecule_table, molecules_with_spectra

    def assert_empty(self):
        molecule_table, molecules_with_spectra = self.get_table_and_count()
        self.assertEqual(len(molecule_table.rows), 0)
        self.assertEqual(molecules_with_spectra, 0)

    def test_empty(self):
        self.assert_empty()

    def test_is_empty_if_no_spectra(self):
        m1 = Molecule(name='test', sum_formula="C1H2O3")
        m1.save()
        s1 = Standard(molecule=m1)
        s1.save()
        molecule_table, molecules_with_spectra = self.get_table_and_count()
        self.assertEqual(len(molecule_table.rows), 1)
        self.assertEqual(molecules_with_spectra, 0)

    def test_is_empty_if_nothing_annotated(self):
        m1 = Molecule(name='test', sum_formula="C1H2O3")
        m1.save()
        s1 = Standard(molecule=m1)
        s1.save()
        d1 = Dataset()
        d1.save()
        fs1 = FragmentationSpectrum(ms1_intensity=42, dataset=d1)
        fs1.save()
        molecule_table, molecules_with_spectra = self.get_table_and_count()
        self.assertEqual(len(molecule_table.rows), 1)
        self.assertEqual(molecules_with_spectra, 0)

    def test_is_not_empty_if_annotated(self):
        m1 = Molecule(name='test', sum_formula="C1H2O3")
        m1.save()
        s1 = Standard(molecule=m1)
        s1.save()
        d1 = Dataset()
        d1.save()
        fs1 = FragmentationSpectrum(ms1_intensity=42, dataset=d1, standard=s1)
        fs1.save()
        molecule_table, molecules_with_spectra = self.get_table_and_count()
        self.assertEqual(len(molecule_table.rows), 1)
        self.assertEqual(molecules_with_spectra, 1)
