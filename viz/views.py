from django.shortcuts import render_to_response, RequestContext
from django.http import HttpResponseRedirect
from django.db.models import Q, Count
from annoying.decorators import render_to
from viz.models import Gene, Isoform, ModuleGene, DgeResult, DieResult, DataSource, Eqtl, Pgc2SczSnp


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
            url = '/viz/gene/{0}'.format(gene.ensg_Id)
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

    m_gene = ModuleGene.objects.get(gene=gene)

    module_size = ModuleGene.objects.filter(parent_module=m_gene.parent_module).aggregate(mCount=Count('parent_module'))

    eqtl_count = Eqtl.objects.filter(gene=gene).filter(adj_p_val__in=['0.01 - 0.05','<0.01']).count()

    data.update({
        'gene': gene,
        'isoforms': isoforms,
        'dge': dge_results,
        'die': die_results,
        'm_gene': m_gene,
        'module_size': module_size,
        'eqtl_count': eqtl_count
    })

    return render_to_response('viz/show_gene.html', data, context_instance=RequestContext(request))


def list_page(request, type):
    data_sources = DataSource.objects.all()

    data = {'data_sources': data_sources}
    if type == 'dge':
        dge_results = DgeResult.objects.filter(adj_p_val__lte=0.05).select_related('gene').order_by('adj_p_val')
        data['dge_results'] = dge_results
        url = 'viz/dge_list.html'

    elif type == 'die':
        die_results = DieResult.objects.filter(adj_p_val__lte=0.05).select_related('isoform').select_related('isoform__parent_gene').order_by('adj_p_val')
        data['die_results'] = die_results
        url = 'viz/die_list.html'

    elif type == 'modules':
        modules = ModuleGene.objects.values('parent_module').annotate(mCount=Count('parent_module'))
        data['modules'] = modules
        url = 'viz/module_list.html'

    return render_to_response(url, data, context_instance=RequestContext(request))


def list_module_genes(request, module):

    data_sources = DataSource.objects.all()

    genes = ModuleGene.objects.filter(parent_module=module).select_related('gene')
    n_genes = ModuleGene.objects.filter(parent_module=module).count()

    data = {
        'data_sources':data_sources,
        'module_name':module,
        'genes': genes,
        'n_genes': n_genes
    }

    return render_to_response('viz/module_gene_list.html', data, context_instance=RequestContext(request))

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

    module_name = request.GET['module_name']
    module_genes = ModuleGene.objects.filter(parent_module=module_name).select_related('gene')

    return {'module_genes': module_genes}


@render_to('viz/eqtl_table.html')
def async_eqtl_load(request):

    gene_id = request.GET['gene_obj_id']
    eqtls = Eqtl.objects.filter(gene=gene_id).filter(adj_p_val__in=['0.01 - 0.05','<0.01']).select_related('snp').order_by('adj_p_val')
    return {'eqtls': eqtls}


