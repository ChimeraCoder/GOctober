from django.conf.urls.defaults import patterns, include, url
from django.contrib.auth import views
from django.contrib import admin

from tastypie.api import Api

from api import CommitResource, ProjectResource, BitbucketHandler

v1_api = Api(api_name='v1')
v1_api.register(CommitResource())
v1_api.register(ProjectResource())
v1_api.register(BitbucketHandler())

admin.autodiscover()


urlpatterns = patterns('',
    # This line should only be active during maintenance!
    #url(r'^.*', 'july.views.maintenance'),
    url(r'^_admin/', admin.site.urls),
    url(r'^api/', include(v1_api.urls)),
    url(r'^$', 'july.views.index', name='index'),
    #url(r'^live/', 'july.live.views.live', name='julython-live'),
    #url(r'^_reconnect/', 'july.live.views.reconnect', name='live-reconnect'),
    url(r'^help/', 'july.views.help_view', name='help'),
    url(r'^signin/$', views.login, name="signin"),
    url(r'^signout/$', views.logout, {'next_page': '/'}, name="signout"),
    url(r'^accounts/profile', 'july.views.login_redirect'),
    url(r'^accounts/', include('social_auth.urls')),
    url(r'^', include('july.people.urls')),

)
