import logging

from django.contrib.auth.models import User, Group
from eve_api.models import EVEAccount
from sso.models import ServiceAccount, Service

class UpdateServiceGroups():
        """
        Cycles through all service accounts and updates group access.
        """

        # run daily
        run_every = 84600

        @property
        def _logger(self):
            if not hasattr(self, '__logger'):
                self.__logger = logging.getLogger(__name__)
            return self.__logger

        def job(self, args):

            if args and len(args) == 1:
                services = Service.objects.filter(active=1, id=args[0])
            else:
                services = Service.objects.filter(active=1)

            for serv in services:
                self._logger.info('Updating %s service' % serv)
                api = serv.api_class
                for servacc in ServiceAccount.objects.filter(active=1, service=serv):
                    self._logger.info('Processing %s' % servacc)
                    #try:
                    ret = api.update_groups(servacc.service_uid, servacc.user.groups.all())
                    if not ret:
                        if not api.check_uid(servacc.service_uid):
                            self._logger.error('%s not setup on %s, deleting ServiceAccount record' % (servacc.service_uid, serv))
                            servacc.delete()
                    #except:
                    #    self._logger.error('Error updating %s' % servacc)

