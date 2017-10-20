import logging

from django.test import TestCase

from standards_review.models import Molecule, Standard, Dataset, ProcessingError
from standards_review.tools import clear_molecules_without_standard, DatabaseLogHandler


class MoleculeCleanTest(TestCase):
    def test_clean_db(self):
        # clean should remove any molecules without a standard
        m1 = Molecule(name='TestMolecule1', sum_formula="C1H2O3")
        m1.save()
        m2 = Molecule(name='TestMolecule2', sum_formula="C2H2O3")
        m2.save()
        s1 = Standard(molecule=m1, inventory_id="0")
        s1.save()
        clear_molecules_without_standard()
        self.assertEqual(Molecule.objects.all().count(), 1)


class DatabaseLogHandlerTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.d1 = Dataset(name='foo')
        cls.d1.save()

    def test_writes_to_database(self):
        msg = "Foo message"
        self.assertFalse(ProcessingError.objects.filter(message=msg, dataset=self.d1).exists())
        record = logging.makeLogRecord({"msg": msg})
        h1 = DatabaseLogHandler(dataset=self.d1)
        h1.emit(record)
        self.assertTrue(ProcessingError.objects.filter(message=msg, dataset=self.d1).exists())
