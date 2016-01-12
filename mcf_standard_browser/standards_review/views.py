from django.shortcuts import render

# Create your views here.

def home_page(request):
    return render(request,'mcf_standards_browse/home_page.html',)
