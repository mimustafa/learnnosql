from django.contrib import admin

from .models import Participant, Site, Study, Visit


admin.site.register(Study)
admin.site.register(Site)
admin.site.register(Participant)
admin.site.register(Visit)
