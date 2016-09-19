__author__ = 'palmer'
from django.conf.urls import url, include
from django.contrib.auth import views as auth_views

from . import views
from .views import SpectraListView

urlpatterns = [
    url(r'^$', views.home_page),
    url(r'^stats/$', views.library_stats, name='stats'),
    url(r'^adduct/add/$', views.adduct_add, name='adduct-add'),
    url(r'^inventory/$', views.standard_list, name='standard-list'),
    url(r'^inventory/add/$', views.standard_add, name='standard-add'),
    url(r'^inventory/add/batch/$', views.standard_add_batch, name='standard-add-batch'),
    url(r'^inventory/inventory(?P<mcfid>.+)/$', views.standard_detail, name='standard-detail'),
    url(r'^inventory/edit/inventory(?P<mcfid>.+)/$', views.standard_edit, name='standard-edit'),
    url(r'^molecule/edit/(?P<pk>.+)/$', views.molecule_edit, name='molecule-edit'),
    url(r'^molecule/add/$', views.molecule_add, name='molecule-add'),
    url(r'^molecule/cleandb/$', views.molecule_cleandb, name='molecule-cleandb'),
    url(r'^molecule/(?P<pk>.+)/$', views.molecule_detail, name='molecule-detail'),
    url(r'^molecule/$', views.molecule_list, name='molecule-list'),
    url(r'^moleculetag/add/$', views.MoleculetagAdd.as_view(), name='moleculetag-add'),
    url(r'^MS2/export/$', views.fragmentSpectrum_export, name='fragmentSpectrum-export'),
    url(r'^MS2/$', views.fragmentSpectrum_list, name='fragmentSpectrum-list'),
    url(r'^MS2/spec(?P<pk>.+)/$', views.fragmentSpectrum_detail, name='fragmentSpectrum-detail'),
    url(r'^upload/dataset/$', views.dataset_upload, name='dataset-upload'),
    url(r'^dataset/$', views.dataset_list, name='dataset-list'),
    url(r'^dataset/(?P<pk>.+)/$', views.dataset_detail, name='dataset-detail'),
    url(r'^xic/(?P<dataset_pk>.+)/inventory(?P<mcfid>.+)/M(?P<adduct_pk>.+)$', views.xic_detail,
        name='xic-detail'),
    url(r'^accounts/login/$', auth_views.login, name='login'),
    url(r'^accounts/logout/$', auth_views.logout, {'next_page': '/'}, name='logout'),
    url(r'^errors/batch_molecule_upload/', views.error_page, name="batch-upload-error"),
    url(r'^about/curatr/', views.about_curatr, name="about-curatr"),
    url(r'^about/', views.about, name="about"),
    url(r'^table/', include('table.urls')),
    url(r'^table_spectra/data/$', SpectraListView.as_view(), name='spectra_table'),
    url(r'^library/$', views.library_home, name='library-home'),
    url(r'^curate/$', views.curate_home, name='curate-home'),
    # url(r'^mol/mol(?P<pk>[0-9]+)/$', views.mol_detail, name='mol_detail'),
    # url(r'^sf/(?P<pk>[A-Z,0-9]+)/$', views.sf_detail, name='sf_detail'),
    # url(r'^ion/ion(?P<pk>[0-9]+)/$', views.ion_detail, name='ion_detail'),
    # url(r'^fragmentSpectrum/spec(?P<pk>[0-9]+)/$', views.fragmentSpectrum_detail, name='fragmentSpectrum_detail'),
    # url(r'^fragmentSpectrum/spec(?P<pk>[0-9]+)/edit/$', views.fragmentSpectrum_edit, name='fragmentSpectrum_edit'),
]


# http://stackoverflow.com/questions/17337843/how-to-implement-a-hierarchy-of-resources-eg-parents-id-children-in-django
