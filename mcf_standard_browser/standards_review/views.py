from django.shortcuts import render, redirect, get_object_or_404, render_to_response
from django.http import HttpResponseRedirect
from models import Standard, FragmentationSpectrum, Dataset, Adduct, Xic
from .forms import MCFStandardForm, UploadFileForm
import numpy as np
from .tools import handle_uploaded_files
import logging

# Create your views here.

def home_page(request):
    return render(request,'mcf_standards_browse/home_page.html',)

def StandardAdduct_detail(request,dataset_pk, standard_pk, adduct_pk):
    print 'standard - yo'
    print dataset_pk, standard_pk, adduct_pk
    return True


def MCFStandard_list(request):
    standards = Standard.objects.all().order_by('MCFID')
    return  render(request,'mcf_standards_browse/mcf_standard_list.html',{'standards':standards})

def MCFStandard_detail(request, pk):
    standard=get_object_or_404(Standard, MCFID=pk)
    #adducts = Adduct.objects.all()
    return render(request, 'mcf_standards_browse/mcf_standard_detail.html', {'standard': standard})

def MCFStandard_add(request):
    if request.method == "POST":
        form = MCFStandardForm(request.POST)
        if form.is_valid():
            standard = form.save()
            standard.save()
            return redirect('MCFStandard-list')
    else:
        form = MCFStandardForm()
    return render(request,'mcf_standards_browse/mcf_standard_add.html', {'form':form})


def fragmentSpectrum_list(request):
    fragmentSpectra = FragmentationSpectrum.objects.all()
    return  render(request,'mcf_standards_browse/mcf_fragmentSpectrum_list.html',{'fragmentSpectra':fragmentSpectra})


def fragmentSpectrum_detail(request,pk):
    spectrum = get_object_or_404(FragmentationSpectrum, pk=pk)
    xdata = np.concatenate((spectrum.centroid_mzs,
                            spectrum.centroid_mzs[0:-1]/2.+spectrum.centroid_mzs[1:]/2.,
                            spectrum.centroid_mzs+0.0000001,
                            spectrum.centroid_mzs-0.0000001,))
    n_mzs = len(xdata)
    ydata = np.concatenate((spectrum.centroid_ints,
                            np.zeros((n_mzs-1,)),
                            np.zeros((n_mzs,)),
                            np.zeros((n_mzs,)),))
    idx = np.argsort(xdata)
    xdata=xdata[idx][1:-1]
    ydata=ydata[idx][1:-1]

    extra_serie1 = {"tooltip": {"y_start": "", "y_end": " "}}
    chartdata = [{
        'x': xdata, 'name': 'intensity', 'y': ydata, 'extra': extra_serie1,'kwargs':{}
    },]
    #charttype = "discreteBarChart"
    charttype = "lineWithFocusChart"
    chartcontainer = 'discretebarchart_container'  # container name
    data = {
        'charttype': charttype,
        'chartdata': chartdata,
        'chartcontainer': chartcontainer,
        'extra': {
            'x_is_date': False,
            'x_axis_format': '',
            'tag_script_js': True,
            'jquery_on_ready': True,
        },
    }

    data['specdata']={}
    data['specdata']['spectrum'] = spectrum
    data['specdata']['centroids'] = [spectrum.centroid_mzs,spectrum.centroid_ints]
    return render_to_response('mcf_standards_browse/mcf_fragmentSpectrum_detail.html', context=data)

def MCFdataset_list(request):
    datasets = Dataset.objects.all()
    return render(request,'mcf_standards_browse/mcf_dataset_list.html',{'datasets':datasets})

def MCFdataset_detail(request, pk):
    dataset=get_object_or_404(Dataset, pk=pk)
    adducts = dataset.adducts_present.all()
    standards = dataset.standards_present.all().order_by('MCFID')
    data = {'dataset':dataset,
            'adducts':adducts,
            'standards':standards,}
    return render_to_response('mcf_standards_browse/mcf_dataset_detail.html', context=data)


def MCFxic_detail(request,dataset_pk, standard_pk, adduct_pk):
    dataset=get_object_or_404(Dataset, pk=dataset_pk)
    standard=get_object_or_404(Standard, pk=standard_pk)
    adduct=get_object_or_404(Adduct, pk=adduct_pk)
    mz=standard.get_mz(adduct)
    delta_mz = mz*dataset.mass_accuracy_ppm*1e-6
    xics=Xic.objects.all().filter(dataset=dataset).filter(mz__gte=mz-delta_mz).filter(mz__lte=mz+delta_mz)
    frag_specs = FragmentationSpectrum.objects.all().filter(dataset=dataset).filter(precursor_mz__gte=mz-delta_mz).filter(precursor_mz__lte=mz+delta_mz)
    chartdata = []
    for xic in xics:
        chartdata.append(
             {'name': xic.mz, 'x': xic.rt, 'y': xic.xic, 'extra': {}, 'kwargs': {}},
         )
    charttype = "lineWithFocusChart"
    chartcontainer = 'linewithfocuschart_container'  # container name
    data = {
        'charttype': charttype,
        'chartdata': chartdata,
        'chartcontainer': chartcontainer,
        'extra': {
            'x_is_date': False,
            'x_axis_format': '',
            'tag_script_js': True,
            'jquery_on_ready': True,},
        "dataset":dataset,
        "standard":standard,
        "adduct":adduct,
        "xics":xics,
        "frag_specs":frag_specs,}
    return render_to_response('mcf_standards_browse/mcf_xic_detail.html', context=data)


def dataset_upload(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            post_dict = dict(request.POST)
            data = {"adducts": post_dict['adducts'],
                    "standards": post_dict['standards'],
                    "mass_accuracy": post_dict['mass_accuracy'][0],}
            handle_uploaded_files(data, request.FILES['mzml_file'])
            return redirect('MCFdataset-list')
    else:
        form = UploadFileForm(initial={"mass_accuracy":10.0})
    return render(request, 'mcf_standards_browse/dataset_upload.html', {'form': form})