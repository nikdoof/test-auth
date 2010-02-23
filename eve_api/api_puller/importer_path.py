import os
import sys
# The path to the folder containing settings.py.
BASE_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
APPS_PATH = os.path.join(BASE_PATH, 'apps')

def fix_environment():
    """
    Callable function to set up all of the Django environmental variables and
    pathing for directly executable python modules.
    """
    from importer_path import BASE_PATH
    # Prepare the environment
    sys.path.insert(0, APPS_PATH)
    sys.path.insert(0, BASE_PATH)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings' 