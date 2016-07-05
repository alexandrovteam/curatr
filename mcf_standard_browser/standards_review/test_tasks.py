import logging

from django.test import TestCase

from models import Molecule, Standard
from tasks import add_batch_standard


class DataImportTest(TestCase):
    def test_batch_add(self):
        csv_filename = "./media/Standard_Library_MCF_Inhouse_metabolites.csv"
        metadata = {}
        add_batch_standard(metadata, csv_filename)
        logging.debug(Molecule.objects.all().count())
        logging.debug(Standard.objects.all().count())
        assert Standard.objects.all().count() > 0

    def test_batch_double_add(self):
        # should not produce duplicate identical entries
        csv_filename = "./media/Standard_Library_MCF_Inhouse_metabolites.csv"
        add_batch_standard({}, csv_filename)
        mol_list_1 = Molecule.objects.all().count()
        std_list_1 = Standard.objects.all().count()
        add_batch_standard({}, csv_filename)
        self.assertEqual(Molecule.objects.all().count(), mol_list_1)
        self.assertEqual(Standard.objects.all().count(), std_list_1)
