import logging

import django_tables2 as tables
import numpy as np
from django.core.urlresolvers import reverse_lazy
from django.db.utils import OperationalError
from django.utils import safestring
from table import Table
from table.columns import Column, LinkColumn, Link
from table.utils import Accessor

from models import Standard, Adduct, FragmentationSpectrum, Dataset


class AdductMzColumn(Column):
    def __init__(self, adduct, field):
        super(AdductMzColumn, self).__init__(header=adduct.html_str, field=field, sortable=False)

    def render(self, obj):
        adduct_mz = obj.molecule.adduct_mzs[self.header]
        return str(np.round(adduct_mz, decimals=5))


class AdductColumn(Column):
    def render(self, spectrum):
        return spectrum.adduct.html_str()


class DatasetStatusColumn(LinkColumn):
    def render(self, dataset):
        if dataset.processing_finished:
            return super(DatasetStatusColumn, self).render(dataset)
        else:
            return 'processing...'


class ProcessingErrorColumn(Column):
    def render(self, dataset):
        if dataset.processingerror_set.count() == 0:
            return
        else:
            return safestring.mark_safe('<div class="big-red"><strong> ! </strong></div>')


class MoleculeTable(tables.Table):
    name = tables.LinkColumn(viewname='molecule-detail', args=(tables.A('id'),), verbose_name='Name')
    formula = tables.Column(accessor='sum_formula', verbose_name='Sum Formula')
    exact_mass = tables.Column(verbose_name='Exact Mass')
    pubchem_id = tables.Column(verbose_name='Pubchem ID')
    spectra_count = tables.Column(accessor='spectra_count',
                                  order_by='-moleculespectracount.spectra_count')
    tags = tables.Column(order_by='-tags', verbose_name='Tags')

    @staticmethod
    def render_tags(value):
        if value.count() > 0:
            return ', '.join(str(v) for v in value.all())
        return '-'

    class Meta:
        order_by = ('spectra_count', 'name')


class StandardTable(tables.Table):
    id = tables.LinkColumn(accessor='inventory_id', verbose_name='Inventory ID', args=[tables.A('inventory_id')],
                           viewname='standard-detail')
    molecule_name = tables.Column(accessor='molecule.name', verbose_name='Name')
    molecular_formula = tables.Column(accessor='molecule.sum_formula', verbose_name='Formula')
    mass = tables.Column(accessor='molecule.exact_mass', verbose_name='Exact Mass')
    vendor = tables.Column(accessor='vendor', verbose_name='Vendor')
    vendor_id = tables.Column(accessor='vendor_cat', verbose_name='Vendor ID')
    pubchem_id = tables.Column(accessor='molecule.pubchem_id', verbose_name='Pubchem ID')

    class Meta:
        order_by = ('id',)


class SpectraTable(Table):
    inventory_id = Column(field='standard.inventory_id', header='Inventory ID')
    molecule = Column(field='standard.molecule.name', header='Molecule')
    precursor_mz = Column(field='precursor_mz', header='Precursor m/z')
    adduct = AdductColumn(field='adduct.delta_formula', header='Adduct')
    view = LinkColumn(header='', sortable=False, searchable=False,
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
                                 links=[Link(text='View', viewname='dataset-detail', args=(Accessor('pk'),))])
    errors = ProcessingErrorColumn(header='', searchable=False, sortable=False)

    class Meta:
        model = Dataset
        ajax = True
        sort = [(0, 'asc')]


try:
    for adduct in Adduct.objects.all().order_by("charge"):
        logging.debug(adduct)
        # dynamically add one column per adduct
        col = tables.Column(accessor='adduct_mzs_by_pk.{}'.format(adduct.pk), empty_values=(), verbose_name=str(
            adduct), orderable=False)
        MoleculeTable.base_columns['adduct{}'.format(adduct.id)] = col
except OperationalError:
    pass
