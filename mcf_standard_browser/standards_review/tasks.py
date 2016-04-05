import logging
import sys

import dateutil
import pandas as pd
import pymzml
from celery import shared_task

from models import Adduct, Dataset, FragmentationSpectrum, Xic
from models import Molecule, Standard


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
                logging.debug("Successfully saved " + molecule.name)

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
        except Exception as e:
            error_list.append([entry['name'], str(e)])
            logging.warning("Failed for: {} with '{}'".format(entry['name'], e))

    return error_list


@shared_task
def handle_uploaded_files(metadata, mzml_filename):
    logging.debug("mzML filename: " + mzml_filename)
    msrun = pymzml.run.Reader(mzml_filename)
    ppm = float(metadata['mass_accuracy_ppm'])
    mz_tol_quad = float(metadata['quad_window_mz'])
    scan_time = []
    standards = Standard.objects.all().filter(pk__in=metadata['standards'])
    adducts = Adduct.objects.all().filter(pk__in=metadata['adducts'])
    mz_upper = {}
    mz_lower = {}
    mz = {}
    logging.debug(standards.count())
    for standard in standards:
        mz_upper[standard] = {}
        mz_lower[standard] = {}
        mz[standard] = {}
        for adduct in adducts:
            mz[standard][adduct] = standard.molecule.get_mz(adduct)

            logging.debug(standard)
            logging.debug(mz[standard][adduct])
            delta_mz = mz[standard][adduct] * ppm * 1e-6
            mz_upper[standard][adduct] = mz[standard][adduct] + delta_mz
            mz_lower[standard][adduct] = mz[standard][adduct] - delta_mz
    logging.debug('adding dataset')
    instrument = ''

    d = Dataset(name=mzml_filename, mass_accuracy_ppm=ppm, processing_finished=False)
    d.instrument = instrument
    d.save()
    for standard in standards:
        d.standards_present.add(standard)
    for adduct in adducts:
        d.adducts_present.add(adduct)
    d.save()
    logging.debug('adding msms')
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
    logging.debug("adding xics")
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
    logging.debug('done')
    logging.debug("added = True")
    return True
