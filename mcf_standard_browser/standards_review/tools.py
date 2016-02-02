__author__ = 'palmer'
from .models import Dataset, Standard, Adduct, Xic, FragmentationSpectrum
from django.conf import settings
import os
import pymzml
import numpy as np
import logging


def handle_uploaded_files(metadata,file):
    mzml_filename = os.path.join(settings.MEDIA_ROOT,"tmp_mzml.mzml")
    with open(mzml_filename, 'w') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    msrun = pymzml.run.Reader(mzml_filename)
    import copy
    ppm=float(metadata['mass_accuracy_ppm'])
    mz_tol_quad = float(metadata['quad_window_mz'])
    scan_time = []
    standards = Standard.objects.all().filter(pk__in=metadata['standards'])
    adducts = Adduct.objects.all().filter(pk__in=metadata['adducts'])
    mz_upper={}
    mz_lower={}
    mz={}
    for standard in standards:
        mz_upper[standard]={}
        mz_lower[standard]={}
        mz[standard]={}
        for adduct in adducts:
            mz[standard][adduct] = standard.get_mz(adduct)

            logging.debug(standard)
            logging.debug(mz[standard][adduct])
            delta_mz = mz[standard][adduct]*ppm*1e-6
            mz_upper[standard][adduct] = mz[standard][adduct]+delta_mz
            mz_lower[standard][adduct] = mz[standard][adduct]-delta_mz
    logging.debug('adding dataset')
    d = Dataset(name=file, mass_accuracy_ppm = ppm)
    d.save()
    for standard in standards:
        d.standards_present.add(standard)
    for adduct in adducts:
        d.adducts_present.add(adduct)
    logging.debug('adding msms - grabbing xics')
    xics={}
    spec_n=0
    for spectrum in msrun:
        spec_n+=1
        if spectrum['ms level'] == 1:
            scan_time.append(spectrum['scan start time'])
        # Iterate adducts/standards and get values as required
        for standard in standards:
            if standard not in xics:
                xics[standard]={}
            for adduct in adducts:
                if adduct not in xics[standard]:
                    xics[standard][adduct]=[]
                if spectrum['ms level']==1:
                    x = 0
                    for m,i in spectrum.centroidedPeaks:
                        if all([m>=mz_lower[standard][adduct],m<=mz_upper[standard][adduct]]):
                            x+=i
                    xics[standard][adduct].append(x)
                if spectrum['ms level'] == 2:
                    add_msms = False
                    pre_mz = float(spectrum['precursors'][0]['mz'])
                    mz_tol_this_adduct =  mz[standard][adduct]*ppm*1e-6
                    if any((abs(pre_mz - mz[standard][adduct]) <= mz_tol_this_adduct, abs(pre_mz - mz[standard][adduct]) <= mz_tol_quad)): # frag spectrum probably the target
                        add_msms=True
                    #elif abs(pre_mz - mz[standard][adduct]) <= mz_tol_quad: # double check that the pre-cursor isn't hiding within quad window
                    #    pre_mz = np.asarray(spectrum.mz)[np.abs(np.argmin(np.asarray(spectrum.mz) - mz[standard][adduct]))]
                    #    if abs(pre_mz - mz[standard][adduct]) <= mz_tol_this_adduct:
                    #        add_msms=True

                    if add_msms:
                        mzs = spectrum.mz
                        ints = spectrum.i
                        quad_ints = [ii for m,ii in zip(mzs,ints) if all((m>=pre_mz-mz_tol_quad       , m<=pre_mz+mz_tol_quad))]
                        ppm_ints  = [ii for m,ii in zip(mzs,ints) if all((m>=pre_mz-mz_tol_this_adduct, m<=pre_mz+mz_tol_this_adduct))]
                        quad_ints_sum = sum(quad_ints)
                        ppm_ints_sum = sum(ppm_ints)
                        logging.debug(quad_ints)
                        logging.debug(ppm_ints)
                        logging.debug(quad_ints_sum)
                        logging.debug(ppm_ints_sum)
                        if ppm_ints_sum == 0:
                            pre_fraction=0
                        else:
                            pre_fraction = sum(ppm_ints)/sum(quad_ints)
                        f = FragmentationSpectrum(precursor_mz=pre_mz,
                              rt = spectrum['scan start time'], dataset=d, spec_num=spec_n, precursor_quad_fraction=pre_fraction)
                        f.set_centroid_mzs(spectrum.mz)
                        f.set_centroid_ints(spectrum.i)
                        f.save()
                    #if all([pre_mz>=mz_lower[standard][adduct],pre_mz<=mz_upper[standard][adduct]]):
                    #    msms.append(copy.copy(spectrum))


    logging.debug("adding xics")
    for standard in standards:
        for adduct in adducts:
            if np.sum(xics[standard][adduct]) > 0:
                x = Xic(mz= standard.get_mz(adduct), dataset=d)
                x.set_xic(xics[standard][adduct])
                x.set_rt(scan_time)
                x.standard = standard
                x.adduct = adduct
                x.save()
    logging.debug('adding msms')


from datetime import datetime, timedelta
from .models import Xic

class ChartData(object):
    @classmethod
    def get_avg_by_day(cls,):
        data = {'dates': range(20), 'values': np.random.rand(20)}
        return data

def update_fragSpec(fragSpecId,response, standard, adduct):
    fs = FragmentationSpectrum.objects.get(pk=fragSpecId)
    logging.debug(fs.dataset)
    if response == '1':
        logging.debug(standard)
        logging.debug(adduct)
        fs.standard=standard
        fs.adduct=adduct
    else:
        fs.standard = None
        fs.adduct = None
    fs.reviewed = True
    fs.save()


def pipe_file_to_disk(filename, file):
    with open(filename, 'w') as destination:
        for chunk in file.chunks():
            destination.write(chunk)


def process_batch_standard(metadata, file):
    """
    handle a csv fil of standards
    header line should be "ID","Name","Formula", "InChi", "solubility", "vendor","vendor_id", "hmdb_id" , "chebi_id", "lipidmaps_id", "cas_id", "pubchem_id"
    name = models.TextField(default = "")
    sum_formula = models.TextField(null=True)
    MCFID = models.TextField(default="")
    inchi_code = models.TextField(default="")
    exact_mass = models.FloatField(default=0.0)
    solubility = models.TextField(null=True, blank=True)
    # External reference numbers
    hmdb_id = models.TextField(null=True, blank=True)
    chebi_id = models.TextField(null=True, blank=True)
    lipidmaps_id = models.TextField(null=True, blank=True)
    cas_id = models.TextField(null=True, blank=True)
    pubchem_id = models.TextField(null=True, blank=True)
    vendor = models.TextField(null=True, blank=True)
    vendor_cat = models.TextField(null=True, blank=True)
    :param csv_file:
    :return:
    """
    csv_filename = os.path.join(settings.MEDIA_ROOT,"tmp_csv.csv")
    logging.debug(">>>>>>>")
    logging.debug(csv_filename)
    pipe_file_to_disk(csv_filename, file)
    add_batch_standard(csv_filename)


def add_batch_standard(csv_filename):
    import pandas as pd
    import sys
    df = pd.read_csv(csv_filename, sep="\t")
    df = df.fillna("")
    for row in df.iterrows():
        try:
            entry = row[1]
            s = Standard(MCFID = entry["id"],
                         name=entry["name"],
                         sum_formula = entry["formula"],
                         inchi_code = entry["inchi"],
                         solubility = entry["solubility"],
                         vendor = entry["vendor"],
                         vendor_cat = entry["vendor_id"],
                         hmdb_id = entry["hmdb_id"],
                         chebi_id = entry["chebi_id"],
                         lipidmaps_id = entry["lipidmaps_id"],
                         cas_id = entry["cas_id"],
                         pubchem_id = entry["pubchem_id"])
            s.save()
        except:
            logging.debug("Failed for: {} with {}".format(entry, sys.exc_info()[0]))


