import csv
import codecs

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.views.generic.list import MultipleObjectMixin


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

