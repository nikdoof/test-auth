import csv
from django.db.models.loading import get_model

def dump(qs, outfile_path, model=None):
	"""
	Takes in a Django queryset and spits out a CSV file.
	
	Usage::
	
		>> from utils import dump2csv
		>> from dummy_app.models import *
		>> qs = DummyModel.objects.all()
		>> dump2csv.dump(qs, './data/dump.csv')
	
	Based on a snippet by zbyte64::
		
		http://www.djangosnippets.org/snippets/790/
	
	"""

        if not model:
            model = qs.model
	writer = csv.writer(open(outfile_path, 'w'))
	
	headers = []
	for field in model._meta.fields:
		headers.append(field.name)
	writer.writerow(headers)
	
	for obj in qs:
		row = []
		for field in headers:
			val = getattr(obj, field)
			if callable(val):
				val = val()
			if type(val) == unicode:
				val = val.encode("utf-8")
			row.append(val)
		writer.writerow(row)


def installed(value):
    from django.conf import settings
    apps = settings.INSTALLED_APPS
    if "." in value:
        for app in apps:
            if app == value:
                return True
    else:
        for app in apps:
            fields = app.split(".")
            if fields[-1] == value:
                return True
    return False

