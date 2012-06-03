from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.template.context import RequestContext
#from google.appengine.ext import db
from july.people.models import Commit
from gae_django.auth.models import User
from django.http import Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse

def user_profile(request, username):
    user = User.all().filter("username", username).get()
    if user == None:
        raise Http404("User not found")

    commits = Commit.all().ancestor(request.user.key())

    return render_to_response('people/profile.html', 
        {"commits":commits}, 
        RequestContext(request)) 
 
@login_required
def edit_profile(request, username, template_name='people/edit.html'):
    from forms import EditUserForm
    user = request.user

    #CONSIDER FILES with no POST?  Can that happen?
    form = EditUserForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        for key in form.cleaned_data:
            setattr(user,key,form.cleaned_data.get(key))
        user.put()
        return HttpResponseRedirect(
                    reverse('member-profile', kwargs={'username': request.user.username})
        )
        
    
    if user == None:
        raise Http404("User not found")

    return render_to_response(template_name, 
                              {'form':form,}, 
                              RequestContext(request))
