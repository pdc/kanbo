# Create your views here.

from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response

def home(request):
    template_name = 'about/home.html'
    template_vars = {}
    return render_to_response(template_name, template_vars, 
        context_instance=RequestContext(request))