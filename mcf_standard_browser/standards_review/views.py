import json
import logging
import os
import time
import zipfile
from collections import Counter, defaultdict
from tempfile import TemporaryFile

import numpy as np
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, FileResponse
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.template import loader
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import CreateView
from django.views.generic import TemplateView, ListView
from django_tables2 import RequestConfig
from table.views import FeedDataView

import tasks
import tools
from models import Standard, FragmentationSpectrum, Dataset, Adduct, Xic, Molecule, MoleculeSpectraCount, MoleculeTag, \
    LcInfo, MsInfo, InstrumentInfo
from tables import StandardTable, MoleculeTable, SpectraTable, DatasetListTable
from .forms import AdductForm, MoleculeForm, StandardForm, UploadFileForm, FragSpecReview, \
    StandardBatchForm, ExportLibrary, MoleculeTagForm, StandardAddForm


# Create your views here.

def home_page(request):
    return render(request, 'mcf_standards_browse/home_page.html', )


def about(request):
    return render(request, 'mcf_standards_browse/about.html', )

def about_curatr(request):
    return render(request, 'mcf_standards_browse/about_curatr.html', )


def curate_home(request):
    return render(request,'mcf_standards_browse/curate_home.html', )

def library_home(request):
    return render(request,'mcf_standards_browse/library_home.html', )


def standard_list(request):
    icontains_fields = ['inventory_id', 'molecule__name', 'molecule__sum_formula', 'molecule__exact_mass', 'vendor',
                        'vendor_cat', 'molecule__pubchem_id']
    search_string = request.GET.get('search', None)
    qs = Standard.objects.all()
    if search_string:
        queries = [Q(**{field + '__icontains': search_string}) for field in icontains_fields]
        search_query = queries.pop()
        for q in queries:
            search_query |= q
        qs = qs.filter(search_query)
    table = StandardTable(qs, attrs={'id': 'molecule_list', 'class': 'table table-striped'})
    RequestConfig(request).configure(table)
    return render(request, "mcf_standards_browse/mcf_standard_list.html", {'standard_list': table})


def molecule_list(request):
    icontains_fields = [
        'name', 'sum_formula', 'exact_mass', 'pubchem_id', 'moleculespectracount__spectra_count', 'tags__name',
        '_adduct_mzs']
    search_string = request.GET.get('search', None)
    qs = Molecule.objects.all()
    if search_string:
        queries = [Q(**{field + '__icontains': search_string}) for field in icontains_fields]
        search_query = queries.pop()
        for q in queries:
            search_query |= q
        qs = qs.filter(search_query)
    table = MoleculeTable(qs, attrs={'id': 'molecule_list', 'class': 'table table-striped'})
    RequestConfig(request).configure(table)
    molecules_with_spectra = MoleculeSpectraCount.objects.filter(spectra_count__gt=0).count()
    return render(request, 'mcf_standards_browse/mcf_molecule_list.html',
                  {'molecule_list': table, 'molecules_with_spectra': molecules_with_spectra})


class IndexView(TemplateView):
    template_name = 'mcf_standards_browse/home_page.html'


class ServerSideView(TemplateView):
    template_name = 'mcf_standards_browse/server-side-base.html'
    model = Standard
    context_object_name = 'browsers'


class Standard_list_ez(ListView):
    template_name = 'eztables/client_side.html'
    model = Standard
    # fields = ('name',
    #        'sum_formula',
    #         'MCFID',)
    context_object_name = 'standards'


def standard_detail(request, mcfid):
    standard = get_object_or_404(Standard, inventory_id=mcfid)
    frag_specs = FragmentationSpectrum.objects.all().filter(standard=standard)
    chart_type = 'line'
    chart_height = 300
    data = {
        "standard": standard,
        "frag_specs": frag_specs,
        "frag_spec_highchart": [{
                                    "chart_id": 'frag_spec{}'.format(spec.id),
                                    "chart": {"type": chart_type, "height": chart_height, "zoomType": "x"},
                                    "title": {"text": ''},
                                    "xAxis": {"title": {"text": 'm/z'},},
                                    "yAxis": {"title": {"text": 'Intensity'}},
                                    "series": [
                                        {"name": 'fragment spectrum', "data": [[x + d, y * m] for x, y in
                                                                               zip(np.round(spec.centroid_mzs, 5),
                                                                                   spec.centroid_ints) for d, m in
                                                                               zip([-0.00, 0, 0.00], [0, 1, 0])]
                                         },
                                    ],} for spec in frag_specs]
    }
    return render(request, 'mcf_standards_browse/mcf_standard_detail.html', data)


def molecule_detail(request, pk):
    molecule = get_object_or_404(Molecule, pk=pk)
    standards = Standard.objects.all().filter(molecule=molecule)
    frag_specs = []
    for standard in standards:
        frag_specs.extend(FragmentationSpectrum.objects.all().filter(standard=standard))
    chart_type = 'line'
    chart_height = 300
    data = {
        'molecule': molecule,
        "standards": [[standard, FragmentationSpectrum.objects.all().filter(standard=standard)] for standard in
                      standards],
        "frag_spec_highchart": [{
                                    "chart_id": 'frag_spec{}'.format(spec.id),
                                    "chart": {"type": chart_type, "height": chart_height, "zoomType": "x"},
                                    "title": {"text": ''},
                                    "xAxis": {"title": {"text": 'm/z'},},
                                    "yAxis": {"title": {"text": 'Intensity'}},
                                    "series": [
                                        {"name": 'fragment spectrum', "data": [[x + d, y * m] for x, y in
                                                                               zip(np.round(spec.centroid_mzs, 5),
                                                                                   spec.centroid_ints) for d, m in
                                                                               zip([-0.00, 0, 0.00], [0, 1, 0])]
                                         },
                                    ],} for spec in frag_specs]
    }
    return render(request, 'mcf_standards_browse/mcf_molecule_detail.html', data)


@login_required()
def standard_add(request):
    if request.method == "POST":
        form = StandardAddForm(request.POST)
        if form.is_valid():
            standard = form.save()
            standard.save()
            return redirect('standard-list')
    else:
        form = StandardAddForm()
    return render(request, 'mcf_standards_browse/mcf_standard_add.html', {'form': form, 'form_type': 'single'})


@login_required()
def standard_edit(request, mcfid):
    standard = get_object_or_404(Standard, inventory_id=mcfid)
    if request.method == "POST":
        form = StandardForm(request.POST, instance=standard)
        if form.is_valid():
            standard = form.save()
            standard.save()
            return redirect('standard-list')
    else:
        form = StandardForm(instance=standard)
    return render(request, 'mcf_standards_browse/mcf_standard_edit.html', {'form': form,})


@login_required()
def molecule_add(request):
    logging.debug('add molecule')
    if request.method == "POST":
        form = MoleculeForm(request.POST)
        if form.is_valid():
            molecule = form.save()
            molecule.save()
            return redirect('molecule-list')
    else:
        form = MoleculeForm()
    return render(request, 'mcf_standards_browse/mcf_molecule_add.html', {'form': form, 'form_type': 'single'})


class MoleculetagAdd(CreateView):
    template_name = 'mcf_standards_browse/mcf_moleculetag_add.html'
    model = MoleculeTag
    form = MoleculeTagForm
    fields = ['name']
    success_url = '/'


@login_required()
def molecule_edit(request, pk):
    molecule = get_object_or_404(Molecule, pk=pk)
    standards = Standard.objects.all().filter(molecule=molecule)
    if request.method == "POST":
        form = MoleculeForm(request.POST, instance=molecule)
        if form.is_valid():
            standard = form.save()
            standard.save()
            return redirect('standard-list')
    else:
        form = MoleculeForm(instance=molecule)
    return render(request, 'mcf_standards_browse/mcf_molecule_edit.html',
                  {'form': form, 'standards': standards, 'molecule': molecule})


@login_required()
def adduct_add(request):
    if request.method == "POST":
        form = AdductForm(request.POST)
        if form.is_valid():
            if Adduct.objects.filter(nM=request.POST['nM'], delta_formula=request.POST['delta_formula']).exists():
                error_list = [
                    ("adduct already exists", "{} {}".format(request.POST['nM'], request.POST['delta_formula']))]
                return render(request, 'mcf_standards_browse/upload_error.html', {'error_list': error_list})
            adduct = form.save()
            adduct.save()
            tools.update_mzs()
        return redirect("/")
    else:
        form = AdductForm()
    return render(request, 'mcf_standards_browse/mcf_adduct_add.html', {'form': form})


@login_required()
def standard_add_batch(request):
    logging.debug(request.FILES)
    if request.method == "POST":
        form = StandardBatchForm(request.POST, request.FILES)
        if form.is_valid():
            tasks.add_batch_standard.delay({'username': request.user.username}, request.FILES[
                'tab_delimited_file'])
            return redirect('standard-list')
    else:
        form = StandardBatchForm()
    return render(request, 'mcf_standards_browse/mcf_standard_add.html', {'form': form, 'form_type': 'batch'})


def error_page(request):
    return render(request, 'mcf_standards_browse/upload_error.html')


def fragmentSpectrum_list(request):
    table = SpectraTable()
    return render(request, 'mcf_standards_browse/mcf_fragmentSpectrum_list.html', {'spectra_list': table})


class SpectraListView(FeedDataView):
    token = SpectraTable.token

    def filter_queryset(self, queryset):
        return super(SpectraListView, self).filter_queryset(queryset).filter(~Q(standard=None))


def fragmentSpectrum_detail(request, pk):
    spectrum = get_object_or_404(FragmentationSpectrum, pk=pk)
    splash_payload = json.dumps({
        "ions": [{"mass": mz, "intensity": int_} for mz, int_ in zip(spectrum.centroid_mzs, spectrum.centroid_ints)],
        "type": "MS"})
    xdata = np.concatenate((spectrum.centroid_mzs,
                            spectrum.centroid_mzs[0:-1] / 2. + spectrum.centroid_mzs[1:] / 2.,
                            spectrum.centroid_mzs + 0.00001,
                            spectrum.centroid_mzs - 0.00001,
                            np.arange(int(spectrum.centroid_mzs[0] - 1), int(spectrum.centroid_mzs[-1] + 1), 1),))
    n_mzs = len(xdata)
    ydata = np.concatenate((spectrum.centroid_ints,
                            np.zeros((n_mzs - 1,)),
                            np.zeros((n_mzs,)),
                            np.zeros((n_mzs,)),
                            np.zeros(spectrum.centroid_mzs[1], spectrum.centroid_mzs[0] + 2, ),))
    idx = np.argsort(xdata)
    xdata = xdata[idx][1:-1]
    ydata = ydata[idx][1:-1]

    extra_serie1 = {"tooltip": {"y_start": "", "y_end": " "}}
    chartdata = [{
        'x': xdata, 'name': 'intensity', 'y': ydata, 'extra': extra_serie1, 'kwargs': {}
    }, ]
    # charttype = "discreteBarChart"
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
        'specdata': {
            'spectrum': spectrum,
            'centroids': [spectrum.centroid_mzs, spectrum.centroid_ints],
        },
        "highchart": {
            "chart_id": 'chart_id',
            "chart": {"renderTo": 'chart_id', "type": chart_type, "height": chart_height, "zoomType": "x"},
            "title": {"text": 'Fragment Spectrum'},
            "xAxis": {"title": {"text": 'm/z'},},
            "yAxis": {"title": {"text": 'Intensity'}},
            "series": [
                {"name": 'spectrum',
                 "data": [[ii, jj] for ii, jj in zip(np.round(chartdata[0]['x'], 5), chartdata[0]['y'])]},
            ],
        },
        "splash_payload": splash_payload,
    }
    return render(request, 'mcf_standards_browse/mcf_fragmentSpectrum_detail.html', data)


def dataset_list(request):
    table = DatasetListTable()
    return render(request, 'mcf_standards_browse/mcf_dataset_list.html', {'dataset_list': table})


def dataset_detail(request, pk):
    if request.method == 'GET':
        return dataset_detail_show(request, pk)
    elif request.method == 'POST':
        return dataset_delete(request, pk)
    else:
        raise Http404()


def dataset_detail_show(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk)
    adducts = dataset.adducts_present.all()
    standards = dataset.standards_present.all().order_by('inventory_id')
    table_list = []
    for standard in standards:
        for adduct in adducts:
            mz = standard.molecule.get_mz(adduct)
            delta_mz = mz * dataset.mass_accuracy_ppm * 1e-6
            table_list.append(
                [standard,
                 adduct,
                 int(np.sum(Xic.objects.get(standard=standard, adduct=adduct, dataset=dataset).xic)),
                 FragmentationSpectrum.objects.all().filter(dataset=dataset).filter(
                     precursor_mz__gte=mz - delta_mz).filter(precursor_mz__lte=mz + delta_mz).count(),
                 ]
            )

        #    data = {'dataset':dataset,
        #            'adducts':adducts,
        #            'standards':standards,
        #            'xics':xics}
    data = {'table_data': table_list,
            'dataset': dataset}
    logging.debug(table_list)
    return render(request, 'mcf_standards_browse/mcf_dataset_detail.html', data)


@login_required()
def dataset_delete(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk)
    path = dataset.path
    dataset.delete()
    try:
        os.remove(path)
    except OSError:
        logging.error("Failed to remove {} from filesystem. The file probably doesn't exist".format(path))
    return redirect('/dataset')


@ensure_csrf_cookie
def xic_detail(request, dataset_pk, mcfid, adduct_pk):
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    standard = get_object_or_404(Standard, inventory_id=mcfid)
    adduct = get_object_or_404(Adduct, pk=adduct_pk)
    mz = standard.molecule.get_mz(adduct)
    delta_mz = mz * dataset.mass_accuracy_ppm * 1e-6
    # xics=Xic.objects.all().filter(dataset=dataset).filter(mz__gte=mz-delta_mz).filter(mz__lte=mz+delta_mz)
    xics = Xic.objects.all().filter(standard=standard, adduct=adduct, dataset=dataset)
    frag_specs = FragmentationSpectrum.objects.all().filter(dataset=dataset).filter(
        precursor_mz__gte=mz - delta_mz).filter(precursor_mz__lte=mz + delta_mz).order_by('-ms1_intensity')[:20]
    form = FragSpecReview(request.POST or None, extra=list([fs.pk for fs in frag_specs]), user=request.user)
    if form.is_valid():
        for (fragSpecId, response) in form.get_response():
            # todo update fields in frag spectra
            logging.debug((form.user, fragSpecId, response))
            tools.update_fragSpec(fragSpecId, response, standard, adduct, request.user.username)
        return redirect('dataset-detail', dataset_pk)
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
            'form': form,
            'charttype': charttype,
            'chartdata': chartdata,
            'chartcontainer': chartcontainer,
            'extra': {
                'x_is_date': False,
                'x_axis_format': '',
                'tag_script_js': True,
                'jquery_on_ready': True,
            },
            "highchart": {
                "chart_id": 'chart_id',
                "chart": {"renderTo": 'chart_id', "type": chart_type, "height": chart_height, "zoomType": "x"},
                "title": {"text": ''},
                "xAxis": {"title": {"text": 'time (s)'},},
                "yAxis": {"title": {"text": 'Intensity'}},
                "series": [
                    {"name": 'xic',
                     "data": [[ii, jj] for ii, jj in zip(np.round(chartdata[0]['x'], 5), chartdata[0]['y'])]},
                    {"name": 'ms2',
                     "data": [[frag_specs[ii].rt, 0] for ii in np.argsort([spec.rt for spec in frag_specs])],
                     'lineColor': 'black',
                     "marker": {"symbol": 'triangle',
                                }
                     }
                ],
            },
            "mz": mz,
            "dataset": dataset,
            "standard": standard,
            "adduct": adduct,
            "xics": xics,
            "frag_specs": frag_specs,
            "frag_spec_highchart": [{
                                        "chart_id": 'frag_spec{}'.format(spec.id),
                                        "chart": {"renderTo": 'chart_id', "type": chart_type, "height": 300,
                                                  "zoomType": "x"},
                                        "title": {"text": ''},
                                        "xAxis": {"title": {"text": 'm/z'},
                                                  "max": spec.precursor_mz + 2 * spec.dataset.quad_window_mz},
                                        "yAxis": {"title": {"text": 'Intensity'}},
                                        "series": [
                                            {"name": 'fragment spectrum', "data": [[x + d, y * m] for x, y in
                                                                                   zip(np.round(spec.centroid_mzs, 5),
                                                                                       spec.centroid_ints) for d, m in
                                                                                   zip([-0.00, 0, 0.00], [0, 1, 0])]
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
            files_dict = dict(request.FILES)
            logging.debug(files_dict)
            logging.debug(post_dict)
            data = {"adducts": post_dict['adducts'],
                    "standards": post_dict['standards'],
                    "mass_accuracy_ppm": post_dict['mass_accuracy_ppm'][0],
                    "quad_window_mz": post_dict['quad_window_mz'][0],
                    "lc_info": post_dict['lc_info'][0],
                    "ms_info": post_dict['ms_info'][0],
                    "instrument_info": post_dict['instrument_info'][0],
                    "ionization_method": post_dict['ionization_method'][0],
                    "ion_analyzer": post_dict['ion_analyzer'][0]}
            uploaded_file = request.FILES['mzml_file']
            base_name, extension = os.path.splitext(uploaded_file.name)
            d = Dataset(name=uploaded_file.name, processing_finished=False)
            d.save()
            mzml_filename = "{}-{}{}".format(base_name, d.id, extension)
            mzml_filepath = os.path.join(settings.MEDIA_ROOT, mzml_filename)
            logging.debug("mzML filepath: " + mzml_filepath)
            logging.debug("original mzML filename: " + uploaded_file.name)
            with open(mzml_filepath, 'w') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            d.path = mzml_filepath
            d.save()
            tasks.handle_uploaded_files.delay(data, mzml_filepath, d)
            return redirect('dataset-list')
    else:
        form = UploadFileForm(initial={"mass_accuracy_ppm": 10.0, 'quad_window_mz': 1.0, 'ion_analyzer': 'QFT',
                                       'ionization_method': 'ESI'})
    autocomplete = {
        'lc_info': [str(info.content) for info in LcInfo.objects.all()],
        'ms_info': [str(info.content) for info in MsInfo.objects.all()],
        'instrument_info': [str(info.content) for info in InstrumentInfo.objects.all()],
        'ionization_method': json.dumps(
            list(set(Dataset.objects.values_list('ionization_method', flat=True).distinct()).union(
                ['APCI', 'APPI', 'EI', 'ESI', 'FAB', 'MALDI']))),
        'ion_analyzer': json.dumps(list(set(Dataset.objects.values_list('ion_analyzer', flat=True).distinct()).union(
            tools.sum_of_2_perms(['B', 'E', 'FT', 'IT', 'Q', 'TOF']))))
    }
    return render(request, 'mcf_standards_browse/dataset_upload.html', {'form': form, 'autocomplete': autocomplete})


class Echo(object):
    #An object that implements just the write method of the file-like interface.

    def write(self, value):
        #Write the value by returning it, instead of storing in a buffer.
        return value


def fragmentSpectrum_export(request):
    if request.method == 'POST':
        form = ExportLibrary(request.POST)
        if form.is_valid():
            post_dict = dict(request.POST)
            #spectra_to_export_id = int(post_dict['spectra_to_export'][0])
            spectra = FragmentationSpectrum.objects.all().filter(reviewed=True).exclude(standard=None)
            #if spectra_to_export_id == 0:
            #    spectra = FragmentationSpectrum.objects.all().filter(reviewed=True).exclude(standard=None)
            #elif spectra_to_export_id == 1:
            #    spectra = FragmentationSpectrum.objects.all().filter(reviewed=True)
            #elif spectra_to_export_id == 2:
            #    spectra = FragmentationSpectrum.objects.all()
            #else:
            #    raise ValueError('export code not known')
            class_to_export_id = int(post_dict['class_to_export'][0])
            if class_to_export_id == 0: # all
                spectra = spectra
            if class_to_export_id == 1: # positive
                spectra = spectra.exclude(adduct__charge__lte=0)
            if class_to_export_id == 2: # negative
                spectra = spectra.exclude(adduct__charge__gte=0)
            data_format_id = int(post_dict['data_format'][0])
            spec_pairs = [[spectrum, zip(spectrum.centroid_mzs, spectrum.centroid_ints, 1000/(np.max(spectrum.centroid_ints))*spectrum.centroid_ints)] for spectrum in spectra]
            c = {'spec_data': spec_pairs}
            if data_format_id == 0:  # mgf
                content_type = "text/txt"
                response = HttpResponse(content_type=content_type)
                response['Content-Disposition'] = 'attachment; filename=mcf_spectra.mgf'
                t = loader.get_template('mcf_standards_browse/mgf_template.mgf')
                response.write(t.render(c))
            elif data_format_id == 1:  # msp
                content_type = "text/txt"
                response = HttpResponse(content_type=content_type)
                response['Content-Disposition'] = 'attachment; filename=mcf_spectra.msp'
                t = loader.get_template('mcf_standards_browse/mgf_template.msp')
                response.write(t.render(c))
            elif data_format_id == 2:  # csv
                content_type = "text/tsv"
                response = HttpResponse(content_type=content_type)
                response['Content-Disposition'] = 'attachment; filename=mcf_spectra.tsv'
                t = loader.get_template('mcf_standards_browse/spectra_export_template.csv')
                response.write(t.render(c))
                # writer = csv.writer(pseudo_buffer, dialect='excel')
                # content_type = "text/csv"
                # response = StreamingHttpResponse((writer.writerow([spectrum.dataset, spectrum.precursor_mz, spectrum.spec_num, spectrum.standard, spectrum.adduct, spectrum.centroid_mzs, spectrum.centroid_ints]) for spectrum in spectra),
                #                     content_type=content_type)
                # response['Content-Disposition'] = 'attachment; filename=mcf_spectra.csv'
            elif data_format_id == 3:  # ebi json
                # if you wanted to do this in memory
                # in_memory = StringIO()
                # zip = ZipFile(in_memory, "w")
                zf_n = os.path.join(settings.MEDIA_ROOT, 'tmp_ebi_export.zip')
                zf = zipfile.ZipFile(zf_n, mode="w")
                filename_list = []
                for cc in spec_pairs:
                    if cc[0].standard:
                        export_filename = "InventoryID{}".format(cc[0].standard.inventory_id)
                    else:
                        export_filename = 'unknown_standard'
                    ii = 0
                    _export_filename = export_filename
                    while _export_filename in filename_list:
                        _export_filename = "{}_{}".format(export_filename, ii)
                        ii += 1
                    export_filename = _export_filename
                    filename_list.append(export_filename)
                    logging.debug(export_filename)
                    t = loader.get_template('mcf_standards_browse/export_template_ebi.json')
                    r = t.render({'spec_data': [cc, ]})
                    info = zipfile.ZipInfo(export_filename.format(ii),
                                           date_time=time.localtime(time.time()),
                                           )
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.comment = 'Remarks go here'
                    info.create_system = 0
                    zf.writestr(info, r)
                zf.close()
                logging.debug('open file: ')
                zfr = zipfile.ZipFile(zf_n, 'r')
                logging.debug(zfr.read(export_filename))
                response = HttpResponse(content_type="application/zip")
                response['Content-Disposition'] = 'attachment; filename="mcf_spectra.zip"'
                response.write(open(zf_n, 'r').read())
            elif data_format_id == 4:  # massbank
                fn_counter = defaultdict(int)  # counts filename occurence for disambiguation
                zf_n = TemporaryFile('w+b', suffix='.zip', dir=settings.MEDIA_ROOT)
                with zipfile.ZipFile(zf_n, mode="w") as zf:
                    for spectrum, peak_list in spec_pairs:
                        if spectrum.standard:
                            ambiguous_fn = "Inventory_ID{}".format(spectrum.standard.inventory_id)
                        else:
                            ambiguous_fn = 'unknown_standard'
                        export_filename = "{}_{}.txt".format(ambiguous_fn, fn_counter[ambiguous_fn])
                        fn_counter[ambiguous_fn] += 1
                        t = loader.get_template('mcf_standards_browse/export_template_massbank.txt')
                        timestamp = time.localtime(time.time())
                        r = t.render({'spectrum': spectrum, 'peak_list': peak_list, 'num_peak': len(peak_list),
                                      'info': {'institute': settings.INSTITUTE_NAME, 'ion_mode':
                                               'POSITIVE' if spectrum.adduct.charge > 0 else 'NEGATIVE'}})
                        info = zipfile.ZipInfo(export_filename, date_time=timestamp)
                        info.compress_type = zipfile.ZIP_DEFLATED
                        info.comment = 'generated by curatr'
                        info.create_system = 0
                        zf.writestr(info, r.encode('utf-8'))
                zf_n.seek(0)
                response = FileResponse(zf_n, content_type="application/zip")
                response['Content-Disposition'] = 'attachment; filename="mcf_spectra.zip"'
            return response
    else:
        form = ExportLibrary()
    return render(request, 'mcf_standards_browse/export_library.html', {'form': form})


@login_required()
def molecule_cleandb(request):
    n_clean, clean_name = tools.clear_molecules_without_standard()
    logging.debug("{} molecules removed".format(n_clean))
    error_list = []
    for name in clean_name:
        error_list.append([name, 'removed'])
    logging.debug(error_list)
    return render(request, 'mcf_standards_browse/upload_error.html', {'error_list': error_list})


def library_stats(request):
    spectra = FragmentationSpectrum.objects
    molecules = Molecule.objects
    annotated_molecules = molecules.filter(moleculespectracount__spectra_count__gt=0)
    reviewed = spectra.filter(reviewed=1)
    accepted = reviewed.filter(standard_id__isnull=False)
    rejected = reviewed.filter(standard_id__isnull=True)
    tag_counts = [t.molecule_set.count() for t in MoleculeTag.objects.all()]
    total_accepted = accepted.count()
    total_rejected = rejected.count()
    total_spectra = spectra.count()
    total_reviewed = reviewed.count()
    total_annotated = annotated_molecules.count()
    total_molecules = molecules.count()
    total_taggings = sum(tag_counts)
    total_tagged = Molecule.objects.filter(tags__isnull=False).count()

    # maps number of annotations to how many molecules exists with that amount of annotations, excluding 0
    annotation_count_histo = Counter(
        [int(d['spectra_count']) for d in MoleculeSpectraCount.objects.filter(spectra_count__gt=0).values()])

    data = {
        "chart1": {
            'data': [total_accepted, total_rejected, total_spectra - total_reviewed],
            'labels': ['accepted', 'rejected', 'unreviewed'],
        },
        "chart2": {
            'data': annotation_count_histo.values(),
            'labels': annotation_count_histo.keys()
        },
        "chart3": {
            'data': tag_counts,
            'labels': [str(t) for t in MoleculeTag.objects.all()],
        },
        "total_spectra": total_spectra,
        "total_molecules": total_molecules,
        "total_annotated": total_annotated,
        "total_annotations": total_reviewed,
        "total_taggings": total_taggings,
        "total_tagged": total_tagged,
        "percent_spectra_curated": _percent(total_reviewed, total_spectra),
        "percent_molecules_annotated": _percent(total_annotated, total_molecules),
        "percent_molecules_tagged": _percent(total_tagged, total_molecules),
    }
    return render(request, 'mcf_standards_browse/mcf_library_stats.html', data)


def _percent(numerator, total_spectra, ndigits=2):
    return round((100.0 * numerator) / total_spectra, ndigits=ndigits)
