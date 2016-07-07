from django.test import TestCase

from models import Molecule, Standard
from tools import clear_molecules_without_standard


class MoleculeCleanTest(TestCase):
    def test_clean_db(self):
        # clean should remove any molecules without a standard
        m1 = Molecule(name='TestMolecule1', sum_formula="C1H2O3")
        m1.save()
        m2 = Molecule(name='TestMolecule2', sum_formula="C2H2O3")
        m2.save()
        s1 = Standard(molecule=m1, MCFID="0")
        s1.save()
        clear_molecules_without_standard()
        self.assertEqual(Molecule.objects.all().count(), 1)
