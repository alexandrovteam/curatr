from django.shortcuts import render, redirect, get_object_or_404

from models import Standard, Adduct
from .forms import MCFStandardForm
# Create your views here.

def home_page(request):
    return render(request,'mcf_standards_browse/home_page.html',)

def StandardAdduct_detail(request,dataset_pk, standard_pk, adduct_pk):
    print 'standard - yo'
    print dataset_pk, standard_pk, adduct_pk
    return True

def Dataset_detail(request):
    print 'dataset detail - yo'
    return True

def Dataset_list(request):
    print 'dataset - yo'
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
