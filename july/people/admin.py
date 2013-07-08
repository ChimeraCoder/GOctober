from django.contrib import admin
from models import Team, Commit, Location, AchievedBadge, Project
from models import Badge, Language


def purge_commits(modeladmin, request, queryset):
    for obj in queryset:
        obj.commit_set.all().delete()
purge_commits.short_description = "Purge Commits"


admin.site.register(
    Commit,
    list_display=['hash', 'email', 'timestamp', 'project', 'user'],
    search_fields=['hash', 'email', 'project__name', 'user__username'],
    ordering=['-timestamp'],
    raw_id_fields=['user', 'project'])

admin.site.register(
    Language,
    list_display=["__unicode__"])

admin.site.register(
    Badge,
    list_display=["__unicode__"])

admin.site.register(AchievedBadge)


class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'forked', 'active']
    list_filter = ['active']
    search_fields = ['name', 'url']
    actions = [purge_commits]


class GroupAdmin(admin.ModelAdmin):
    list_display = ["__unicode__", "slug", 'total', 'approved']
    ordering = ['-total']
    list_filter = ['approved']
    search_fields = ['name', 'slug']


admin.site.register(Team, GroupAdmin)
admin.site.register(Location, GroupAdmin)
admin.site.register(Project, ProjectAdmin)
