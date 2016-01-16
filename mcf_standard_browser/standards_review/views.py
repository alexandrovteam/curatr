from django.shortcuts import render, redirect, get_object_or_404, render_to_response

from models import Standard, FragmentationSpectrum, Dataset, Adduct, Xic
from .forms import MCFStandardForm
import numpy as np
import datetime
# Create your views here.

def home_page(request):
    return render(request,'mcf_standards_browse/home_page.html',)

def StandardAdduct_detail(request,dataset_pk, standard_pk, adduct_pk):
    print 'standard - yo'
    print dataset_pk, standard_pk, adduct_pk
    return True


def MCFStandard_list(request):
    standards = Standard.objects.all()
    print len(standards)
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

    #return render_to_response('discretebarchart.html', data)
    #return render('spec_browse/lineplusbarchart.html', data)
    return render_to_response('mcf_standards_browse/mcf_fragmentSpectrum_detail.html', context=data)
    #return render(request, 'mcf_standards_browse/mcf_fragmentSpectrum_detail.html', data)


def MCFdataset_list(request):
    datasets = Dataset.objects.all()
    return  render(request,'mcf_standards_browse/mcf_dataset_list.html',{'datasets':datasets})

def MCFdataset_detail(request, pk):
    dataset=get_object_or_404(Dataset, pk=pk)
    adducts = dataset.adducts_present.all()
    standards = dataset.standards_present.all()
    data = {'dataset':dataset,
            'adducts':adducts,
            'standards':standards,}
    return render_to_response('mcf_standards_browse/mcf_dataset_detail.html', context=data)

def MCFxic_detail(request,dataset_pk, standard_pk, adduct_pk):
    dataset=get_object_or_404(Dataset, pk=dataset_pk)
    standard=get_object_or_404(Standard, pk=standard_pk)
    adduct=get_object_or_404(Adduct, pk=adduct_pk)
    #todo - add mass accuracy to dataset
    mz=standard.get_mz(adduct)
    xics=Xic.objects.all().filter(dataset=dataset).filter(mz__gte=mz+0.01).filter(mz__lte=mz-0.01)
    data = {"dataset":dataset,
            "standard":standard,
            "adduct":adduct,
            "xics":xics,}
    return render_to_response('mcf_standards_browse/mcf_xic_detail.html', context=data)


