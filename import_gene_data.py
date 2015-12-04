__author__ = 'davidkavanagh'
import sys
import synapseclient
import gc
import django
from django.db import transaction, reset_queries
from viz.models import DataSource, Gene, Isoform, ModuleGene, DgeResult, DieResult, Pgc2SczSnp, Eqtl

syn = synapseclient.Synapse()
syn.login('DavyK_mssm', 'blue3cheese6_@_syn', rememberMe=True)


INSERT_CHUNK_SIZE = 999

ENSG_2_HGNC_MAP = {}


def bin_beta(value):
    if value < 0:
        return 'down'
    elif value > 0:
        return 'up'
    else:
        return 'no change'


def bin_pval(value):
    if value <=1 and value > 0.1:
        return '0.1 - 1'
    elif value <= 0.1 and value > 0.05:
        return '0.05 - 0.1'
    elif value <= 0.05 and value > 0.01:
        return '0.01 - 0.05'
    else:
        return '<0.01'


def list_chunker(l, n):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


def get_synapse_file_path(syn_id):
    entity = syn.get(syn_id)
    return entity.path


def add_data_source(file_name):
    '''
    Data source file should be
    <Cohort> i.e "CMC(Mssm/Penn/Pitt)"
    <TISSUE_TYPE> i.e. 'DLPFC'
    SVA [Y/N]
    Single-line description (no more than 3,000 characters)
    '''

    data_source_file = open(file_name, 'r')

    cohort_string = data_source_file.next().rstrip()

    tissue_type = data_source_file.next().rstrip()

    sva_choice = data_source_file.next().rstrip()

    description = data_source_file.next().rstrip()

    ds = DataSource(cohort=cohort_string, tissue=tissue_type, sva=sva_choice, description=description)
    ds.save()

    global DATA_SOURCE
    DATA_SOURCE = ds


def make_map(syn_id):
    map_file_name = get_synapse_file_path(syn_id)
    map_file = open(map_file_name, 'r')
    map_file.next() # skip header

    id_to_symbol = {}

    for line in map_file:
        fields = line.rstrip().rsplit()
        gene_id = fields[0]
        gene_symbol = fields[1]

        id_to_symbol[gene_id] = gene_symbol

    map_file.close()

    return id_to_symbol


def process_gene_file(syn_id):
    file_name = get_synapse_file_path(syn_id)
    gene_file = open(file_name, 'r')
    gene_file.next() # skip header

    genes = {}

    sys.stdout.write('reading gene file\n\n')
    sys.stdout.flush()
    for line in gene_file:
        fields = line.rstrip().rsplit()
        ens_t_ID, chrom, strand, start_bp, end_bp, ens_g_ID = fields[1], fields[2], fields[3], fields[4], fields[5], fields[12]

        try:
            g = genes[ens_g_ID]
        
        except KeyError:
            genes[ens_g_ID] = {'chrom': chrom, 'strand': strand, 'start_bp': start_bp, 'end_bp': end_bp, 'symbol': ENSG_2_HGNC_MAP[ens_g_ID]}
            g = genes[ens_g_ID]
        
        if strand == '+' or strand == '.':
            if start_bp < g['start_bp']:
                g['start_bp'] = start_bp

            if end_bp > g['end_bp']:
                g['end_bp'] = end_bp
        else:
            if start_bp > g['start_bp']:
                g['start_bp'] = start_bp

            if end_bp < g['end_bp']:
                g['end_bp'] = end_bp

    gene_objects = []

    sys.stdout.write('inserting genes into database\n\n')
    sys.stdout.flush()
    for g, d in genes.iteritems():
        gene_objects.append(Gene(ensg_Id=g, chrom_name=d['chrom'], start_bp=int(d['start_bp']), end_bp=int(d['end_bp']), strand=d['strand'], symbol=d['symbol']))


    Gene.objects.bulk_create(gene_objects)


def process_isoform_file(syn_id):

    all_genes = Gene.objects.all()

    db_genes = {g.ensg_Id: g for g in all_genes}

    sys.stdout.write('reading isoform file\n\n')
    sys.stdout.flush()

    file_name = get_synapse_file_path(syn_id)
    metainfo_file = open(file_name, 'r')
    header = metainfo_file.next().rstrip().rsplit()

    metainfo = {}

    for line in metainfo_file:
        fields = line.rstrip().rsplit()

        transcriptID = fields[0]

        data = dict(zip(header, fields))

        data['START'] = int(data['START'])
        data['END'] = int(data['END'])
        data['ISO_LEN'] = int(data['ISO_LEN'])

        metainfo[transcriptID] = data

    metainfo_file.close()

    sys.stdout.write('inserting isoforms into database\n\n')
    sys.stdout.flush()
    iso_objects = []
    for iso, d in metainfo.iteritems():
        iso_objects.append(
            Isoform(
                parent_gene=db_genes[d['GENE']],
                enst_Id=iso,
                iso_Id=d['isoformID'],
                chrom_name=d['CHROM'],
                start_bp=d['START'],
                end_bp=d['END'],
                total_length=d['ISO_LEN']
                )
            )

    Isoform.objects.bulk_create(iso_objects)

"""
def process_module_file(file_name):

    sys.stdout.write('reading module file\n\n')
    sys.stdout.flush()
    module_file = open(file_name, 'r')
    module_file.next() # skip header

    modules = {}

    for line in module_file:
        fields = line.rstrip().rsplit()

        module_name, size, aveExpr = fields[0], int(fields[1]), float(fields[2])

        modules[module_name] = {'size': size, 'aveExpr': aveExpr}

    sys.stdout.write('inserting modules into database\n\n')
    sys.stdout.flush()
    module_objects = []
    for m, d in modules.iteritems():
        module_objects.append(
            CoexppModule(
                data_source=DATA_SOURCE,
                name=m,
                size=d['size'],
                mean_expr=d['aveExpr']
            )
        )
    CoexppModule.objects.bulk_create(module_objects)
"""

def process_gene_module_file(syn_id):

    all_genes = Gene.objects.all()
    db_genes = {g.ensg_Id: g for g in all_genes}

    #all_modules = CoexppModule.objects.all()
    #db_modules = {m.name: m for m in all_modules}

    sys.stdout.write('reading module gene file\n\n')
    sys.stdout.flush()

    file_name = get_synapse_file_path(syn_id)
    module_file = open(file_name, 'r')
    header = module_file.next().rstrip().rsplit()

    module_genes = {}

    for line in module_file:
        fields = line.rstrip().rsplit()

        data = dict(zip(header, fields))

        module_genes[data['Gene']] = data

    sys.stdout.write('inserting module genes into database\n\n')
    sys.stdout.flush()
    module_gene_objects = []
    for g, d in module_genes.iteritems():

        this_gene = g
        module_gene_objects.append(
            ModuleGene(
                data_source=DATA_SOURCE,
                gene=db_genes[g],
                parent_module=d['Module'],
                k_all=d['k.all'],
                k_in=d['k.in'],
                k_out=d['k.out'],
                k_diff=d['k.diff'],
                k_in_normed=d['k.in.normed'],
                k_all_normed=d['k.all.normed'],

                to_all=d['to.all'],
                to_in=d['to.in'],
                to_out=d['to.out'],
                to_diff=d['to.diff'],
                to_in_normed=d['to.in.normed'],
                to_all_normed=d['to.all.normed']
            )
        )

    ModuleGene.objects.bulk_create(module_gene_objects)


def process_dge_results_file(syn_id):

    all_genes = Gene.objects.all()
    db_genes = {g.ensg_Id: g for g in all_genes}

    sys.stdout.write('reading DGE results file\n\n')
    sys.stdout.flush()

    file_name = get_synapse_file_path(syn_id)
    dge_file = open(file_name, 'r')

    header = dge_file.next().rstrip().rsplit()

    dge = {}
    for line in dge_file:
        fields = line.rstrip().rsplit()
        data = dict(zip(header, fields))

        dge[data['genes']] = data

    sys.stdout.write('inserting DGE results into database\n\n')
    sys.stdout.flush()
    dge_objects = []
    
    for g, d in dge.iteritems():
        dge_objects.append(
            DgeResult(
                data_source=DATA_SOURCE,
                gene=db_genes[g],
                aveExpr=d['AveExpr'],
                t_statistic=d['t'],
                beta=d['B'],
                logFC=d['logFC'],
                ci_l=d['CI.L'],
                ci_r=d['CI.R'],
                p_val=d['P.Value'],
                adj_p_val=d['adj.P.Val']
            )
        )

    DgeResult.objects.bulk_create(dge_objects)


def process_die_results_file(syn_id):

    all_isoforms = Isoform.objects.all()
    db_isos = {i.enst_Id: i for i in all_isoforms}

    sys.stdout.write('reading DIE results file\n\n')
    sys.stdout.flush()

    file_name = get_synapse_file_path(syn_id)
    die_file = open(file_name, 'r')

    header = die_file.next().rstrip().rsplit()

    die = {}
    for line in die_file:
        fields = line.rstrip().rsplit()
        data = dict(zip(header, fields))

        die[data['isoforms']] = data

    die_objects = []

    sys.stdout.write('inserting DIE results into database\n\n')
    sys.stdout.flush()
    for i, d in die.iteritems():
        die_objects.append(
            DieResult(
                data_source=DATA_SOURCE,
                isoform=db_isos[i],
                aveExpr=d['AveExpr'],
                t_statistic=d['t'],
                beta=d['B'],
                logFC=d['logFC'],
                ci_l=d['CI.L'],
                ci_r=d['CI.R'],
                p_val=d['P.Value'],
                adj_p_val=d['adj.P.Val']
            )
        )

    DieResult.objects.bulk_create(die_objects)


def process_eqtls_file(file_name):
    """
        reads each line of the eqtl results file, splitting out the SNP data from the eqtl data.
        Insert all snps to the DB
        The insert all eqtls as the eqtl references SNP id.
        Probably a better way to do this.

    :param file_name: path of file with eqtl results

    :return:
    """
    eqtl_file = open(file_name)

    header = eqtl_file.next().rstrip().rsplit()
    
    all_genes = Gene.objects.all()
    db_genes = {g.ensg_Id: g for g in all_genes}

    count = 0
    snps_already_seen = set()
    pgc_snps_to_insert = []
    for line in eqtl_file:
        fields = line.rstrip().rsplit()
        data = dict(zip(header, fields))

        if data['SNP'] not in snps_already_seen:
            pgc_snp = Pgc2SczSnp(
                rs_Id=data['SNP'],
                chrom_name=data['SNP_CHR'],
                position=data['SNP_POS'],
                allele_a1=data['A1'],
                allele_a2=data['A2'],
                pgc_scz2_case_freq_a1=data['PGC_SCZ2_CASE_FREQ_A1'],
                pgc_scz2_cont_freq_a1=data['PGC_SCZ2_CONTROL_FREQ_A1'],
                scz_odd_ratio=data['SCZ_ODDS_RATIO'],
                scz_p_val=data['SCZ_P'],
            )
            pgc_snps_to_insert.append(pgc_snp)
            snps_already_seen.add(data['SNP'])

        if len(pgc_snps_to_insert) == INSERT_CHUNK_SIZE:
            Pgc2SczSnp.objects.bulk_create(pgc_snps_to_insert)
            count += len(pgc_snps_to_insert)
            del pgc_snps_to_insert[:]
            sys.stdout.write('\r processed {0} PGC SNPs'.format(count))
            sys.stdout.flush()

    if len(pgc_snps_to_insert) > 0:
        Pgc2SczSnp.objects.bulk_create(pgc_snps_to_insert)
        count += len(pgc_snps_to_insert)
        del pgc_snps_to_insert[:]
        sys.stdout.write('\r processed {0} PGC SNPs'.format(count))
        sys.stdout.flush()


    print len(snps_already_seen)
    print "\nInserted {0} PGC SNPs into the database\n".format(count)


    all_snps = Pgc2SczSnp.objects.all()
    db_snps = {s.rs_Id: s for s in all_snps}

    print 'Matching Eqtls agains {0} snps'.format(len(db_snps))

    count = 0
    eqtl_file.seek(0) # return pointer to begining of file
    eqtl_file.next() # skip header
    eqtls_to_insert = []
    for line in eqtl_file:
        fields = line.rstrip().rsplit()
        data = dict(zip(header, fields))

        b = bin_beta(float(data['eQTL_BETA']))
        p = bin_pval(float(data['eQTL_P']))
        adj_p = bin_pval(float(data['eQTL_FDR']))

        eqtls_to_insert.append(
            Eqtl(
                data_source=DATA_SOURCE,
                snp=db_snps[data['SNP']],
                gene=db_genes[data['GENE']],
                mode='CIS',
                beta=b,
                p_val=p,
                adj_p_val=adj_p,
            )
        )

        if len(eqtls_to_insert) == INSERT_CHUNK_SIZE:
            Eqtl.objects.bulk_create(eqtls_to_insert)
            count += len(eqtls_to_insert)
            del eqtls_to_insert[:]
            sys.stdout.write('\r processed {0} eQTLs'.format(count))
            sys.stdout.flush()

    if len(eqtls_to_insert) > 0:
        Eqtl.objects.bulk_create(eqtls_to_insert)
        count += len(eqtls_to_insert)
        del eqtls_to_insert[:]
        sys.stdout.write('\r processed {0} eQTLs'.format(count))
        sys.stdout.flush()

    print "\nInserted {0} eqtls into the database\n".format(count)

if __name__== '__main__':

    django.setup()

    args_file = open(sys.argv[1], 'r')
    args = {}
    # A file detailing the full paths of the data, for each of the data types. (genes, dde results, eqtls, etc)
    for line in args_file:
        fields = line.rstrip().rsplit(": ")
        name, value = fields[0], fields[1]
        sys.stdout.write('{0}:{1}'.format(name, value))
        sys.stdout.flush()
        args[name] = value

    add_data_source(args['data_source'])

    global ENSG_2_HGNC_MAP

    sys.stdout.write('reading gene symbol map\n\n')
    sys.stdout.flush()
    ENSG_2_HGNC_MAP = make_map(args['gene_symbol_map'])


    process_gene_file(args['genes'])

    process_isoform_file(args['isoforms'])

    #process_module_file(args['modules'])

    process_gene_module_file(args['module_genes'])

    process_dge_results_file(args['dge_results'])

    process_die_results_file(args['die_results'])

    process_eqtls_file(args['eqtls'])

    print "Finished!!!"




