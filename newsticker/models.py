from collections import OrderedDict
from urllib.parse import urlencode

from django.db import models
from django.urls import reverse, resolve
from django.utils import timezone
from treebeard.mp_tree import MP_Node
from djangocms_text_ckeditor.fields import HTMLField

from bs4 import BeautifulSoup
import string
import random


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

    def current_by_date(self, qs=None, limit_days=3, limit_categories_qs=None, ref_date=None, short_link=None):
        if qs is None:
            qs = self.current(ref_date=ref_date, limit_days=limit_days, limit_categories_qs=limit_categories_qs)

        by_date = OrderedDict()
        for ni in qs:
            ni.short_link = short_link
            d = timezone.localtime(ni.pub_dt, timezone=timezone.get_current_timezone()).date()
            cat = ni.category
            if d not in by_date:
                by_date[d] = OrderedDict()

            if cat not in by_date[d]:
                by_date[d][cat] = [ni]
            else:
                by_date[d][cat].append(ni)
        return by_date


class TickerRefManager(models.Manager):
    def in_summary(self):
        return self.filter(is_in_summary=True)

    def not_in_summary(self):
        return self.filter(is_in_summary=False)


class TickerItem(models.Model):
    short_link = None

    category = models.ForeignKey(TickerCategory, on_delete=models.CASCADE)
    publication = models.ForeignKey(TickerPublication, on_delete=models.CASCADE)
    item_type = models.ForeignKey(TickerItemType, on_delete=models.CASCADE)
    created_dt = models.DateTimeField(auto_now_add=True)
    pub_dt = models.DateTimeField(default=timezone.now)
    headline = models.CharField(max_length=255)
    summary = HTMLField(
        null=True,
        blank=True,
        help_text='Cited Work: GRÜNEN | Marker: Referenz | Variable: Mehr +/-'
    )
    has_summary = models.BooleanField(default=True, editable=False)
    refs_in_summary_count = models.IntegerField(default=0, editable=False)
    objects = TickerItemManager()

    def get_rendered_summary(self):
        soup = BeautifulSoup(self.summary, 'html.parser')
        marker_tags = soup.find_all("span", {'class': "marker"})
        tickerrefs = list(self.tickerref_set.all())
        ref_type_icon = {
            'website': 'fa ms-1 fa-globe',
            'pdf': 'fa ms-1 fa-file-pdf',
            'video': 'fa ms-1 fa-video',
            'image': 'fa ms-1 fa-image',
            'tickeritem': 'fa ms-1 fa-link'
        }

        ref_replaced_in_summary = []

        for i, marker_tag in enumerate(marker_tags):
            try:
                ref = tickerrefs[i]
            except IndexError:
                ref = None
            if ref:
                href = ref.get_href(short_link=self.short_link)
                ref_text = ref.text
                ref_title = ref.title
                if href:
                    ref_title = ref.get_ref_title()
                    target = ''
                    if not ref.get_is_local():
                        target = '_blank'
                    # create Tags
                    a_tag = soup.new_tag('a', attrs={'href': href, 'title': ref_title, 'data-ref-type': ref.ref_type, 'target': target})
                    sup_tag = soup.new_tag('sup', attrs={'class': 'mx-1'})
                    fa_icon_tag = soup.new_tag('i', attrs={'class': ref_type_icon[ref.ref_type]})

                    if '^' in marker_tag.string:
                        a_tag.string = ''
                    else:
                        a_tag.string = marker_tag.string
                    # sup-Tag ID
                    #sup_tag.string = str(ref.pk) + ""
                    sup_tag.string = ""
                    # i-Tag
                    sup_tag.append(fa_icon_tag)
                    a_tag.append(sup_tag)

                    marker_tag.replace_with(a_tag)
                    ref_replaced_in_summary.append(ref)

                if ref_text and ref.ref_type == 'abbreviation':
                    abbr_tag = soup.new_tag('abbr', attrs={
                        'title': ref_text,
                        #'class': 'initialism'
                    })
                    if ref_title:
                        abbr_tag.string = ref_title
                    else:
                        abbr_tag.string = marker_tag.string
                    hidden_tag = soup.new_tag('span', attrs={'class': 'd-none hidden-abbr'})
                    hidden_tag.string = f' ({ref_text})'
                    abbr_tag.append(hidden_tag)
                    marker_tag.replace_with(abbr_tag)
                    ref_replaced_in_summary.append(ref)

        # Update Ref stats
        for ref in tickerrefs:
            ref.is_in_summary = ref in ref_replaced_in_summary
            ref.save(update_fields=('is_in_summary',))
        self.refs_in_summary_count = len(ref_replaced_in_summary)
        self.save(update_fields=('refs_in_summary_count',))

        return str(soup)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.has_summary = False
        if self.summary:
            if len(self.summary) > len('<p></p>'):
                self.has_summary = True
        super().save(update_fields=('has_summary',))

    def get_absolute_url(self, short_link=None):
        # Todo: add single page
        return self.get_overview_url(short_link=short_link)

    def get_overview_url(self, collape_cat=False, short_link=None):
        params = {
            'date': self.pub_dt.strftime("%Y-%m-%d"),
            'days': '0',
            'show_all': 'on'
        }
        if self.short_link:
            params['s'] = self.short_link.short
        if short_link:
            params['s'] = short_link.short
        if collape_cat:
            params['collapse_cat'] = str(self.category.pk)

        get_params = urlencode(params)

        return reverse('gruene_cms_news:newsticker_index') + f'?{get_params}#ti-{self.pk}'

    def __str__(self):
        date_str = self.pub_dt.strftime("%Y-%m-%d")
        return f'{date_str} {self.headline}'


class TickerRef(models.Model):
    item = models.ForeignKey(TickerItem, on_delete=models.CASCADE, related_name='tickerref_set')
    ref_type = models.CharField(max_length=30, choices=(
        ('website', 'Website'),
        ('pdf', 'PDF'),
        ('video', 'Video'),
        ('image', 'Image'),
        ('tickeritem', 'Ticker Item'),
        ('abbreviation', 'Abbreviation'),
    ))
    index = models.IntegerField(default=0)
    url = models.URLField(null=True, blank=True)
    uploadfile = models.FileField(upload_to=tickerref_file_upload, null=True, blank=True)
    linked_tickeritem = models.ForeignKey(TickerItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_tickerref_set')

    title = models.CharField(max_length=255, null=True, blank=True)
    text = models.CharField(max_length=255, null=True, blank=True)
    #internal = models.BooleanField(default=False)

    is_in_summary = models.BooleanField(default=False, editable=False)
    objects = TickerRefManager()

    def get_is_local(self):
        if self.url:
            if self.url.startswith('http'):
                return False
            return True
        if self.uploadfile:
            return True
        if self.linked_tickeritem:
            return True
        if self.text and self.ref_type == 'abbreviation':
            return True
        return False

    def get_ref_title(self):
        dp = "MISSING FILE/URL/LINKED TICKERITEM"
        if self.title:
            return self.title
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

    def get_href(self, short_link=None):
        if self.uploadfile:
            return self.uploadfile.url
        if self.url:
            return self.url
        if self.linked_tickeritem:
            return self.linked_tickeritem.get_absolute_url(short_link=short_link)
        return None

    class Meta:
        ordering = ['item', 'index']


class ShareLink(models.Model):
    short = models.CharField(max_length=5, editable=False)
    valid_until = models.DateTimeField()
    shared_with_notes = models.CharField(max_length=255, null=True, blank=True)

    # maybe later: limit to tickeritems
    #display_tickeritems = models.ManyToManyField(TickerItem, null=True)
    display_date = models.DateField()
    display_days = models.IntegerField(default=0)

    clicks_log = models.TextField(null=True, blank=True)
    clicks_counter = models.IntegerField(default=0)

    @staticmethod
    def generate_short_id(size):
        return ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=size))

    def get_default_short_size(self):
        return self._meta.get_field('short').max_length

    def save(self, *args, **kwargs):
        if not self.short:
            size = self.get_default_short_size()
            short = self.generate_short_id(size=size)
            if ShareLink.objects.filter(short=short).exists():
                return self.save(*args, **kwargs)
            self.short = short
        return super(ShareLink, self).save(*args, **kwargs)

    def is_valid(self):
        return self.valid_until >= timezone.now()

    def add_request(self, request):
        local_dt = timezone.localtime(timezone.now(), timezone=timezone.get_current_timezone())
        dt_str = local_dt.strftime("%Y-%m-%d;%H:%M:%S")
        user_agent = request.headers["user-agent"]
        content_params = request.content_params
        user_name = request.user.get_username()
        log_line = f'{dt_str};{user_name};{user_agent};{content_params}\n'
        logs = self.clicks_log or ''
        logs += log_line
        self.clicks_log = logs
        self.clicks_counter += 1
        self.save(update_fields=['clicks_log', 'clicks_counter'])

    def resolve_url(self, view_name='gruene_cms_news:newsticker_index'):
        base_url = reverse(view_name)
        params = {
            'date': self.display_date.strftime("%Y-%m-%d"),
            'days': str(self.display_days),
            'show_all': 'on',
            's': self.short
        }
        get_params = urlencode(params)
        return base_url + f'?{get_params}'

    def get_short_link_url(self, view_name='gruene_cms_news:newsticker_share'):
        return reverse(view_name, kwargs={'short': self.short})

    def __str__(self):
        return self.short


