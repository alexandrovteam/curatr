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
    ppm=float(metadata['mass_accuracy'])
    scan_time = []
    standards = Standard.objects.all().filter(pk__in=metadata['standards'])
    adducts = Adduct.objects.all().filter(pk__in=metadata['adducts'])
    mz_upper={}
    mz_lower={}
    for standard in standards:
        mz_upper[standard]={}
        mz_lower[standard]={}
        for adduct in adducts:
            mz = standard.get_mz(adduct)
            logging.debug(standard)
            logging.debug(mz)
            delta_mz = mz*ppm*1e-6
            mz_upper[standard][adduct] = mz+delta_mz
            mz_lower[standard][adduct] = mz-delta_mz
    xics={}
    msms=[]
    for spectrum in msrun:
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
                    pre_mz = float(spectrum['precursors'][0]['mz'])
                    if all([pre_mz>=mz_lower[standard][adduct],pre_mz<=mz_upper[standard][adduct]]):
                        msms.append(copy.copy(spectrum))
    logging.debug(len(scan_time))
    logging.debug(np.shape(msms))
    logging.debug('adding dataset')
    d = Dataset(name=file, mass_accuracy_ppm = metadata['mass_accuracy'])
    d.save()
    for standard in standards:
        d.standards_present.add(standard)
    for adduct in adducts:
        d.adducts_present.add(adduct)
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
    for m in msms:
        f = FragmentationSpectrum(precursor_mz=m['precursors'][0]['mz'],
                              rt = m['scan start time'], dataset=d)
        f.set_centroid_mzs(m.mz)
        f.set_centroid_ints(m.i)
        f.save()
