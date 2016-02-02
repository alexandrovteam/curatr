__author__ = 'palmer'
from django.conf.urls.static import static
from django.conf.urls import url
from . import views
from .views import MCFStandard_list_ez
urlpatterns = [
    url(r'^$', views.home_page),
    url(r'^library/$', views.MCFStandard_list, name='MCFStandard-list'),
    url(r'^library/add/$', views.MCFStandard_add, name='MCFStandard-add'),
    url(r'^library/add/batch/$', views.MCFStandard_add_batch, name='MCFStandard-add-batch'),
    url(r'^library/MCF(?P<pk>.+)/$', views.MCFStandard_detail, name='MCFStandard-detail'),
    url(r'^MS2/$', views.fragmentSpectrum_list, name='fragmentSpectrum-list'),
    url(r'^MS2/spec(?P<pk>.+)/$', views.fragmentSpectrum_detail, name='fragmentSpectrum-detail'),
    url(r'^upload/dataset/$', views.dataset_upload, name='dataset-upload'),
    url(r'^dataset/$', views.MCFdataset_list, name='MCFdataset-list'),
    url(r'^dataset/(?P<pk>.+)/$', views.MCFdataset_detail, name='MCFdataset-detail'),
    url(r'^xic/(?P<dataset_pk>.+)/MCF(?P<standard_pk>.+)/M(?P<adduct_pk>.+)$', views.MCFxic_detail, name='MCFxic-detail'),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),
    url(r'^about/', MCFStandard_list_ez.as_view(), name="MCFStandard_list_ez"),

    #url(r'^mol/mol(?P<pk>[0-9]+)/$', views.mol_detail, name='mol_detail'),
    #url(r'^sf/(?P<pk>[A-Z,0-9]+)/$', views.sf_detail, name='sf_detail'),
    #url(r'^ion/ion(?P<pk>[0-9]+)/$', views.ion_detail, name='ion_detail'),
    #url(r'^fragmentSpectrum/spec(?P<pk>[0-9]+)/$', views.fragmentSpectrum_detail, name='fragmentSpectrum_detail'),
    #url(r'^fragmentSpectrum/spec(?P<pk>[0-9]+)/edit/$', views.fragmentSpectrum_edit, name='fragmentSpectrum_edit'),
]


#http://stackoverflow.com/questions/17337843/how-to-implement-a-hierarchy-of-resources-eg-parents-id-children-in-django