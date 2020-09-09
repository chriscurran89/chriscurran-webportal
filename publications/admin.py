from django.contrib import admin
from publications.models import Publication


class PublicationAdmin(admin.ModelAdmin):

    pass


admin.site.register(Publication, PublicationAdmin)