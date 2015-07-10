__author__ = 'davidkavanagh'
import sys
from  datetime import datetime
from django.db import transaction
from viz.models import DataSource, Gene, Isoform, CoexppModule, ModuleGene, DgeResult, DieResult, Pgc2SczSnp, Eqtl


INSERT_CHUNK_SIZE = 999

ENSG_2_HGNC_MAP = {}


def list_chunker(l, n):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


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


def make_map(map_file_name):

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


def process_gene_file(file_name):

    gene_file = open(file_name, 'r')
    gene_file.next() # skip header

    genes = {}

    print 'reading gene file\n\n'
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

    print 'inserting genes into database\n\n'
    for g, d in genes.iteritems():
        gene_objects.append(Gene(ensg_Id=g, chrom_name=d['chrom'], start_bp=int(d['start_bp']), end_bp=int(d['end_bp']), strand=d['strand'], symbol=d['symbol']))


    Gene.objects.bulk_create(gene_objects)


def process_isoform_file(file_name):

    all_genes = Gene.objects.all()

    db_genes = {g.ensg_Id: g for g in all_genes}

    print 'reading isoform file\n\n'
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

    print 'inserting isoforms into database\n\n'
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


def process_module_file(file_name):

    print 'reading module file\n\n'
    module_file = open(file_name, 'r')
    module_file.next() # skip header

    modules = {}

    for line in module_file:
        fields = line.rstrip().rsplit()

        module_name, size, aveExpr = fields[0], int(fields[1]), float(fields[2])

        modules[module_name] = {'size': size, 'aveExpr': aveExpr}

    print 'inserting modules into database\n\n'
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


def process_gene_module_file(file_name):

    all_genes = Gene.objects.all()
    db_genes = {g.ensg_Id: g for g in all_genes}

    all_modules = CoexppModule.objects.all()
    db_modules = {m.name: m for m in all_modules}

    print 'reading module gene file\n\n'
    module_file = open(file_name, 'r')
    header = module_file.next().rstrip().rsplit()

    module_genes = {}

    for line in module_file:
        fields = line.rstrip().rsplit()

        data = dict(zip(header, fields))

        module_genes[data['Gene']] = data

    print 'inserting module genes into database\n\n'
    module_gene_objects = []
    for g, d in module_genes.iteritems():

        this_gene = g
        module_gene_objects.append(
            ModuleGene(
                data_source=DATA_SOURCE,
                gene=db_genes[g],
                parent_module=db_modules[d['Module']],
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


def process_dge_results_file(file_name):

    all_genes = Gene.objects.all()
    db_genes = {g.ensg_Id: g for g in all_genes}

    print 'reading DGE results file\n\n'
    dge_file = open(file_name, 'r')

    header = dge_file.next().rstrip().rsplit()

    dge = {}
    for line in dge_file:
        fields = line.rstrip().rsplit()
        data = dict(zip(header, fields))

        dge[data['genes']] = data

    print 'inserting DGE results into database\n\n'
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


def process_die_results_file(file_name):

    all_isoforms = Isoform.objects.all()
    db_isos = {i.enst_Id: i for i in all_isoforms}

    print 'reading DIE results file\n\n'
    die_file = open(file_name, 'r')

    header = die_file.next().rstrip().rsplit()

    die = {}
    for line in die_file:
        fields = line.rstrip().rsplit()
        data = dict(zip(header, fields))

        die[data['isoforms']] = data

    die_objects = []

    print 'inserting DIE results into database\n\n'
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

    eqtl_file = open(file_name)

    header = eqtl_file.next().rstrip().rsplit()

    pgc_scz2_snps = {}

    eqtls = {}

    count = 0
    for line in eqtl_file:
        fields = line.rstrip().rsplit()

        data = dict(zip(header, fields))
        if data['SNP'] != 'SNP':
            try:
                pgc_scz2_snps[data['SNP']]
            except KeyError:
                pgc_scz2_snps[data['SNP']] = {
                    'SNP_CHR': data['SNP_CHR'],
                    'SNP_POS': data['SNP_POS'],
                    'A1': data['A1'],
                    'A2': data['A2'],
                    'PGC_SCZ2_CASE_FREQ_A1': data['PGC_SCZ2_CASE_FREQ_A1'],
                    'PGC_SCZ2_CONTROL_FREQ_A1': data['PGC_SCZ2_CONTROL_FREQ_A1'],
                    'SCZ_ODDS_RATIO': data['SCZ_ODDS_RATIO'],
                    'SCZ_P': data['SCZ_P']
                    }
            snp_gene = '{0}x{1}'.format(data['SNP'], data['GENE'])

            try:
                eqtls[snp_gene]

            except KeyError:
                eqtls[snp_gene] = {
                    'SNP': data['SNP'],
                    'GENE': data['GENE'],
                    'MODE': 'cis',
                    'BETA': data['eQTL_BETA'],
                    'eQTL_P': data['eQTL_P'],
                    'eQTL_FDR': data['eQTL_FDR']
                }

            count += 1
            if count % 100000 == 0:
                print 'read {0} eQTLs'.format(count)


    snp_objects = []
    for rsId, d in pgc_scz2_snps.iteritems():

        snp_objects.append(
            Pgc2SczSnp(
                rs_Id=rsId,
                chrom_name=d['SNP_CHR'],
                position=d['SNP_POS'],
                allele_a1=d['A1'],
                allele_a2=d['A2'],
                pgc_scz2_case_freq_a1=d['PGC_SCZ2_CASE_FREQ_A1'],
                pgc_scz2_cont_freq_a1=d['PGC_SCZ2_CONTROL_FREQ_A1'],
                scz_odd_ratio=d['SCZ_ODDS_RATIO'],
                scz_p_val=d['SCZ_P'],
            )
        )

    print '\ninserting {0} PGC2 snps into database\n'.format(len(pgc_scz2_snps))
    snp_object_chunks = list_chunker(snp_objects, INSERT_CHUNK_SIZE)
    count = 0
    with transaction.atomic():
        for l in snp_object_chunks:
            Pgc2SczSnp.objects.bulk_create(l)
            count += INSERT_CHUNK_SIZE
            sys.stdout.write('\r  processed {0} records'.format(count))
            sys.stdout.flush()

    all_genes = Gene.objects.all()
    db_genes = {g.ensg_Id: g for g in all_genes}

    all_snps = Pgc2SczSnp.objects.all()
    db_snps = {snp.rs_Id: snp for snp in all_snps}

    print '\ninserting {0} eqtls in the database\n'.format(len(eqtls))
    eqtl_objects = []
    for snp_gene, d in eqtls.iteritems():
        eqtl_objects.append(
            Eqtl(
                data_source=DATA_SOURCE,
                snp=db_snps[d['SNP']],
                gene=db_genes[d['GENE']],
                mode=d['MODE'],
                beta=d['BETA'],
                p_val=d['eQTL_P'],
                adj_p_val=d['eQTL_FDR'],
            )
        )

    eqtl_object_chunks = list_chunker(eqtl_objects, INSERT_CHUNK_SIZE)
    count = 0

    with transaction.atomic():
        for l in eqtl_object_chunks:
            Eqtl.objects.bulk_create(l)
            count += INSERT_CHUNK_SIZE
            sys.stdout.write('\r  processed {0} records'.format(count))
            sys.stdout.flush()



if __name__== '__main__':

    args_file = open(sys.argv[1], 'r')
    args = {}
    for line in args_file:
        fields = line.rstrip().rsplit(": ")
        name, value = fields[0], fields[1]
        print '{0}:{1}'.format(name, value)
        args[name] = value

    add_data_source(args['data_source'])

    global ENSG_2_HGNC_MAP

    print 'reading gene symbol map\n\n'
    ENSG_2_HGNC_MAP = make_map(args['gene_symbol_map'])

    process_gene_file(args['genes'])

    process_isoform_file(args['isoforms'])

    process_module_file(args['modules'])

    process_gene_module_file(args['module_genes'])

    process_dge_results_file(args['dge_results'])

    process_die_results_file(args['die_results'])

    process_eqtls_file(args['eqtls'])




