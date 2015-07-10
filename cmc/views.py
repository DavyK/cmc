from django.shortcuts import render_to_response, RequestContext
from django.http import HttpResponseRedirect
from viz.models import DataSource
# Create your views here.


def home(request):

    data_sources = DataSource.objects.all()

    data = {'data_sources': data_sources}
    return render_to_response('cmc/base.html', data, context_instance=RequestContext(request))

