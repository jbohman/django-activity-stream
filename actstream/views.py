from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from actstream.models import Follow, Action, user_stream, actor_stream, \
    model_stream, follow, unfollow

def respond(request, code):
    """
    Responds to the request with the given response code.
    If ``next`` is in the form, it will redirect instead
    """
    if 'next' in request.REQUEST:
        return HttpResponseRedirect(request.REQUEST['next'])
    return type('Response%d' % code, (HttpResponse,), {'status_code': code})()

@login_required
def follow_unfollow(request, content_type_id, object_id, do_follow=True):
    """
    Creates or deletes the follow relationship between ``request.user`` and the actor defined by ``content_type_id``, ``object_id``
    """
    if request.method == 'POST':
        ctype = get_object_or_404(ContentType, pk=content_type_id)
        actor = get_object_or_404(ctype.model_class(), pk=object_id)
            
        if do_follow:
            follow(request.user, actor)
            return respond(request, 201) # CREATED
        unfollow(request.user, actor)
        return respond(request, 204) # NO CONTENT

    response = HttpResponse()
    response['Allow'] = 'POST'
    response.status_code = 405 # Method not allowed
    return response
    
@login_required
def stream(request):
    """
    Index page for authenticated user's activity stream. (Eg: Your feed at github.com)
    """
    return render_to_response('activity/actor.html', {
        'ctype': ContentType.objects.get_for_model(request.user),
        'actor':request.user,'action_list':user_stream(request.user)
    }, context_instance=RequestContext(request))
    
def followers(request, content_type_id, object_id):
    """
    Creates a listing of ``User``s that follow the actor defined by ``content_type_id``, ``object_id``
    """
    ctype = get_object_or_404(ContentType, pk=content_type_id)
    follows = Follow.objects.filter(content_type=ctype, object_id=object_id)
    actor = get_object_or_404(ctype.model_class(), pk=object_id)
    return render_to_response('activity/followers.html', {
        'followers': (f.user for f in follows), 'actor':actor
    }, context_instance=RequestContext(request))
    
def user(request, username):
    """
    ``User`` focused activity stream. (Eg: Profile page twitter.com/justquick)
    """
    user = get_object_or_404(User, username=username, is_active=True)
    return render_to_response('activity/actor.html', {
        'ctype': ContentType.objects.get_for_model(User),
        'actor':user,'action_list':actor_stream(user)
    }, context_instance=RequestContext(request))
    
def detail(request, action_id):
    """
    ``Action`` detail view (pretty boring, mainly used for get_absolute_url)
    """
    return render_to_response('activity/detail.html', {
        'action': get_object_or_404(Action, pk=action_id)
    }, context_instance=RequestContext(request))
    
def actor(request, content_type_id, object_id):
    """
    ``Actor`` focused activity stream for actor defined by ``content_type_id``, ``object_id``
    """
    ctype = get_object_or_404(ContentType, pk=content_type_id)
    actor = get_object_or_404(ctype.model_class(), pk=object_id)    
    return render_to_response('activity/actor.html', {
        'action_list': actor_stream(actor), 'actor':actor,'ctype':ctype
    }, context_instance=RequestContext(request))
    
def model(request, content_type_id):
    """
    ``Actor`` focused activity stream for actor defined by ``content_type_id``, ``object_id``
    """
    ctype = get_object_or_404(ContentType, pk=content_type_id)
    actor = ctype.model_class()
    return render_to_response('activity/actor.html', {
        'action_list': model_stream(actor),'ctype':ctype,'actor':ctype#._meta.verbose_name_plural.title()
    }, context_instance=RequestContext(request)) 
