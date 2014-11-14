# -*- coding: utf-8 -*-
# Copyright (c) 2011-2014 Polyconseil SAS. All rights reserved.
from __future__ import absolute_import, print_function, unicode_literals

from django.conf import settings
from django.utils.translation import ugettext as _


class GetconfMiddleware(object):
    """
   Middleware that sets the service and environment getconf has read
   """
    def process_request(self, request):
        request.SERVICE = getattr(settings, 'SERVICE', _("unknown"))
        request.ENVIRONMENT = getattr(settings, 'ENVIRONMENT', _("unknown"))
