import os

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie

import tasks
from models import Standard, FragmentationSpectrum, Dataset, Adduct, Xic, Molecule
from .forms import MCFAdductForm, MCFMoleculeForm, MCFStandardForm, UploadFileForm, FragSpecReview, MCFStandardBatchForm, ExportLibrary
import numpy as np
import tools
import logging
import os
import time
from django.views.generic import TemplateView, ListView
from django.contrib.auth.decorators import login_required
import csv
import zipfile
from django.http import StreamingHttpResponse
from django.template import loader, Context
from django.conf import settings
from django.db.models import Q

# Create your views here.

def home_page(request):
    return render(request,'mcf_standards_browse/home_page.html',)

def about(request):
    return render(request,'mcf_standards_browse/about.html',)


def MCFStandard_list(request):
    #page_size = 10
    #pagenr = int(request.GET["pagenr"])
    standards = Standard.objects.all()#[pagenr * page_size:(pagenr + 1) * page_size]
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
    frag_specs = FragmentationSpectrum.objects.all().filter(standard=standard)
    chart_type = 'line'
    chart_height=300
    data={
        "standard":standard,
        "frag_specs":frag_specs,
        "frag_spec_highchart": [{
                "chart_id": 'frag_spec{}'.format(spec.id),
                "chart": {"type": chart_type, "height": chart_height, "zoomType": "x"},
                "title": {"text": ''},
                "xAxis":  {"title": {"text": 'm/z'},},
                "yAxis": {"title": {"text": 'Intensity'}},
                "series": [
                        {"name": 'fragment spectrum', "data": [[x+d,y*m] for x,y in zip(np.round(spec.centroid_mzs,5), spec.centroid_ints) for d,m in zip([-0.00,0,0.00 ],[0,1,0])]
                            },
                    ],} for spec in frag_specs]
          }
    return render(request, 'mcf_standards_browse/mcf_standard_detail.html', data)

def MCFMolecule_detail(request, pk):
    molecule=get_object_or_404(Molecule, pk=pk)
    standards = Standard.objects.all().filter(molecule=molecule)
    frag_specs = []
    for standard in standards:
        frag_specs.extend(FragmentationSpectrum.objects.all().filter(standard=standard))
    chart_type = 'line'
    chart_height=300
    data={
        'molecule': molecule,
        "standards":[[standard,FragmentationSpectrum.objects.all().filter(standard=standard)] for standard in standards],
        "frag_spec_highchart": [{
                "chart_id": 'frag_spec{}'.format(spec.id),
                "chart": {"type": chart_type, "height": chart_height, "zoomType": "x"},
                "title": {"text": ''},
                "xAxis":  {"title": {"text": 'm/z'},},
                "yAxis": {"title": {"text": 'Intensity'}},
                "series": [
                        {"name": 'fragment spectrum', "data": [[x+d,y*m] for x,y in zip(np.round(spec.centroid_mzs,5), spec.centroid_ints) for d,m in zip([-0.00,0,0.00 ],[0,1,0])]
                            },
                    ],} for spec in frag_specs]
          }
    return render(request, 'mcf_standards_browse/mcf_molecule_detail.html', data)

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
def MCFAdduct_add(request):
    if request.method == "POST":
        form = MCFAdductForm(request.POST)
        if form.is_valid():
            if Adduct.objects.filter(nM=request.POST['nM'], delta_formula=request.POST['delta_formula']).exists():
                error_list =[("adduct already exists","{} {}".format(request.POST['nM'], request.POST['delta_formula']))]
                return render(request, 'mcf_standards_browse/upload_error.html', {'error_list': error_list})
            adduct=form.save()
            adduct.save()
            tools.update_mzs()
        return redirect("/")
    else:
        form = MCFAdductForm()
    return render(request,'mcf_standards_browse/mcf_adduct_add.html', {'form':form})


@login_required()
def MCFStandard_add_batch(request):
    logging.debug(request.FILES)
    if request.method == "POST":
        form = MCFStandardBatchForm(request.POST, request.FILES)
        if form.is_valid():
            tasks.add_batch_standard.delay({'username': request.user.username}, request.FILES[
                'semicolon_delimited_file'])
            return redirect('MCFStandard-list')
    else:
        form = MCFStandardBatchForm()
    return render(request,'mcf_standards_browse/mcf_standard_add.html', {'form':form, 'form_type':'batch'})


def error_page(request):
    return render(request,'mcf_standards_browse/upload_error.html')


def fragmentSpectrum_list(request):
    logging.debug(request)
    if request.method == "POST":
        logging.debug('got some post')
        logging.debug(request.POST)
    fragmentSpectra = FragmentationSpectrum.objects.all().filter(~Q(standard=None))
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
    return render(request, 'mcf_standards_browse/mcf_fragmentSpectrum_detail.html', data)

def MCFdataset_list(request):
    datasets = Dataset.objects.all()
    return render(request,'mcf_standards_browse/mcf_dataset_list.html',{'datasets':datasets})

def MCFdataset_detail(request, pk):
    dataset=get_object_or_404(Dataset, pk=pk)
    adducts = dataset.adducts_present.all()
    standards = dataset.standards_present.all().order_by('MCFID')
    table_list = []
    for standard in standards:
        for adduct in adducts:
            mz=standard.molecule.get_mz(adduct)
            delta_mz = mz*dataset.mass_accuracy_ppm*1e-6
            table_list.append(
                [standard,
                 adduct,
                 int(np.sum(Xic.objects.get(standard=standard,adduct=adduct,dataset=dataset).xic)),
                 FragmentationSpectrum.objects.all().filter(dataset=dataset).filter(precursor_mz__gte=mz-delta_mz).filter(precursor_mz__lte=mz+delta_mz).count(),
                ]
                )

#    data = {'dataset':dataset,
#            'adducts':adducts,
#            'standards':standards,
#            'xics':xics}
    data = {'table_data':table_list,
            'dataset': dataset}
    logging.debug(table_list)
    return render(request, 'mcf_standards_browse/mcf_dataset_detail.html', data)


@ensure_csrf_cookie
def MCFxic_detail(request, dataset_pk, standard_pk, adduct_pk):
    dataset=get_object_or_404(Dataset, pk=dataset_pk)
    standard=get_object_or_404(Standard, pk=standard_pk)
    adduct=get_object_or_404(Adduct, pk=adduct_pk)
    mz=standard.molecule.get_mz(adduct)
    delta_mz = mz*dataset.mass_accuracy_ppm*1e-6
    #xics=Xic.objects.all().filter(dataset=dataset).filter(mz__gte=mz-delta_mz).filter(mz__lte=mz+delta_mz)
    xics = Xic.objects.all().filter(standard=standard,adduct=adduct,dataset=dataset)
    frag_specs = FragmentationSpectrum.objects.all().filter(dataset=dataset).filter(precursor_mz__gte=mz-delta_mz).filter(precursor_mz__lte=mz+delta_mz).order_by('-ms1_intensity')[:20]
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
        chart_height = 300
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
                "chart": {"renderTo": 'chart_id', "type": chart_type, "height": chart_height, "zoomType": "x"},
                "title": {"text": ''},
                "xAxis":  {"title": {"text": 'time (s)'},},
                "yAxis": {"title": {"text": 'Intensity'}},
                "series": [
                        {"name": 'xic', "data": [[ii, jj ] for ii,jj in zip (np.round(chartdata[0]['x'],5), chartdata[0]['y'])]},
                        {"name": 'ms2', "data": [[frag_specs[ii].rt, 0] for ii in np.argsort([spec.rt for spec in frag_specs])],
                          'lineColor':'black',
                         "marker":{ "symbol": 'triangle',
                                    }
                         }
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
                        {"name": 'fragment spectrum', "data": [[x+d,y*m] for x,y in zip(np.round(spec.centroid_mzs,5), spec.centroid_ints) for d,m in zip([-0.00,0,0.00 ],[0,1,0])]
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
            files_dict=dict(request.FILES)
            logging.debug(files_dict)
            data = {"adducts": post_dict['adducts'],
                    "standards": post_dict['standards'],
                    "mass_accuracy_ppm": post_dict['mass_accuracy_ppm'][0],
                    "quad_window_mz": post_dict['quad_window_mz'][0]}
            uploaded_file = request.FILES['mzml_file']
            mzml_filename = os.path.join(settings.MEDIA_ROOT, uploaded_file.name)
            with open(mzml_filename, 'w') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            tasks.handle_uploaded_files.delay(data, mzml_filename)

            return redirect('MCFdataset-list')
    else:
        form = UploadFileForm(initial={"mass_accuracy_ppm":10.0, 'quad_window_mz':1.0})
    return render(request, 'mcf_standards_browse/dataset_upload.html', {'form': form})


class Echo(object):
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value

def fragmentSpectrum_export(request):
    if request.method=='POST':
        form = ExportLibrary(request.POST)
        if form.is_valid():
            post_dict = dict(request.POST)
            spectra_to_export_id =int(post_dict['spectra_to_export'][0])
            if spectra_to_export_id  == 0:
                spectra = FragmentationSpectrum.objects.all().filter(reviewed=True).exclude(standard=None)
            elif spectra_to_export_id  == 1:
                spectra = FragmentationSpectrum.objects.all().filter(reviewed=True)
            elif spectra_to_export_id == 2:
                spectra = FragmentationSpectrum.objects.all()
            else:
                raise ValueError('export code not known')
            pseudo_buffer = Echo()
            data_format_id = int(post_dict['data_format'][0])
            spec_pairs =  [[spectrum, zip(spectrum.centroid_mzs, spectrum.centroid_ints)] for spectrum in spectra]
            c = Context({'spec_data': spec_pairs})
            if data_format_id   == 0: #mgf
                content_type = "text/txt"
                response=HttpResponse(content_type=content_type)
                response['Content-Disposition'] = 'attachment; filename=mcf_spectra.mgf'
                t = loader.get_template('mcf_standards_browse/mgf_template.mgf')
                response.write(t.render(c))
            elif data_format_id   == 1: #mgf
                content_type = "text/txt"
                response=HttpResponse(content_type=content_type)
                response['Content-Disposition'] = 'attachment; filename=mcf_spectra.msp'
                t = loader.get_template('mcf_standards_browse/mgf_template.msp')
                response.write(t.render(c))
            elif data_format_id == 2: #csv
                writer = csv.writer(pseudo_buffer)
                content_type = "text/csv"
                response = StreamingHttpResponse((writer.writerow([spectrum.pk, spectrum.centroid_mzs, spectrum.centroid_ints]) for spectrum in spectra),
                                     content_type=content_type)
                response['Content-Disposition'] = 'attachment; filename=mcf_spectra.csv'
            elif data_format_id == 3: #ebi json
                # if you wanted to do this in memory
                # in_memory = StringIO()
                # zip = ZipFile(in_memory, "w")
                zf_n = os.path.join(settings.MEDIA_ROOT,'tmp_ebi_export.zip')
                zf = zipfile.ZipFile(zf_n, mode="w")
                filename_list = []
                for ii,cc in enumerate(c['spec_data']):
                    if cc[0].standard:
                        export_filename = "MCFID{}".format(cc[0].standard.MCFID)
                    else:
                        export_filename = 'unknown_standard'
                    ii=0
                    _export_filename = export_filename
                    while _export_filename in filename_list:
                        _export_filename = "{}_{}".format(export_filename,ii)
                        ii +=1
                    export_filename = _export_filename
                    filename_list.append(export_filename)
                    logging.debug(export_filename)
                    t = loader.get_template('mcf_standards_browse/export_template_ebi.json')
                    r = t.render({'spec_data':[cc,]})
                    info = zipfile.ZipInfo(export_filename.format(ii),
                           date_time=time.localtime(time.time()),
                           )
                    info.compress_type=zipfile.ZIP_DEFLATED
                    info.comment='Remarks go here'
                    info.create_system=0
                    zf.writestr(info, r)
                zf.close()
                logging.debug('open file: ')
                zfr = zipfile.ZipFile(zf_n, 'r')
                logging.debug(zfr.read(export_filename))
                response = HttpResponse(content_type="application/zip")
                response['Content-Disposition'] = 'attachment; filename="mcf_spectra.zip"'
                response.write(open(zf_n,'r').read())
            return response
    else:
        form=ExportLibrary()
    return render(request, 'mcf_standards_browse/export_library.html', {'form':form})


@login_required()
def MCFMolecule_cleandb(request):
    n_clean, clean_name = tools.clear_molecules_without_standard()
    logging.debug("{} molecules removed".format(n_clean))
    error_list = []
    for name in clean_name:
        error_list.append([name, 'removed'])
    logging.debug(error_list)
    return render(request,'mcf_standards_browse/upload_error.html',{'error_list':error_list})

