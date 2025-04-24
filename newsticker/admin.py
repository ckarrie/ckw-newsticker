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


class ShareLinkAdmin(admin.ModelAdmin):
    list_display = ['short', 'display_date', 'display_days', 'valid_until', 'clicks_counter', 'resolve_url', 'get_short_link_url', 'shared_with_notes', 'absolute_url']

    def get_queryset(self, request):
        qs = super(ShareLinkAdmin, self).get_queryset(request)
        self.request = request
        return qs

    def absolute_url(self, obj):
        return self.request.build_absolute_uri(obj.get_short_link_url())


admin.site.register(models.TickerCategory, TickerCategoryAdmin)
admin.site.register(models.TickerPublication, TickerPublicationAdmin)
admin.site.register(models.TickerItemType, TickerItemTypeAdmin)
admin.site.register(models.TickerItem, TickerItemAdmin)
admin.site.register(models.TickerRef, TickerRefAdmin)
admin.site.register(models.ShareLink, ShareLinkAdmin)
