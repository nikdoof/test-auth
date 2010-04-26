from django.http import HttpResponse

def oauth_callback(request, other):
    return HttpResponse('Fake callback view.')
