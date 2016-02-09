from django.shortcuts import render, redirect, get_object_or_404, render_to_response, HttpResponse
from django.views.generic import TemplateView, ListView
from django.views.decorators.csrf import ensure_csrf_cookie
from models import Standard, FragmentationSpectrum, Dataset, Adduct, Xic, Molecule
from .forms import MCFMoleculeForm, MCFStandardForm, UploadFileForm, FragSpecReview, MCFStandardBatchForm
import numpy as np
import tools
import sys
sys.path.append('/Users/palmer/Documents/python_codebase/django-highcharts/django-highcharts/highcharts/')
import json
import logging
from django.views.generic import TemplateView, ListView
from django.contrib.auth.decorators import login_required


# Create your views here.

def home_page(request):
    return render(request,'mcf_standards_browse/home_page.html',)


def MCFStandard_list(request):
    standards = Standard.objects.all()#.order_by('MCFID')
    adducts = Adduct.objects.all()
    adduct_names = [adduct for adduct in adducts]
    standard_data = []
    for standard in standards:
        precalc_adduct_mzs = standard.molecule.adduct_mzs
        adduct_mzs=[]
        for adduct in adducts:
            adduct_mzs.append({"val": np.round(precalc_adduct_mzs[str(adduct)], decimals=5)})
        standard_data.append([standard,adduct_mzs])

    return  render(request,'mcf_standards_browse/mcf_standard_list.html',{'standards':standard_data, 'adduct_names':adduct_names,})

def MCFMolecule_list(request):
    molecules = Molecule.objects.all()
    adducts = Adduct.objects.all()
    adduct_names = [adduct for adduct in adducts]
    logging.debug(adduct_names)
    standard_data = []
    for molecule in molecules:
        precalc_adduct_mzs = molecule.adduct_mzs
        adduct_mzs=[]
        for adduct in adducts:
            adduct_mzs.append({"val": np.round(precalc_adduct_mzs[str(adduct)], decimals=5)})
        standard_data.append([molecule,adduct_mzs])

    return  render(request,'mcf_standards_browse/mcf_molecule_list.html',{'standards':standard_data, 'adduct_names':adduct_names,})



class IndexView(TemplateView):
    template_name = 'mcf_standards_browse/home_page.html'

class ServerSideView(TemplateView):
    template_name = 'mcf_standards_browse/server-side-base.html'
    model = Standard
    context_object_name = 'browsers'

class MCFStandard_list_ez(ListView):
    template_name ='eztables/client_side.html'
    model = Standard
    #fields = ('name',
    #        'sum_formula',
    #         'MCFID',)
    context_object_name = 'standards'

def MCFStandard_detail(request, pk):
    standard=get_object_or_404(Standard, MCFID=pk)
    return render(request, 'mcf_standards_browse/mcf_standard_detail.html', {'standard': standard})

def MCFMolecule_detail(request, pk):
    molecule=get_object_or_404(Molecule, pk=pk)
    return render(request, 'mcf_standards_browse/mcf_molecule_detail.html', {'molecule': molecule})

@login_required()
def MCFStandard_add(request):
    if request.method == "POST":
        form = MCFStandardForm(request.POST)
        if form.is_valid():
            standard = form.save()
            standard.save()
            return redirect('MCFStandard-list')
    else:
        form = MCFStandardForm()
    return render(request,'mcf_standards_browse/mcf_standard_add.html', {'form':form, 'form_type':'single'})

@login_required()
def MCFStandard_edit(request, pk):
    standard = get_object_or_404(Standard, MCFID=pk)
    if request.method == "POST":
        form = MCFStandardForm(request.POST)
        if form.is_valid():
            standard = form.save()
            standard.save()
            return redirect('MCFStandard-list')
    else:
        form = MCFStandardForm(instance=standard)
    logging.debug(form)
    return render(request,'mcf_standards_browse/mcf_standard_edit.html', {'form':form,})

@login_required()
def MCFMolecule_edit(request, pk):
    molecule = get_object_or_404(Molecule, pk=pk)
    standards = Standard.objects.all().filter(molecule=molecule)
    if request.method == "POST":
        form = MCFMoleculeForm(request.POST)
        if form.is_valid():
            standard = form.save()
            standard.save()
            return redirect('MCFStandard-list')
    else:
        form = MCFMoleculeForm(instance=molecule)
    return render(request,'mcf_standards_browse/mcf_molecule_edit.html', {'form':form, 'standards': standards, 'molecule':molecule})



@login_required()
def MCFStandard_add_batch(request):
    logging.debug(request.FILES)
    if request.method == "POST":
        form = MCFStandardBatchForm(request.POST, request.FILES)
        if form.is_valid():
            error_list = tools.process_batch_standard({'username': request.user.username}, request.FILES['semicolon_delimited_file'])
            logging.debug(error_list)
            if error_list =={}:
                return redirect('MCFStandard-list')
            else:
                return redirect('upload-error', error_list= error_list)
    else:
        form = MCFStandardBatchForm()
    return render(request,'mcf_standards_browse/mcf_standard_add.html', {'form':form, 'form_type':'batch'})


def upload_error(request, error_list):
    render_to_response(request,'mcf_standards_browse/upload_error.html', context=error_list)


def fragmentSpectrum_list(request):
    fragmentSpectra = FragmentationSpectrum.objects.all()
    return  render(request,'mcf_standards_browse/mcf_fragmentSpectrum_list.html',{'fragmentSpectra':fragmentSpectra})


def fragmentSpectrum_detail(request,pk):
    spectrum = get_object_or_404(FragmentationSpectrum, pk=pk)
    xdata = np.concatenate((spectrum.centroid_mzs,
                            spectrum.centroid_mzs[0:-1]/2.+spectrum.centroid_mzs[1:]/2.,
                            spectrum.centroid_mzs+0.00001,
                            spectrum.centroid_mzs-0.00001,
                            np.arange(int(spectrum.centroid_mzs[0]-1),int(spectrum.centroid_mzs[-1]+1),1),))
    n_mzs = len(xdata)
    ydata = np.concatenate((spectrum.centroid_ints,
                            np.zeros((n_mzs-1,)),
                            np.zeros((n_mzs,)),
                            np.zeros((n_mzs,)),
                            np.zeros(spectrum.centroid_mzs[1],spectrum.centroid_mzs[0]+2,),))
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
    chartID = 'chart_ID'
    chart_type = 'line'
    chart_height = 500
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
        'specdata':{
            'spectrum': spectrum,
            'centroids':  [spectrum.centroid_mzs,spectrum.centroid_ints],
        },
        "highchart":{
            "chart_id": 'chart_id',
            "chart": {"renderTo": 'chart_id', "type": chart_type, "height": chart_height, "zoomType": "x"},
            "title": {"text": 'Fragment Spectrum'},
            "xAxis":  {"title": {"text": 'm/z'},},
            "yAxis": {"title": {"text": 'Intensity'}},
            "series": [
                    {"name": 'spectrum', "data": [[ii, jj ] for ii,jj in zip (np.round(chartdata[0]['x'],5), chartdata[0]['y'])]},
                ],
        },
    }
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


@ensure_csrf_cookie
def MCFxic_detail(request, dataset_pk, standard_pk, adduct_pk):
    dataset=get_object_or_404(Dataset, pk=dataset_pk)
    standard=get_object_or_404(Standard, pk=standard_pk)
    adduct=get_object_or_404(Adduct, pk=adduct_pk)
    mz=standard.molecule.get_mz(adduct)
    delta_mz = mz*dataset.mass_accuracy_ppm*1e-6
    xics=Xic.objects.all().filter(dataset=dataset).filter(mz__gte=mz-delta_mz).filter(mz__lte=mz+delta_mz)
    frag_specs = FragmentationSpectrum.objects.all().filter(dataset=dataset).filter(precursor_mz__gte=mz-delta_mz).filter(precursor_mz__lte=mz+delta_mz)
    form = FragSpecReview(request.POST or None, extra=list([fs.pk for fs in frag_specs]), user=request.user)
    if form.is_valid():
        for (fragSpecId, response) in form.get_response():
            #todo update fields in frag spectra
            logging.debug((form.user,fragSpecId,response))
            tools.update_fragSpec(fragSpecId, response, standard, adduct, request.user.username)
        return redirect('MCFdataset-detail',dataset_pk)
    else:
        chartdata = []
        for xic in xics:
            chartdata.append(
                 {'name': xic.mz, 'x': xic.rt, 'y': xic.xic, 'extra': {}, 'kwargs': {}},
             )
        charttype = "lineWithFocusChart"
        chartcontainer = 'discretebarchart_container'  # container name
        chartID = 'chart_ID'
        chart_type = 'line'
        chart_height = 500
        data = {
            'form':form,
            'charttype': charttype,
            'chartdata': chartdata,
            'chartcontainer': chartcontainer,
            'extra': {
                'x_is_date': False,
                'x_axis_format': '',
                'tag_script_js': True,
                'jquery_on_ready': True,
                },
            "highchart":{
                "chart_id": 'chart_id',
                "chart": {"renderTo": 'chart_id', "type": chart_type, "height": 300, "zoomType": "x"},
                "title": {"text": ''},
                "xAxis":  {"title": {"text": 'time (s)'},},
                "yAxis": {"title": {"text": 'Intensity'}},
                "series": [
                        {"name": 'xic', "data": [[ii, jj ] for ii,jj in zip (np.round(chartdata[0]['x'],5), chartdata[0]['y'])]},
                    ],
            },
            "mz":mz,
            "dataset":dataset,
            "standard":standard,
            "adduct":adduct,
            "xics":xics,
            "frag_specs":frag_specs,
            "frag_spec_highchart": [{
                "chart_id": 'frag_spec{}'.format(spec.id),
                "chart": {"renderTo": 'chart_id', "type": chart_type, "height": 300, "zoomType": "x"},
                "title": {"text": ''},
                "xAxis":  {"title": {"text": 'm/z'},},
                "yAxis": {"title": {"text": 'Intensity'}},
                "series": [
                        {"name": 'fragment spectrum', "data": [[x+d,y*m] for x,y in zip(np.round(spec.centroid_mzs,5), spec.centroid_ints) for d,m in zip([-0.0001,0,0.0001],[0,1,0])]
                            },
                    ],} for spec in frag_specs]
        }
        return render(request, 'mcf_standards_browse/mcf_xic_detail.html', context=data)

@login_required()
def dataset_upload(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            post_dict = dict(request.POST)
            data = {"adducts": post_dict['adducts'],
                    "standards": post_dict['standards'],
                    "mass_accuracy_ppm": post_dict['mass_accuracy_ppm'][0],
                    "quad_window_mz": post_dict['quad_window_mz'][0]}
            r= tools.handle_uploaded_files(data, request.FILES['mzml_file'])
            logging.debug("added = {}".format(r))
            return redirect('MCFdataset-list')
    else:
        form = UploadFileForm(initial={"mass_accuracy_ppm":10.0, 'quad_window_mz':1.0})
    return render(request, 'mcf_standards_browse/dataset_upload.html', {'form': form})

