import numpy as np
from django.core.urlresolvers import reverse_lazy
from table import Table
from table.columns import Column, LinkColumn, Link
from table.utils import Accessor

from models import Standard, Adduct, Molecule, FragmentationSpectrum, Dataset


class AdductMzColumn(Column):
    def __init__(self, adduct, field):
        super(AdductMzColumn, self).__init__(header=str(adduct), field=field, sortable=False)

    def render(self, obj):
        adduct_mz = obj.molecule.adduct_mzs[self.header]
        return str(np.round(adduct_mz, decimals=5))


class StandardAdductColumn(Column):
    def render(self, spectrum):
        return "{} {}".format(spectrum.standard, spectrum.adduct.html_str)


class ReviewStatusColumn(Column):
    def render(self, spectrum):
        if spectrum.reviewed:
            if spectrum.standard == None:
                return 'Rejected'
            else:
                return 'Confirmed'
        else:
            return 'Unrated'


class DatasetStatusColumn(LinkColumn):
    def render(self, dataset):
        if dataset.processing_finished:
            return super(DatasetStatusColumn, self).render(dataset)
        else:
            return 'processing...'


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


class StandardTable(Table):
    id = LinkColumn(field='MCFID', header='Inventory ID',
                    links=[Link(text=Accessor('MCFID'), viewname='MCFStandard-detail', args=(Accessor('MCFID'),))])
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


class SpectraTable(Table):
    id = Column(field='pk', header='ID')
    precursor_mz = Column(field='precursor_mz', header='Precursor m/z')
    standard = StandardAdductColumn(field='standard_id', header='Ion')
    review_status = ReviewStatusColumn(header='Review Status', sortable=False)
    view = LinkColumn(header='', sortable=False,
                      links=[Link(text='View', viewname='fragmentSpectrum-detail', kwargs={'pk': Accessor('pk')})])

    class Meta:
        model = FragmentationSpectrum
        ajax = True
        ajax_source = reverse_lazy('spectra_table')
        sort = [(0, 'asc')]


class DatasetListTable(Table):
    id = Column(field='id', header='ID')
    name = Column(field='name', header='Dataset')
    status = DatasetStatusColumn(field='processing_finished', header='Status',
                                 links=[Link(text='View', viewname='MCFdataset-detail', args=(Accessor('pk'),))])

    class Meta:
        model = Dataset
        ajax = True
        sort = [(0, 'asc')]


for adduct in Adduct.objects.all():
    # dynamically add one column per adduct
    col = AdductMzColumn(adduct=adduct, field='molecule.adduct_mz')
    setattr(StandardTable, 'adduct{}'.format(adduct.id), col)
    StandardTable.base_columns.append(col)
    col = AdductMzColumn(adduct=adduct, field='adduct_mz')
    setattr(MoleculeTable, 'adduct{}'.format(adduct.id), col)
    MoleculeTable.base_columns.append(col)
