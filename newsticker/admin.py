from . import models

from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory


class TickerRefInlineAdmin(admin.TabularInline):
    model = models.TickerRef
    fk_name = 'item'
    autocomplete_fields = ['linked_tickeritem']


class TickerCategoryAdmin(TreeAdmin):
    list_display = ['name']
    form = movenodeform_factory(models.TickerCategory)


class TickerPublicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'url']


class TickerItemTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'color']


class TickerItemAdmin(admin.ModelAdmin):
    list_display = ['category', 'publication', 'pub_dt', 'headline', 'refs_in_summary_count']
    search_fields = [
        'headline',
        'summary'
    ]
    date_hierarchy = 'pub_dt'
    inlines = [TickerRefInlineAdmin]


class TickerRefAdmin(admin.ModelAdmin):
    list_display = ['item', 'is_in_summary', 'ref_type', 'index', 'url', 'uploadfile',]
    list_filter = ['is_in_summary', 'ref_type']


admin.site.register(models.TickerCategory, TickerCategoryAdmin)
admin.site.register(models.TickerPublication, TickerPublicationAdmin)
admin.site.register(models.TickerItemType, TickerItemTypeAdmin)
admin.site.register(models.TickerItem, TickerItemAdmin)
admin.site.register(models.TickerRef, TickerRefAdmin)
