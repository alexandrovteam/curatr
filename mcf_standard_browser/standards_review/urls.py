__author__ = 'palmer'
from django.conf.urls import url, include
from django.contrib.auth import views as auth_views

from . import views
from .views import StandardListView

urlpatterns = [
    url(r'^$', views.home_page),
    url(r'^adduct/add/$', views.MCFAdduct_add, name='MCFAdduct-add'),
    url(r'^inventory/$', views.MCFStandard_list, name='MCFStandard-list'),
    url(r'^inventory/add/$', views.MCFStandard_add, name='MCFStandard-add'),
    url(r'^inventory/add/batch/$', views.MCFStandard_add_batch, name='MCFStandard-add-batch'),
    url(r'^inventory/MCF(?P<pk>.+)/$', views.MCFStandard_detail, name='MCFStandard-detail'),
    url(r'^inventory/edit/MCF(?P<pk>.+)/$', views.MCFStandard_edit, name='MCFStandard-edit'),
    url(r'^molecule/edit/(?P<pk>.+)/$', views.MCFMolecule_edit, name='MCFMolecule-edit'),
    url(r'^molecule/cleandb/$', views.MCFMolecule_cleandb, name='MCFMolecule-cleandb'),
    url(r'^molecule/(?P<pk>.+)/$', views.MCFMolecule_detail, name='MCFMolecule-detail'),
    url(r'^molecule/$', views.MCFMolecule_list, name='MCFMolecule-list'),
    url(r'^MS2/export/$', views.fragmentSpectrum_export, name='fragmentSpectrum-export'),
    url(r'^MS2/$', views.fragmentSpectrum_list, name='fragmentSpectrum-list'),
    url(r'^MS2/spec(?P<pk>.+)/$', views.fragmentSpectrum_detail, name='fragmentSpectrum-detail'),
    url(r'^upload/dataset/$', views.dataset_upload, name='dataset-upload'),
    url(r'^dataset/$', views.MCFdataset_list, name='MCFdataset-list'),
    url(r'^dataset/(?P<pk>.+)/$', views.MCFdataset_detail, name='MCFdataset-detail'),
    url(r'^xic/(?P<dataset_pk>.+)/MCF(?P<standard_pk>.+)/M(?P<adduct_pk>.+)$', views.MCFxic_detail,
        name='MCFxic-detail'),
    url(r'^accounts/login/$', auth_views.login, name='login'),
    url(r'^accounts/logout/$', auth_views.logout, {'next_page': '/'}),
    url(r'^errors/batch_molecule_upload/', views.error_page, name="batch-upload-error"),
    url(r'^about/', views.about, name="about"),
    url(r'^table/', include('table.urls')),
    url(r'^table_standard/data/$', StandardListView.as_view(), name='standard_table'),
    # url(r'^mol/mol(?P<pk>[0-9]+)/$', views.mol_detail, name='mol_detail'),
    # url(r'^sf/(?P<pk>[A-Z,0-9]+)/$', views.sf_detail, name='sf_detail'),
    # url(r'^ion/ion(?P<pk>[0-9]+)/$', views.ion_detail, name='ion_detail'),
    # url(r'^fragmentSpectrum/spec(?P<pk>[0-9]+)/$', views.fragmentSpectrum_detail, name='fragmentSpectrum_detail'),
    # url(r'^fragmentSpectrum/spec(?P<pk>[0-9]+)/edit/$', views.fragmentSpectrum_edit, name='fragmentSpectrum_edit'),
]


# http://stackoverflow.com/questions/17337843/how-to-implement-a-hierarchy-of-resources-eg-parents-id-children-in-django
