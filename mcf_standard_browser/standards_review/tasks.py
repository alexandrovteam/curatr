import logging
import sys

import dateutil
import pandas as pd
import pymzml
from celery import shared_task
from celery.schedules import crontab
from celery.task import periodic_task

from models import Adduct, FragmentationSpectrum, Xic, LcInfo, MsInfo, InstrumentInfo
from models import Molecule, Standard
from django.conf import settings
from tools import DatabaseLogHandler
import os
import datetime
import numpy as np

@shared_task
def add_batch_standard(metadata, csv_file):
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
    error_list = []
    df = pd.read_csv(csv_file, sep="\t", dtype=unicode)
    logging.info('I read the file')
    df.columns = [x.replace(" ", "_").lower() for x in df.columns]
    logging.info("I replaced columns")
    df = df.fillna("")
    # df = df.applymap(to_unicode)
    logging.info("Shape: {}".format(df.shape))
    for row in df.iterrows():
        logging.info("row: {}".format(row))
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
                logging.info("about to save " + molecule.name)
                logging.info(molecule)
                molecule.save()
                logging.info("Successfully saved " + molecule.name)

            s = Standard.objects.all().filter(inventory_id=entry['id'])
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
                s.inventory_id = s.pk
            else:
                s.inventory_id = entry['id']
            s.save()
        except:
            error_list.append([entry['name'], sys.exc_info()[1]])
            logging.warning("Failed for: {} with {}".format(entry['name'], sys.exc_info()[1]))

    return error_list


@shared_task
def handle_uploaded_files(metadata, mzml_filepath, d):
    logger = logging.getLogger(__file__ + str(d.id))
    logger.addHandler(DatabaseLogHandler(d, level=logging.ERROR))

    msrun = pymzml.run.Reader(mzml_filepath)
    ppm = float(metadata['mass_accuracy_ppm'])
    mz_tol_quad = float(metadata['quad_window_mz'])
    ionization_method = metadata['ionization_method']
    ion_analyzer = metadata['ion_analyzer']
    scan_time = []
    standards = Standard.objects.all().filter(pk__in=metadata['standards'])
    adducts = Adduct.objects.all().filter(pk__in=metadata['adducts'])
    mz_upper = {}
    mz_lower = {}
    mz = {}
    logger.debug(standards.count())
    for standard in standards:
        mz_upper[standard] = {}
        mz_lower[standard] = {}
        mz[standard] = {}
        for adduct in adducts:
            mz[standard][adduct] = standard.molecule.get_mz(adduct)
            logger.debug({'standard': standard})
            logger.debug({'mz': mz[standard][adduct]})
            delta_mz = mz[standard][adduct] * ppm * 1e-6
            mz_upper[standard][adduct] = mz[standard][adduct] + delta_mz
            mz_lower[standard][adduct] = mz[standard][adduct] - delta_mz
    logger.debug('adding dataset')
    try:
        lc_info = metadata['lc_info']
        ms_info = metadata['ms_info']
        instrument_info = metadata['instrument_info']
    except LookupError:
        logger.debug('no instrument information supplied; using empty string instead')
        lc_info = ms_info = instrument_info = ''

    lc_info_stripped = set()
    ms_info_stripped = set()
    instr_info_stripped = set()
    tag_sets = (lc_info_stripped, ms_info_stripped, instr_info_stripped)
    for tag_str, tag_set in zip([lc_info, ms_info, instrument_info], tag_sets):
        for tag in tag_str.split(', '):
            if tag:
                tag_stripped = tag.replace(',', '').strip()
                tag_set.add(tag_stripped)
    for tag_set, TagClass, attrname in zip(tag_sets, [LcInfo, MsInfo, InstrumentInfo],
                                           ['lc_info', 'ms_info', 'instrument_info']):
        for tag in tag_set:
            tag_obj = TagClass.objects.get_or_create(content=tag)[0]
            if tag_obj not in getattr(d, attrname).all():
                getattr(d, attrname).add(tag_obj)

    d.ionization_method = ionization_method
    d.ion_analyzer = ion_analyzer
    d.mass_accuracy_ppm = ppm
    d.save()
    for standard in standards:
        d.standards_present.add(standard)
    for adduct in adducts:
        d.adducts_present.add(adduct)
    d.save()
    logger.debug('adding msms')
    xics = {}
    spec_n = 0
    for spectrum in msrun:
        spec_n += 1
        if spectrum['ms level'] == 1:
            scan_time.append(spectrum['scan start time'])
        # Iterate adducts/standards and get values as required
        for standard in standards:
            if standard not in xics:
                xics[standard] = {}
            for adduct in adducts:
                if adduct not in xics[standard]:
                    xics[standard][adduct] = []
                if spectrum['ms level'] == 1:
                    x = 0
                    for m, i in spectrum.centroidedPeaks:
                        if all([m >= mz_lower[standard][adduct], m <= mz_upper[standard][adduct]]):
                            x += i
                    xics[standard][adduct].append(x)
                if spectrum['ms level'] == 2:
                    add_msms = False
                    pre_mz = float(spectrum['precursors'][0]['mz'])
                    mz_tol_this_adduct = mz[standard][adduct] * ppm * 1e-6
                    if any((abs(pre_mz - mz[standard][adduct]) <= mz_tol_this_adduct,
                            abs(pre_mz - mz[standard][adduct]) <= mz_tol_quad)):  # frag spectrum probably the target
                        add_msms = True
                    if add_msms:
                        ms1_intensity = xics[standard][adduct][-1]
                        mzs = spectrum.mz
                        ints = spectrum.i
                        quad_ints = [ii for m, ii in zip(mzs, ints) if
                                     all((m >= pre_mz - mz_tol_quad, m <= pre_mz + mz_tol_quad))]
                        ppm_ints = [ii for m, ii in zip(mzs, ints) if
                                    all((m >= pre_mz - mz_tol_this_adduct, m <= pre_mz + mz_tol_this_adduct))]
                        quad_ints_sum = sum(quad_ints)
                        ppm_ints_sum = sum(ppm_ints)
                        ce_type = ''
                        ce_energy = ''
                        ce_gas = ''
                        logging.warning(spectrum.keys())
                        if "MS:1000512" in spectrum: # Thermo filter string
                            ce_str = spectrum["MS:1000512"].split('@')[1].split('[')[0]
                        else:
                            for element in spectrum.xmlTree:
                                if element.get('accession') == "MS:1000133":
                                    ce_type = element.items()
                                elif element.get('accession') == "MS:1000045":
                                    ce_energy = dict(element.items())
                            ce_str = "{} {} {}".format(ce_energy['name'], ce_energy['value'], ce_energy['unitName'])
                        if ppm_ints_sum == 0:
                            pre_fraction = 0
                        else:
                            pre_fraction = sum(ppm_ints) / sum(quad_ints)
                        f = FragmentationSpectrum(precursor_mz=pre_mz,
                                                  rt=spectrum['scan start time'], dataset=d, spec_num=spec_n,
                                                  precursor_quad_fraction=pre_fraction, ms1_intensity=ms1_intensity,
                                                  collision_energy=ce_str)
                        f.set_centroid_mzs(spectrum.mz)
                        f.set_centroid_ints(spectrum.i)
                        f.collision = ce_str
                        f.save()
    logger.debug("adding xics")
    for standard in standards:
        for adduct in adducts:
            # if np.sum(xics[standard][adduct]) > 0:
            x = Xic(mz=standard.molecule.get_mz(adduct), dataset=d)
            x.set_xic(xics[standard][adduct])
            x.set_rt(scan_time)
            x.standard = standard
            x.adduct = adduct
            x.save()
    d.processing_finished = True
    d.save()
    logger.debug('done')
    logger.debug("added = True")
    return True


@periodic_task(run_every=crontab(minute=0, hour=4))  # every day at 4am
def scrape_pubchem_for_inchi():
    from pubchempy import BadRequestError, Compound, NotFoundError
    for m in Molecule.objects.filter(pubchem_id__isnull=False).order_by('pubchem_id'):
        if m.inchi_code == "":
            try:
                c = Compound.from_cid(m.pubchem_id)
                m.inchi_code = c.inchi
                m.save()
            except (BadRequestError, NotFoundError):
                logging.error('Invalid PubChem CID: {}'.format(m.pubchem_id))


@periodic_task(run_every=crontab(minute=0, hour=1, day_of_week=1))  # every week at 1am
def remove_old_spectra():
    """
    Deletes unreviewed spectra from the database if they have been there for longer than settings.SPECTRA_LIFETIME (weeks)

    """
    logging.debug('running tidy old')
    if settings.SPECTRA_LIFETIME:
        time_threshold = (datetime.datetime.now() - datetime.timedelta(weeks=settings.SPECTRA_LIFETIME)).date()
        logging.debug(('deleting spectra before', time_threshold))
        spectra = FragmentationSpectrum.objects.filter(reviewed=False).filter(date_added__lt=time_threshold)
        logging.debug(('number spectra to delete:', spectra.count()))
        spectra.delete()


@periodic_task(run_every=crontab(minute=0, hour=0))  # every day at midnight
def periodic_export():
    from . import export
    for polarity in [None, 'positive', 'negative']:
        spectra = FragmentationSpectrum.objects.all().filter(reviewed=True).exclude(standard=None)
        if polarity:
            if polarity == 'positive':
                spectra = spectra.exclude(adduct__charge__lte=0)
            elif polarity == 'negative':
                spectra = spectra.exclude(adduct__charge__gte=0)
            else:
                raise ValueError("value of polarity not valid {}".format(polarity))

        spec_pairs = [[spectrum, zip(spectrum.centroid_mzs, spectrum.centroid_ints,
                                 (999 / (np.max(spectrum.centroid_ints)) * spectrum.centroid_ints).astype(int))] for
                  spectrum in spectra]
        for fmt in [at for at in dir(export) if at.startswith('write')]:
            fmt_name = fmt.replace("write_", "")
            d = datetime.datetime.now()
            fn = os.path.join(settings.MEDIA_ROOT, d.strftime("%y%d%m_{}.zip".format(fmt_name)))
            if polarity:
                fn = fn.replace(fmt_name, fmt_name + polarity)
            getattr(export, fmt)(fn, spec_pairs)

