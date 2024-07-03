from django.contrib import admin

from teams.models import Team, Task


admin.site.register(Team)
admin.site.register(Task)