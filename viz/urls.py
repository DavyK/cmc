__author__ = 'davidkavanagh'
from django.conf.urls import patterns, include, url
from viz import views

urlpatterns = patterns(
    '',
    url(r'^search/$', views.search, name='search'),
    url(r'^gene/(?P<gene_id>\w+)/$', views.gene, name='gene'),
    url(r'^list/(?P<type>\w+)/$', views.list_page, name='list_page'),
    url(r'^list/modules/(?P<module>\w+)/$', views.list_module_genes, name='list_module_genes'),
    url(r'^eqtl/(?P<snp_id>\w+)/$', views.eqtl, name='eqtl'),
    url(r'^async_module_load/$', views.async_module_load, name='async_module_load'),
    url(r'^async_eqtl_load/$', views.async_eqtl_load, name='async_eqtl_load'),
    url(r'^network/$', views.network, name='network'),
)
