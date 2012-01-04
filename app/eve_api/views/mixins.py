import csv
import codecs

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.views.generic.list import MultipleObjectMixin

from eve_api.views.utils import DiggPaginator

class CSVResponseMixin(object):

    def get_csv_headers(self):
        self.data = self.get_csv_data()
        if not len(self.data):
            raise ImproperlyConfigured("No data returned, so we're unable to create the header row")
        return [x for x in self.data[0].keys()]

    def get_csv_data(self):
        return getattr(self, 'csv_data', [])

    def get_dialect(self):
        return getattr(self, 'dialect', csv.excel)

    def get_charset(self):
        charset = getattr(self, 'charset', 'windows-1252')
        try:
            codecs.lookup(charset)
        except LookupError:
            raise ImproperlyConfigured("Invalid output characterset (%s) provided" % charset)
        return charset

    def get_filename(self):
        return getattr(self, 'csv_filename', 'output.csv')

    def get(self, request, *args, **kwargs):
        # Initial setup
        charset = self.get_charset()
        response = HttpResponse(mimetype='text/csv; charset=%s' % charset)
        response['Content-Disposition'] = 'attachment; filename=%s' % self.get_filename()

        w = csv.writer(response, self.get_dialect())

        # Headings
        headings = [unicode(c).encode(charset, 'replace') for c in self.get_csv_headers()]
        w.writerow(headings)

        # Rows
        for row in self.data:
            row = [unicode(c).encode(charset, 'replace') for c in row.values()]
            w.writerow(row)

        # Done
        return response


class MultipleObjectCSVResponseMixin(CSVResponseMixin, MultipleObjectMixin):

    def get_filename(self):
        return '%s.csv' % self.model.__name__

    def get_csv_data(self):
        return self.queryset.all().values()


class DetailPaginationMixin(object):

    detail_queryset_name = 'qs'

    def paginate_queryset(self, queryset, page_size):
        """
        Paginate the queryset, if needed.
        """
        paginator = DiggPaginator(queryset, page_size, body=10, tail=1)
        page = self.kwargs.get('page') or self.request.GET.get('page') or 1
        try:
            page_number = int(page)
        except ValueError:
            if page == 'last':
                page_number = paginator.num_pages
            else:
                raise Http404(_(u"Page is not 'last', nor can it be converted to an int."))
        try:
            page = paginator.page(page_number)
            return (paginator, page, page.object_list, page.has_other_pages())
        except InvalidPage:
            raise Http404(_(u'Invalid page (%(page_number)s)') % {
                                'page_number': page_number
            })

    def get_pagination_queryset(self):
        return None

    def get_context_data(self, **kwargs):
        ctx = super(DetailPaginationMixin, self).get_context_data(**kwargs)

        qs = self.get_pagination_queryset()
        paginator, page, queryset, is_paginated = self.paginate_queryset(qs, 25)

        ctx.update({
            'paginator': paginator,
            'page_obj': page,
            'is_paginated': is_paginated,
            self.detail_queryset_name: queryset,
        })
        return ctx

