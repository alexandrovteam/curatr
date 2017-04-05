from django.core.management.base import BaseCommand, CommandError
import logging
import os
from standards_review.models import Dataset
from standards_review.tools import update_spectrum_from_file

class Command(BaseCommand):
    help = 'Reinsert spectra into the database for all data files'
    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--check_files',
            action='store_true',
            dest='check_files',
            default=False,
            help='Just check which files are present',
        )
    def handle(self, *args, **options):
        datasets = Dataset.objects.all()
        for dataset in datasets:
            try:
                logging.debug("Updating dataset {}".format(dataset))
                if options['check_files']:
                    logging.debug(dataset.path, os.path.exists(dataset.path))
                else:
                    update_spectrum_from_file(dataset)
            except Exception as e:
                logging.error("Error updating spectrum")
                logging.error(e, exc_info=True)
        return 0