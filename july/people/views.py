from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.template.context import RequestContext
from google.appengine.ext import ndb

from gae_django.auth.models import User

from july.people.models import Commit

def user_profile(request, username):
    user = User.query(ndb.GenericProperty('username') == username).get()
    if user == None:
        raise Http404("User not found")

    commits = Commit.query(ancestor=user.key)

    return render_to_response('people/profile.html', 
        {"commits":commits, 'profile':user}, 
        RequestContext(request)) 
 
@login_required
def edit_profile(request, username, template_name='people/edit.html'):
    from forms import EditUserForm
    user = User.query(ndb.GenericProperty('username') == username).get()

    if user == None:
        raise Http404("User not found")
    
    if user.key != request.user.key:
        http403 = HttpResponse("This ain't you!")
        http403.status = 403
        return http403
    

    form = EditUserForm(request.POST or None, user=request.user)
    if form.is_valid():
        for key in form.cleaned_data:
            setattr(user, key, form.cleaned_data.get(key))
        user.put()
        return HttpResponseRedirect(
            reverse('member-profile', kwargs={'username':request.user.username})
        )
        
    

    return render_to_response(template_name, 
                              {'form':form}, 
                              RequestContext(request))
