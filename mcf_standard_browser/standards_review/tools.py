from tasks import add_batch_standard

import tasks

__author__ = 'palmer'
from .models import Dataset, Standard, Adduct, Xic, FragmentationSpectrum, Molecule
from django.conf import settings
import os
import pymzml
import numpy as np
import logging
from django.contrib.auth.models import User


def handle_uploaded_files(metadata,file):
    logging.debug(file.name)
    mzml_filename = os.path.join(settings.MEDIA_ROOT,file.name)
    with open(mzml_filename, 'w') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    msrun = pymzml.run.Reader(mzml_filename)
    ppm=float(metadata['mass_accuracy_ppm'])
    mz_tol_quad = float(metadata['quad_window_mz'])
    scan_time = []
    standards = Standard.objects.all().filter(pk__in=metadata['standards'])
    adducts = Adduct.objects.all().filter(pk__in=metadata['adducts'])
    mz_upper={}
    mz_lower={}
    mz={}
    logging.debug(standards.count())
    for standard in standards:
        mz_upper[standard]={}
        mz_lower[standard]={}
        mz[standard]={}
        for adduct in adducts:
            mz[standard][adduct] = standard.molecule.get_mz(adduct)

            logging.debug(standard)
            logging.debug(mz[standard][adduct])
            delta_mz = mz[standard][adduct]*ppm*1e-6
            mz_upper[standard][adduct] = mz[standard][adduct]+delta_mz
            mz_lower[standard][adduct] = mz[standard][adduct]-delta_mz
    logging.debug('adding dataset')
    instrument = ''

    d = Dataset(name=file, mass_accuracy_ppm = ppm)
    d.instrument = instrument
    d.save()
    for standard in standards:
        d.standards_present.add(standard)
    for adduct in adducts:
        d.adducts_present.add(adduct)
    d.save()
    logging.debug('adding msms')
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
                    if add_msms:
                        ms1_intensity = xics[standard][adduct][-1]
                        mzs = spectrum.mz
                        ints = spectrum.i
                        quad_ints = [ii for m,ii in zip(mzs,ints) if all((m>=pre_mz-mz_tol_quad       , m<=pre_mz+mz_tol_quad))]
                        ppm_ints  = [ii for m,ii in zip(mzs,ints) if all((m>=pre_mz-mz_tol_this_adduct, m<=pre_mz+mz_tol_this_adduct))]
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
                            pre_fraction=0
                        else:
                            pre_fraction = sum(ppm_ints)/sum(quad_ints)
                        f = FragmentationSpectrum(precursor_mz=pre_mz,
                              rt = spectrum['scan start time'], dataset=d, spec_num=spec_n, precursor_quad_fraction=pre_fraction, ms1_intensity=ms1_intensity, collision_energy=ce_str)
                        f.set_centroid_mzs(spectrum.mz)
                        f.set_centroid_ints(spectrum.i)
                        f.collision = ce_str
                        f.save()
    logging.debug("adding xics")
    for standard in standards:
        for adduct in adducts:
            #if np.sum(xics[standard][adduct]) > 0:
                x = Xic(mz= standard.molecule.get_mz(adduct), dataset=d)
                x.set_xic(xics[standard][adduct])
                x.set_rt(scan_time)
                x.standard = standard
                x.adduct = adduct
                x.save()
    logging.debug('done')
    return True


class ChartData(object):
    @classmethod
    def get_avg_by_day(cls,):
        data = {'dates': range(20), 'values': np.random.rand(20)}
        return data

def update_fragSpec(fragSpecId,response, standard, adduct, username):
    fs = FragmentationSpectrum.objects.get(pk=fragSpecId)
    logging.debug(fs.dataset)
    if response == '0':
        fs.standard = None
        fs.adduct = None
        fs.reviewed = True
    elif response == '1':
        fs.standard=standard
        fs.adduct=adduct
        fs.reviewed = True
    else:
        fs.standard = None
        fs.adduct = None
        fs.reviewed = False
    fs.last_editor = User.objects.get(username=username)
    fs.save()


def pipe_file_to_disk(filename, file):
    with open(filename, 'w') as destination:
        for chunk in file.chunks():
            destination.write(chunk)


def process_batch_standard(metadata, file):
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
    csv_filename = os.path.join(settings.MEDIA_ROOT,"tmp_csv.csv")
    pipe_file_to_disk(csv_filename, file)
    error_list = add_batch_standard(csv_filename)
    return error_list


def process_batch_standard_async(metadata, file):
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
    csv_filename = os.path.join(settings.MEDIA_ROOT,"tmp_csv.csv")
    pipe_file_to_disk(csv_filename, file)
    async = tasks.add_batch_standard_async.delay(csv_filename)
    async.get()


def to_unicode(s):
    return s.encode("utf-8", errors="ignore")


def update_mzs():
    molecules = Molecule.objects.all()
    for molecule in molecules:
        molecule.set_adduct_mzs()
        molecule.save()


