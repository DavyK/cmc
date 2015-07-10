from django.db import models

# Create your models here.


class DataSource(models.Model):
    cohort = models.CharField(max_length=50)
    tissue = models.CharField(max_length=50)
    sva = models.CharField(max_length=20, choices=[('Y', 'SVA'), ('N', 'NO_SVA')])
    description = models.TextField(max_length=3000)

    def __unicode__(self):
        if self.sva == 'Y':
            sva_choice='SVA'
        else:
            sva_choice='NO_SVA'
        return '{0}-{1}-{2}'.format(self.cohort, self.tissue, sva_choice)


class Gene(models.Model):
    ensg_Id = models.CharField(db_index=True, max_length=20, unique=True)
    chrom_name = models.CharField(max_length=5)
    start_bp = models.IntegerField()
    end_bp = models.IntegerField()
    symbol = models.CharField(db_index=True, max_length=20)
    strand = models.CharField(max_length=20, choices=[('+', 'sense'), ('-', 'antisense'), ('.', 'unknown')])

    def __unicode__(self):
        return '{0} ({1})'.format(self.ensg_Id, self.symbol)


class Isoform(models.Model):
    parent_gene = models.ForeignKey(Gene)

    enst_Id = models.CharField(max_length=20)
    iso_Id = models.CharField(max_length=200)

    chrom_name = models.CharField(max_length=5)
    start_bp = models.IntegerField()
    end_bp = models.IntegerField()
    total_length = models.IntegerField()


class DgeResult(models.Model):
    data_source = models.ForeignKey(DataSource)
    gene = models.ForeignKey(Gene)

    aveExpr = models.FloatField()
    t_statistic = models.FloatField()
    beta = models.FloatField()
    logFC = models.FloatField()
    ci_l = models.FloatField()
    ci_r = models.FloatField()
    p_val = models.FloatField()
    adj_p_val = models.FloatField()


class DieResult(models.Model):
    data_source = models.ForeignKey(DataSource)

    isoform = models.ForeignKey(Isoform)

    aveExpr = models.FloatField()
    t_statistic = models.FloatField()
    beta = models.FloatField()
    logFC = models.FloatField()
    ci_l = models.FloatField()
    ci_r = models.FloatField()
    p_val = models.FloatField()
    adj_p_val = models.FloatField()


class CoexppModule(models.Model):
    data_source = models.ForeignKey(DataSource)
    
    name = models.CharField(max_length=20)
    size = models.IntegerField()
    mean_expr = models.FloatField()


class ModuleGene(models.Model):
    data_source = models.ForeignKey(DataSource)
    
    gene = models.ForeignKey(Gene)
    parent_module = models.ForeignKey(CoexppModule)

    k_all = models.FloatField()
    k_in = models.FloatField()
    k_out = models.FloatField()
    k_diff = models.FloatField()
    k_in_normed = models.FloatField()
    k_all_normed = models.FloatField()

    to_all = models.FloatField()
    to_in = models.FloatField()
    to_out = models.FloatField()
    to_diff = models.FloatField()
    to_in_normed = models.FloatField()
    to_all_normed = models.FloatField()


class Pgc2SczSnp(models.Model):
    rs_Id = models.CharField(db_index=True, max_length=20)
    chrom_name = models.CharField(max_length=5)
    position = models.IntegerField()

    allele_a1 = models.CharField(max_length=3)
    allele_a2 = models.CharField(max_length=3)

    pgc_scz2_case_freq_a1 = models.FloatField()
    pgc_scz2_cont_freq_a1 = models.FloatField()

    scz_odd_ratio = models.FloatField()
    scz_p_val = models.FloatField()


class Eqtl(models.Model):
    data_source = models.ForeignKey(DataSource)

    snp = models.ForeignKey(Pgc2SczSnp)
    gene = models.ForeignKey(Gene)
    mode = models.CharField(max_length=20, choices=[('c', 'CIS'), ('t', 'TRANS')])

    beta = models.FloatField()
    p_val = models.FloatField()
    adj_p_val = models.FloatField()


