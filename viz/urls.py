__author__ = 'davidkavanagh'
from django.conf.urls import patterns, include, url
from viz import views

urlpatterns = patterns(
    '',
    url(r'^search/$', views.search, name='search'),
    url(r'^gene/(?P<gene_id>\d+)/$', views.gene, name='gene'),
    url(r'^dge/$', views.list_de_genes, name='list_de_genes'),
    url(r'^die/$', views.list_de_isos, name='list_de_isos'),
    url(r'^modules/$', views.list_modules, name='list_modules'),
    url(r'^eqtl/(?P<snp_id>\d+)/$', views.eqtl, name='eqtl'),
    url(r'^async_module_load/$', views.async_module_load, name='async_module_load'),
    url(r'^async_eqtl_load/$', views.async_eqtl_load, name='async_eqtl_load'),
    url(r'^network/$', views.network, name='network'),
)
