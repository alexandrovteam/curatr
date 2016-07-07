from django.conf import settings
from django.test import TestCase
from os.path import join

from models import Molecule, Standard
from tasks import add_batch_standard


class DataImportTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(DataImportTest, cls).setUpClass()
        cls.csv_filepath = join(settings.MEDIA_ROOT, "Standard_Library_MCF_Inhouse_metabolites.csv")

    def test_batch_add(self):
        metadata = {}
        add_batch_standard(metadata, open(self.csv_filepath, 'r'))
        self.assertGreater(Standard.objects.all().count(), 0)

    def test_batch_double_add(self):
        # should not produce duplicate identical entries
        add_batch_standard({}, open(self.csv_filepath, 'r'))
        mol_list_1 = Molecule.objects.all().count()
        std_list_1 = Standard.objects.all().count()
        add_batch_standard({}, open(self.csv_filepath, 'r'))
        self.assertEqual(Molecule.objects.all().count(), mol_list_1)
        self.assertEqual(Standard.objects.all().count(), std_list_1)
