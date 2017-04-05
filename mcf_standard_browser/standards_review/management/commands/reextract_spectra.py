from django.core.management.base import BaseCommand, CommandError
import logging
import traceback
from standards_review.models import Dataset
from standards_review.tools import update_spectrum_from_file

class Command(BaseCommand):
    help = 'Reinsert spectra into the database for all data files'
    def handle(self, *args, **options):
        datasets = Dataset.objects.all()
        for dataset in datasets:
            try:
                logging.debug("Updating dataset {}".format(dataset))
                update_spectrum_from_file(dataset)
            except Exception as e:
                logging.error("Error updating spectrum")
                logging.error(e, exc_info=True)
        return 0