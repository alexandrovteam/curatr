import logging

import django_tables2 as tables
from django.db import OperationalError

from .models import Adduct


class MoleculeTable2(tables.Table):
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


try:
    for adduct in Adduct.objects.all().order_by("charge"):
        logging.debug(adduct)
        # dynamically add one column per adduct
        col = tables.Column(accessor='adduct_mzs_by_pk.{}'.format(adduct.pk), empty_values=(), verbose_name=str(
            adduct))
        MoleculeTable2.base_columns['adduct{}'.format(adduct.id)] = col
except OperationalError:
    pass
