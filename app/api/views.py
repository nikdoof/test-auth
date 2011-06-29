from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from piston import forms
from piston.models import Token

def oauth_callback_view(request, other):
    return HttpResponse("The application you allowed access to didn't request a callback, thats odd and should be fixed")


@login_required
def oauth_auth_view(request, token, callback, params):
    form = forms.OAuthAuthenticationForm(initial={
        'oauth_token': token.key,
        'oauth_callback': token.get_callback_url() or callback,
      })

    return render_to_response('piston/authorize_token.html',
            { 'form': form, 'consumer': token.consumer, 'user': token.user, 'request': request }, context_instance=RequestContext(request))


@login_required
def oauth_list_tokens(request):
    # List all Access tokens
    tokens = Token.objects.filter(token_type=Token.ACCESS)
    return render_to_response('api/view_tokens.html', { 'tokens': tokens, 'request': request }, context_instance=RequestContext(request))


@login_required
def oauth_revoke_token(request, key):
    token = get_object_or_404(Token, key=key)
    if token.user == request.user:
        token.delete()
        messages.success(request, "Access for %s has been revoked" % token.consumer.name, fail_silently=True)

    return redirect(oauth_list_tokens)    
