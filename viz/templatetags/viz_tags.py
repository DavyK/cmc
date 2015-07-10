__author__ = 'davidkavanagh'
import django
from django import template


register = template.Library()



def bin_pval(value):
    if value <= 0.1 and value > 0.05:
        return '0.05 - 0.1'
    elif value <= 0.05 and value > 0.01:
        return '0.01 - 0.05'
    else:
        return '<0.01'

def beta_dir(value):
    if value < 0:
        return 'down'
    elif value > 0:
        return 'up'
    else:
        return 'no change'


register.filter('bin_pval', bin_pval)
register.filter('beta_dir', beta_dir)