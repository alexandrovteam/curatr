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

        parser.add_argument(
            '--path_swap',
            action='store_true',
            dest='path_swap_new',
            default=False,
            help='Remove existing path and replace with this directory',
        )


    def handle(self, *args, **options):
        datasets = Dataset.objects.all()
        for dataset in datasets:
            try:
                if options['check_files']:
                    path = dataset.path
                    if options['path_swap_new']:
                        path = self.path_swap(dataset.path, options["path_swap_old"], options["path_swap_new"])
                    logging.debug((path, os.path.exists(path)))
                else:
                    logging.debug(dataset.path)
                    update_spectrum_from_file(dataset)
            except Exception as e:
                logging.error("Error updating spectrum")
                logging.error(e, exc_info=True)

    def path_swap(self, path, path_swap_new):
        path = os.path.split(path)[1]
        return os.path.join(path_swap_new, path)