__author__ = 'palmer'

from django.conf.urls import include, url
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^$', views.home_page),
    #url(r'^mol/mol(?P<pk>[0-9]+)/$', views.mol_detail, name='mol_detail'),
    #url(r'^sf/(?P<pk>[A-Z,0-9]+)/$', views.sf_detail, name='sf_detail'),
    #url(r'^ion/ion(?P<pk>[0-9]+)/$', views.ion_detail, name='ion_detail'),
    #url(r'^fragmentSpectrum/spec(?P<pk>[0-9]+)/$', views.fragmentSpectrum_detail, name='fragmentSpectrum_detail'),
    #url(r'^fragmentSpectrum/spec(?P<pk>[0-9]+)/edit/$', views.fragmentSpectrum_edit, name='fragmentSpectrum_edit'),
]
