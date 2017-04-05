from django.core.management.base import BaseCommand, CommandError
import logging
import traceback
from standards_review.models import FragmentationSpectrum

class Command(BaseCommand):
    help = 'Delete any spectra that have not been curated and allocated a standard'
    def handle(self, *args, **options):
        var = raw_input("This will delete *all* spectra without a standard assigned. Are you sure [y/N]: ")
        if var == 'y':
            std_del = FragmentationSpectrum.objects.exclude(standard__isnull=False).delete()
            adduct_del = FragmentationSpectrum.objects.exclude(adduct__isnull=False).delete()
        else:
            logging.debug('remove unassigned spectra cancelled')
        return std_del, adduct_del
