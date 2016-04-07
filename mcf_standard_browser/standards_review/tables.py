from django.core.urlresolvers import reverse_lazy
from table import Table
from table.columns import Column

from models import Standard


class AdductMzsColumn(Column):
    def render(self, obj):
        adduct_mzs = obj.molecule.adduct_mzs
        return '\n'.join('{}: {}'.format(k, v) for k, v in adduct_mzs.items())


class StandardTable(Table):
    id = Column(field='MCFID', header='Inventory ID')
    molecule_name = Column(field='molecule.name', header='Name')
    molecular_formula = Column(field='molecule.sum_formula', header='Formula')
    mass = Column(field='molecule.exact_mass', header='Exact Mass')
    vendor = Column(field='vendor', header='Vendor')
    vendor_id = Column(field='vendor_cat', header='Vendor ID')
    pubchem_id = Column(field='molecule.pubchem_id', header='Pubchem ID')
    adducts = AdductMzsColumn(field='molecule.adduct_mzs', header='Adduct m/z')

    class Meta:
        model = Standard
        ajax = True
        ajax_source = reverse_lazy('standard_table')
        sort = [(0, 'asc')]
