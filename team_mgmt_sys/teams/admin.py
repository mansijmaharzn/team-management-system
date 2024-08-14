from django.contrib import admin

from teams.models import Team, Task


# admin.site.register(Team)
admin.site.register(Task)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "description")
