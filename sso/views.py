from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required

from sso.models import ServiceAccount

def index(request):
    pass

@login_required
def profile(request):

    user = request.user
    profile = request.user.get_profile()
    srvaccounts = ServiceAccounts.objects.get(user=request.user) 
    
    return render_to_response('sso/profile.html', locals())


def service_add(request):
    pass

def service_del(request):
    pass



