from collections import OrderedDict

from django.db import models
from django.urls import reverse
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
        return self.name


class TickerPublication(models.Model):
    name = models.CharField(max_length=60)
    url = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class TickerItemType(models.Model):
    name = models.CharField(max_length=60)
    color = models.CharField(max_length=6, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class TickerItemManager(models.Manager):
    def current(self, ref_date=None, limit_days=3, limit_categories_qs=None):
        #today = timezone.localtime(timezone.now(), timezone=timezone.get_current_timezone()).date()
        if ref_date is None:
            ref_date = timezone.now().date()
        start_calc_date = ref_date - timezone.timedelta(days=limit_days)
        qs = self.filter(pub_dt__date__range=(start_calc_date, ref_date))
        #print(f'pub_dt__date__range=("{start_calc_date}", "{ref_date}")')
        if limit_categories_qs:
            qs = qs.filter(category__in=limit_categories_qs)
        qs = qs.order_by('-pub_dt__date', 'category__path', 'pub_dt')
        return qs

    def current_by_date(self, qs=None, limit_days=3, limit_categories_qs=None, ref_date=None):
        if qs is None:
            qs = self.current(ref_date=ref_date, limit_days=limit_days, limit_categories_qs=limit_categories_qs)

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
    summary = HTMLField(
        null=True,
        blank=True,
        help_text='Cited Work: GRÜNEN | Marker: Referenz'
    )
    has_summary = models.BooleanField(default=True, editable=False)
    objects = TickerItemManager()

    def get_rendered_summary(self):
        soup = BeautifulSoup(self.summary, 'html.parser')
        marker_tags = soup.find_all("span", {'class': "marker"})
        tickerrefs = list(self.tickerref_set.all())
        ref_type_icon = {
            'website': 'fa fa-globe',
            'pdf': 'fa fa-file-pdf',
            'video': 'fa fa-video',
            'image': 'fa fa-image',
            'tickeritem': 'fa fa-link'
        }

        for i, marker_tag in enumerate(marker_tags):
            try:
                ref = tickerrefs[i]
            except IndexError:
                ref = None
            if ref:
                href = ref.get_href()
                if href:
                    sup_tag = soup.new_tag('sup')
                    ref_title = ref.get_ref_title()
                    target = ''
                    if not ref.get_is_local():
                        target = '_blank'
                    a_tag = soup.new_tag('a', attrs={'href': href, 'title': ref_title, 'data-ref-type': ref.ref_type, 'target': target})
                    a_tag.string = str(ref.pk) + " "
                    fa_icon_tag = soup.new_tag('i', attrs={'class': ref_type_icon[ref.ref_type]})
                    a_tag.append(fa_icon_tag)
                    sup_tag.append(a_tag)
                    marker_tag.replace_with(sup_tag)

        return str(soup)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.has_summary = False
        if self.summary:
            if len(self.summary) > len('<p></p>'):
                self.has_summary = True
        super().save(update_fields=('has_summary',))

    def get_absolute_url(self):
        # Todo: add single page
        return self.get_overview_url()

    def get_overview_url(self):
        return reverse('gruene_cms_news:newsticker_index') + f'?date={self.pub_dt.strftime("%Y-%m-%d")}&days=0&collapse_cat={self.category.pk}#ti-{self.pk}'

    def __str__(self):
        return self.headline


class TickerRef(models.Model):
    item = models.ForeignKey(TickerItem, on_delete=models.CASCADE, related_name='tickerref_set')
    ref_type = models.CharField(max_length=30, choices=(
        ('website', 'Website'),
        ('pdf', 'PDF'),
        ('video', 'Video'),
        ('image', 'Image'),
        ('tickeritem', 'Ticker Item'),
    ))
    index = models.IntegerField(default=0)
    url = models.URLField(null=True, blank=True)
    uploadfile = models.FileField(upload_to=tickerref_file_upload, null=True, blank=True)
    linked_tickeritem = models.ForeignKey(TickerItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_tickerref_set')

    def get_is_local(self):
        if self.url:
            if self.url.startswith('http'):
                return False
            return True
        if self.uploadfile:
            return True
        if self.linked_tickeritem:
            return True
        return False

    def get_ref_title(self):
        if self.url:
            if self.ref_type == 'website':
                if self.url.startswith('http'):
                    return f'Externer Link'
                return 'Interner Link'
            if self.ref_type == 'pdf':
                if self.url.startswith('http'):
                    return f'Externes PDF'
                return f'Internes PDF'
            if self.ref_type == 'video':
                if 'youtube' in self.url:
                    return 'YouTube-Video'
                return 'Video-Link'
            if self.ref_type == 'image':
                if self.url.startswith('http'):
                    return f'Externes Bild'
                return f'Internes Bild'

        if self.uploadfile:
            if self.ref_type == 'website':
                return 'Interner Link'
            if self.ref_type == 'pdf':
                return f'Internes PDF'
            if self.ref_type == 'video':
                return f'Internes Video'
            if self.ref_type == 'image':
                return f'Internes Bild'

        if self.linked_tickeritem:
            dp = f'News Ticker: {self.linked_tickeritem.headline}, vom {self.linked_tickeritem.pub_dt.strftime("%Y-%m-%d")}'
        return dp

    def get_href(self):
        if self.uploadfile:
            return self.uploadfile.url
        if self.url:
            return self.url
        if self.linked_tickeritem:
            return self.linked_tickeritem.get_absolute_url()
        return None

    class Meta:
        ordering = ['item', 'index']




