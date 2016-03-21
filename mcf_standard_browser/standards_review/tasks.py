import logging

import dateutil
import os
from celery import shared_task
from django.conf import settings

from models import Molecule, Standard
from tools import pipe_file_to_disk


@shared_task
def process_batch_standard(metadata, file_):
    """
    handle a csv fil of standards
    header line should be "mcfid","name","formula", "inchi", "solubility", "vendor","vendor_id", "hmdb_id" , "chebi_id", "lipidmaps_id", "cas_id", "pubchem_id". "date","location","lot_num"

    To Be Set:
    ### Standard
    # mandatory
    molecule = models.ForeignKey(Molecule, default=Molecule.objects.all().filter(name='DUMMY'))
    MCFID = models.IntegerField(null=True, blank=True)# if blank MCFID == Standard.pk
    # optional
    vendor = models.TextField(null=True, blank=True)
    vendor_cat = models.TextField(null=True, blank=True)
    lot_num = models.TextField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    purchase_date = models.DateField(null=True, blank=True)

    If Not Existing:
    ### Molecule
    # mandatory
    name = models.TextField(default = "")
    sum_formula = models.TextField(null=True)
    pubchem_id = models.TextField(null=True, blank=True)
    # Optional
    inchi_code = models.TextField(default="")
    exact_mass = models.FloatField(default=0.0)
    solubility = models.TextField(null=True, blank=True)
    # External reference numbers
    hmdb_id = models.TextField(null=True, blank=True)
    chebi_id = models.TextField(null=True, blank=True)
    lipidmaps_id = models.TextField(null=True, blank=True)
    cas_id = models.TextField(null=True, blank=True)
    :param csv_file:
    :return:
    """
    csv_filepath = os.path.join(settings.MEDIA_ROOT, "tmp_csv.csv")
    pipe_file_to_disk(csv_filepath, file_)
    errors = add_batch_standard(csv_filepath)
    os.remove(csv_filepath)
    return errors


def add_batch_standard(csv_filename):
    import pandas as pd
    import sys
    error_list = []
    df = pd.read_csv(csv_filename, sep="\t", dtype=unicode)
    df.columns = [x.replace(" ", "_").lower() for x in df.columns]
    df = df.fillna("")
    # df = df.applymap(to_unicode)
    logging.debug("Shape: {}".format(df.shape))
    for row in df.iterrows():
        try:
            # clean up input
            entry = row[1]
            if entry['formula'] == '':
                raise ValueError('sum formula cannot be blank')
            # for tag in entry.keys():
            #    if entry[tag] != "":
            #        entry[tag] = entry[tag].encode("utf8") # make strings safe

            entry['id'] = ''.join([char for char in entry['id'] if char in ("0123456789")])

            if entry['pubchem_id'] != "":
                molecule = Molecule.objects.all().filter(pubchem_id=entry['pubchem_id'])
            else:
                molecule = Molecule.objects.all().filter(name__iexact=entry['name'])  # filter lowercase

            if molecule.exists():
                molecule = molecule[0]
            else:
                molecule = Molecule(
                    name=entry["name"],
                    sum_formula=entry["formula"],
                    inchi_code=entry["inchi"],
                    solubility=entry["solubility"],
                    hmdb_id=entry["hmdb_id"],
                    chebi_id=entry["chebi_id"],
                    lipidmaps_id=entry["lipidmaps_id"],
                    cas_id=entry["cas_id"],
                    pubchem_id=entry["pubchem_id"],
                )
                molecule.save()
                print("Successfully saved " + molecule.name)

            s = Standard.objects.all().filter(MCFID=entry['id'])
            if s.exists():  # standard already added, overwrite
                s = s[0]
            else:
                s = Standard(molecule=molecule)
                s.save()
            s.vendor = entry["vendor"]
            s.vendor_cat = entry["vendor_id"]
            s.lot_num = entry["lot_num"]
            if entry["purchase_date"] != '':
                s.purchase_date = dateutil.parser.parse(entry["purchase_date"], fuzzy=True)
            s.save()
            if entry["id"] == []:
                s.MCFID = s.pk
            else:
                s.MCFID = entry['id']
            s.save()
        except:
            error_list.append([entry['name'], sys.exc_info()[1]])
            # error_list.append([[''.join([i if ord(i) < 128 else ' ' for i in entry['name']])], slugify(sys.exc_info()[1]).encode('utf-8').strip()])
            logging.debug("Failed for: {} with {}".format(entry['name'], sys.exc_info()[1]))

    return error_list
