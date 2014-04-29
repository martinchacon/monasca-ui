# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging

from django.conf import settings
from monclient import client as mon_client
from horizon.utils import functions as utils
from openstack_dashboard.api import base

LOG = logging.getLogger(__name__)


class AttrStore:
    pass

def format_parameters(params):
    parameters = {}
    for count, p in enumerate(params, 1):
        parameters['Parameters.member.%d.ParameterKey' % count] = p
        parameters['Parameters.member.%d.ParameterValue' % count] = params[p]
    return parameters


def monclient(request, password=None):
    api_version = "2_0"
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    endpoint = 'http://192.168.10.4:8080/v2.0'  # base.url_for(request, 'orchestration')
    LOG.debug('monclient connection created using token "%s" and url "%s"' %
              (request.user.token.id, endpoint))
    kwargs = {
        'token': request.user.token.id,
        'insecure': insecure,
        'ca_file': cacert,
        'username': request.user.username,
        'password': password
        #'timeout': args.timeout,
        #'ca_file': args.ca_file,
        #'cert_file': args.cert_file,
        #'key_file': args.key_file,
    }
    client = mon_client.Client(api_version, endpoint, **kwargs)
    client.format_parameters = format_parameters
    return client


def alarm_list(request, marker=None, paginate=False):
    limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
    page_size = utils.get_page_size(request)

    if paginate:
        request_size = page_size + 1
    else:
        request_size = limit

    kwargs = {}
    if marker:
        kwargs['marker'] = marker
    args = AttrStore()
    args.runlocal = True
    args.os_tenant_id = "12345678"
    alarm_iter = monclient(request).alarms.list(args, **kwargs)

    has_more_data = False
    alarms = list(alarm_iter)
    if paginate:
        if len(alarms) > page_size:
            alarms.pop()
            has_more_data = True
    return (alarms, has_more_data)


def alarm_delete(request, alarm_id):
    return monclient(request).alarm.delete(alarm_id)


def alarm_get(request, alarm_id):
    return monclient(request).alarm.get(alarm_id)


def alarm_create(request, password=None, **kwargs):
    return monclient(request, password).alarm.create(**kwargs)


def alarm_update(request, alarm_id, **kwargs):
    return monclient(request).alarm.update(alarm_id, **kwargs)
