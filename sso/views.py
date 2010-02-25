from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from eve_api.models.api_player import EVEAccount
from sso.models import ServiceAccount, SSOUser

def index(request):
    pass

@login_required
def profile(request):

    user = request.user
    try:
        profile = request.user.get_profile()
    except SSOUser.DoesNotExist:
        profile = SSOUser(user=request.user)
        profile.save()

    try:
        srvaccounts = ServiceAccount.objects.get(user=request.user)
    except ServiceAccount.DoesNotExist:
        srvaccounts = None
    
    try:
        eveaccounts = EVEAccount.objects.get(user=request.user)
    except EVEAccount.DoesNotExist:
        eveaccounts = None

    return render_to_response('profile.html', locals())


def service_add(request):
    pass

def service_del(request):
    pass



