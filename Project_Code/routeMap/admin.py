from django.contrib import admin
from .models import pointBox
# Register your models here.

class pointBoxAdmin(admin.ModelAdmin):
    list_display = ('id', 'situaName', 'situation', 'coordinate', 'remark', 'popularNum', 'isSlove', 'startDate', 'endDate', 'posterName', 'picLink', 'physicalAddr')
    list_filter = ('situation' ,'coordinate')
    search_fields = ('situaName',)
    ordering = ('id',)

admin.site.register(pointBox, pointBoxAdmin)