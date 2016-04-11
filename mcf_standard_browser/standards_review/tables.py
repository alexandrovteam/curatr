import numpy as np
from django.core.urlresolvers import reverse_lazy
from table import Table
from table.columns import Column

from models import Standard, Adduct, Molecule


class AdductMzColumn(Column):
    def __init__(self, adduct, field):
        super(AdductMzColumn, self).__init__(header=str(adduct), field=field, sortable=False)

    def render(self, obj):
        adduct_mz = obj.molecule.adduct_mzs[self.header]
        return str(np.round(adduct_mz, decimals=5))


class StandardTable(Table):
    id = Column(field='MCFID', header='Inventory ID')
    molecule_name = Column(field='molecule.name', header='Name')
    molecular_formula = Column(field='molecule.sum_formula', header='Formula')
    mass = Column(field='molecule.exact_mass', header='Exact Mass')
    vendor = Column(field='vendor', header='Vendor')
    vendor_id = Column(field='vendor_cat', header='Vendor ID')
    pubchem_id = Column(field='molecule.pubchem_id', header='Pubchem ID')

    class Meta:
        model = Standard
        ajax = True
        ajax_source = reverse_lazy('standard_table')
        sort = [(0, 'asc')]


class MoleculeTable(Table):
    name = Column(field='name', header='Name')
    formula = Column(field='sum_formula', header='Formula')
    exact_mass = Column(field='exact_mass', header='Exact Mass')
    pubchem_id = Column(field='pubchem_id', header='Pubchem ID')

    class Meta:
        model = Molecule
        ajax = True
        ajax_source = reverse_lazy('molecule_table')
        sort = [(0, 'asc')]


for adduct in Adduct.objects.all():
    # dynamically add one column per adduct
    col = AdductMzColumn(adduct=adduct, field='molecule.adduct_mz')
    setattr(StandardTable, 'adduct{}'.format(adduct.id), col)
    StandardTable.base_columns.append(col)
    col = AdductMzColumn(adduct=adduct, field='adduct_mz')
    setattr(MoleculeTable, 'adduct{}'.format(adduct.id), col)
    MoleculeTable.base_columns.append(col)
