from django.shortcuts import render_to_response, RequestContext
from django.http import HttpResponseRedirect
from django.db.models import Q
from annoying.decorators import render_to
# Create your views here.
from viz.models import Gene, Isoform, ModuleGene, CoexppModule, DgeResult, DieResult, DataSource, Eqtl, Pgc2SczSnp


def search(request):
    data_sources = DataSource.objects.all()

    data = {'data_sources': data_sources}
    if request.method == 'POST':

        search_term = request.POST['search_term']
        search_results = Gene.objects.filter(Q(ensg_Id=search_term) | Q(symbol=search_term))

        if len(search_results) > 1:
            data['search_results'] = search_results
            return render_to_response('viz/list_search_results.html', data, context_instance=RequestContext(request))

        elif len(search_results) == 0:
            return render_to_response('viz/show_gene.html', data, context_instance=RequestContext(request))

        else:
            gene = search_results[0]
            url = '/viz/gene/{0}'.format(gene.id)
            return HttpResponseRedirect(url)
    else:
        return render_to_response('viz/show_gene.html', data, context_instance=RequestContext(request))


def gene(request, gene_id):

    data_sources = DataSource.objects.all()

    data = {'data_sources': data_sources}

    gene = Gene.objects.get(pk=gene_id)

    isoforms = Isoform.objects.filter(parent_gene=gene)

    dge_results = DgeResult.objects.filter(gene=gene)[0]
    die_results = DieResult.objects.filter(isoform__in=isoforms)

    module = ModuleGene.objects.select_related('parent_module').filter(gene=gene)[0]

    eqtl_count = Eqtl.objects.filter(gene=gene).filter(adj_p_val__lte=0.05).count()

    data.update({
        'gene': gene,
        'isoforms': isoforms,
        'dge': dge_results,
        'die': die_results,
        'module': module,
        'eqtl_count': eqtl_count
    })

    return render_to_response('viz/show_gene.html', data, context_instance=RequestContext(request))


def list_de_genes(request):

    data_sources = DataSource.objects.all()

    data = {'data_sources': data_sources}

    dge_results = DgeResult.objects.filter(adj_p_val__lte=0.05).select_related('gene').order_by('adj_p_val')

    data['dge_results'] = dge_results

    return render_to_response('viz/dge_list.html', data, context_instance=RequestContext(request))


def list_de_isos(request):

    data_sources = DataSource.objects.all()

    data = {'data_sources': data_sources}

    die_results = DieResult.objects.filter(adj_p_val__lte=0.05).select_related('isoform').select_related('isoform__parent_gene').order_by('adj_p_val')

    data['die_results'] = die_results

    return render_to_response('viz/die_list.html', data, context_instance=RequestContext(request))


def list_modules(request):

    data_sources = DataSource.objects.all()

    data = {'data_sources': data_sources}

    modules = CoexppModule.objects.all()

    data['modules'] = modules

    return render_to_response('viz/module_list.html', data, context_instance=RequestContext(request))



def eqtl(request, snp_id):

    data_sources = DataSource.objects.all()

    egenes = Eqtl.objects.filter(snp__pk=snp_id).select_related('snp').select_related('gene')
    eqtl = egenes[0]

    data = {
        'data_sources': data_sources,
        'eqtl': eqtl,
        'egenes': egenes
    }

    return render_to_response('viz/eqtl_egenes.html', data, context_instance=RequestContext(request))


def network(request):

    data = {
    }

    return render_to_response('viz/show_network.html', data, context_instance=RequestContext(request))


@render_to('viz/module_table.html')
def async_module_load(request):

    module_id = request.GET['module_obj_id']
    print module_id
    module_genes = ModuleGene.objects.filter(parent_module__id=module_id).select_related('gene')

    return {'module_genes': module_genes}

@render_to('viz/eqtl_table.html')
def async_eqtl_load(request):

    gene_id = request.GET['gene_obj_id']
    eqtls = Eqtl.objects.filter(gene=gene_id).filter(adj_p_val__lte=0.05).select_related('snp').order_by('adj_p_val')
    print len(eqtls)
    return {'eqtls': eqtls}


