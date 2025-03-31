from . import models

from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory


class TickerRefInlineAdmin(admin.TabularInline):
    model = models.TickerRef


class TickerCategoryAdmin(TreeAdmin):
    list_display = ['name']
    form = movenodeform_factory(models.TickerCategory)


class TickerPublicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'url']


class TickerItemTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'color']


class TickerItemAdmin(admin.ModelAdmin):
    list_display = ['category', 'publication', 'created_dt', 'headline']
    inlines = [TickerRefInlineAdmin]


class TickerRefAdmin(admin.ModelAdmin):
    list_display = ['item', 'ref_type', 'index', 'url', 'uploadfile']


admin.site.register(models.TickerCategory, TickerCategoryAdmin)
admin.site.register(models.TickerPublication, TickerPublicationAdmin)
admin.site.register(models.TickerItemType, TickerItemTypeAdmin)
admin.site.register(models.TickerItem, TickerItemAdmin)
admin.site.register(models.TickerRef, TickerRefAdmin)
