from collections import OrderedDict

from django.db import models
from django.utils import timezone
from treebeard.mp_tree import MP_Node
from djangocms_text_ckeditor.fields import HTMLField
from bs4 import BeautifulSoup


def tickerref_file_upload(instance, filename):
    return 'newsticker/files/{0}/{1}'.format(instance.item.pk, filename)


class TickerCategory(MP_Node):
    name = models.CharField(max_length=60)
    node_order_by = ['name']

    def __str__(self):
        return 'Category: {}'.format(self.name)


class TickerPublication(models.Model):
    name = models.CharField(max_length=60)
    url = models.URLField(null=True, blank=True)

    def __str__(self):
        return 'Pub: {}'.format(self.name)


class TickerItemType(models.Model):
    name = models.CharField(max_length=60)
    color = models.CharField(max_length=6, null=True, blank=True)

    def __str__(self):
        return 'Type: {}'.format(self.name)


class TickerItemManager(models.Manager):
    def current(self, limit_days=3, limit_categories_qs=None):
        #today = timezone.localtime(timezone.now(), timezone=timezone.get_current_timezone()).date()
        start_day = timezone.localtime(
            timezone.now() - timezone.timedelta(days=limit_days),
            timezone=timezone.get_current_timezone()
        ).date()
        qs = self.filter(pub_dt__date__gte=start_day)
        if limit_categories_qs:
            qs = qs.filter(category__in=limit_categories_qs)
        qs = qs.order_by('-pub_dt__date', 'category', 'pub_dt')
        return qs

    def current_by_date(self, qs=None, limit_days=3, limit_categories_qs=None):
        if qs is None:
            qs = self.current(limit_days=limit_days, limit_categories_qs=limit_categories_qs)

        by_date = OrderedDict()
        for ni in qs:
            d = timezone.localtime(ni.pub_dt, timezone=timezone.get_current_timezone()).date()
            cat = ni.category
            if d not in by_date:
                by_date[d] = OrderedDict()

            if cat not in by_date[d]:
                by_date[d][cat] = [ni]
            else:
                by_date[d][cat].append(ni)
        return by_date


class TickerItem(models.Model):
    category = models.ForeignKey(TickerCategory, on_delete=models.CASCADE)
    publication = models.ForeignKey(TickerPublication, on_delete=models.CASCADE)
    item_type = models.ForeignKey(TickerItemType, on_delete=models.CASCADE)
    created_dt = models.DateTimeField(auto_now_add=True)
    pub_dt = models.DateTimeField(default=timezone.now)
    headline = models.CharField(max_length=255)
    summary = HTMLField(help_text='Cited Work: GRÜNEN | Marker: Referenz')
    objects = TickerItemManager()

    def get_rendered_summary(self):
        soup = BeautifulSoup(self.summary, 'html.parser')
        marker_tags = soup.find_all("span", {'class': "marker"})
        tickerrefs = list(self.tickerref_set.all())
        for i, marker_tag in enumerate(marker_tags):
            try:
                ref = tickerrefs[i]
            except IndexError:
                ref = None
            if ref:
                href = ref.get_href()
                if href:
                    sup_tag = soup.new_tag('sup')
                    a_tag = soup.new_tag('a', attrs={'href': href, 'title': href, 'data-ref-type': ref.ref_type, 'target': '_blank'})
                    a_tag.string = str(ref.pk)
                    sup_tag.append(a_tag)
                    marker_tag.replace_with(sup_tag)

        return str(soup)

    def __str__(self):
        return self.headline


class TickerRef(models.Model):
    item = models.ForeignKey(TickerItem, on_delete=models.CASCADE)
    ref_type = models.CharField(max_length=30, choices=(
        ('website', 'Website'),
        ('pdf', 'PDF'),
        ('video', 'Video'),
        ('image', 'Image'),
    ))
    index = models.IntegerField(default=0)
    url = models.URLField(null=True, blank=True)
    uploadfile = models.FileField(upload_to=tickerref_file_upload, null=True, blank=True)

    def get_href(self):
        if self.url:
            return self.url
        if self.uploadfile:
            return self.uploadfile.url
        return None

    class Meta:
        ordering = ['item', 'index']




