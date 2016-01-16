__author__ = 'palmer'

from django.conf.urls import include, url
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^$', views.home_page),
    url(r'^dataset/(?P<dataset_pk>.+)/MCF(?P<standard_pk>.+)/M(?P<adduct_pk>.+)$', views.StandardAdduct_detail, name='standard_addect_detail'),
    url(r'^dataset/(?P<pk>.+)/$', views.Dataset_detail, name='dataset-detail'),
    url(r'^dataset/$', views.Dataset_list, name='dataset-list'),
    url(r'^library/$', views.MCFStandard_list, name='MCFStandard-list'),
    url(r'^library/add/$', views.MCFStandard_add, name='MCFStandard-add'),

    #url(r'^mol/mol(?P<pk>[0-9]+)/$', views.mol_detail, name='mol_detail'),
    #url(r'^sf/(?P<pk>[A-Z,0-9]+)/$', views.sf_detail, name='sf_detail'),
    #url(r'^ion/ion(?P<pk>[0-9]+)/$', views.ion_detail, name='ion_detail'),
    #url(r'^fragmentSpectrum/spec(?P<pk>[0-9]+)/$', views.fragmentSpectrum_detail, name='fragmentSpectrum_detail'),
    #url(r'^fragmentSpectrum/spec(?P<pk>[0-9]+)/edit/$', views.fragmentSpectrum_edit, name='fragmentSpectrum_edit'),
]


#http://stackoverflow.com/questions/17337843/how-to-implement-a-hierarchy-of-resources-eg-parents-id-children-in-django