from unittest import skip

from django.conf import settings
from django.test import TestCase
from os.path import join

from models import Molecule, Standard, Dataset, Adduct
from tasks import add_batch_standard, handle_uploaded_files


class DataImportTest(TestCase):  # TODO: add test cases for overwriting existing standards
    @classmethod
    def setUpClass(cls):
        super(DataImportTest, cls).setUpClass()
        cls.csv_filepath = join(settings.MEDIA_ROOT, "Standard_Library_MCF_Inhouse_metabolites.csv")

    @skip("Would fail because spreadsheet contains errors")
    def test_batch_add(self):
        metadata = {}
        errors = add_batch_standard(metadata, open(self.csv_filepath, 'r'))
        self.assertEqual(len(errors), 0)
        self.assertEqual(Standard.objects.all().count(), 861)

    def test_batch_double_add(self):
        # should not produce duplicate identical entries
        add_batch_standard({}, open(self.csv_filepath, 'r'))
        mol_list_1 = Molecule.objects.all().count()
        std_list_1 = Standard.objects.all().count()
        add_batch_standard({}, open(self.csv_filepath, 'r'))
        self.assertEqual(Molecule.objects.all().count(), mol_list_1)
        self.assertEqual(Standard.objects.all().count(), std_list_1)


class DatasetUploadTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        csv_filepath = join(settings.MEDIA_ROOT, "Standard_Library_MCF_Inhouse_metabolites.csv")
        add_batch_standard({}, csv_filepath)
        Adduct.objects.create(nM=1, delta_formula='-H', charge=-1)
        cls.mzml_filepath = join(settings.MEDIA_ROOT, "sample.mzML")
        cls.d1 = Dataset(name='foo')
        cls.d1.save()

    def test_dataset_upload(self):
        metadata = {'mass_accuracy_ppm': 0.000001,
                    'quad_window_mz': 0.000001,
                    'standards': [x[0] for x in Standard.objects.filter(molecule__name='SUCROSE').values_list("pk")],
                    'adducts': [x[0] for x in Adduct.objects.all().values_list("pk")]}
        handle_uploaded_files(metadata, self.mzml_filepath, self.d1)
        self.assertGreater(self.d1.fragmentationspectrum_set.count(), 0)
