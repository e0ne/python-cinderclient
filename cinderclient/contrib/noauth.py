# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os

from cinderclient import auth_plugin
from cinderclient import exceptions

from keystoneauth1 import loading
from keystoneauth1 import plugin

class CinderNoAuthPlugin(plugin.BaseAuthPlugin):
    def __init__(self, user_id, project_id, roles, endpoint):
        self._user_id = user_id
        self._project_id = project_id
        self._endpoint = endpoint
        self._roles = roles
        self.auth_token = '%s:%s' % (self.opts['user_id'],
                                     self.opts['project_id'])

    def parse_opts(self, args):
        if not args.os_project_id or not args.os_tenant_id:
            raise exceptions.CommandError('tenant_id or project_id')
        self.opts['project_id'] = args.os_project_id or args.os_tenant_id

        if not args.os_user_id:
            raise exceptions.CommandError('user_id')

        self.opts['user_id'] = args.os_user_id
        self.opts['bypass_url'] = args.bypass_url
        return self.opts

    def get_headers(self, session, **kwargs):
        return {'x-user-id': self._user_id,
                'x-project-id': self._project_id,
                'x-roles': self._roles}

    def get_user_id(self, session, **kwargs):
        return self._user_id

    def get_project_id(self, session, **kwargs):
        return self._project_id

    def get_endpoint(self, session, **kwargs):
        return self._endpoint


#    def authenticate(self, cls, auth_url):
#        self.auth_token = '%s:%s' % (self.opts['user_id'],
#                                     self.opts['project_id'])
#
#        url = self.opts['bypass_url'].rstrip('/')
#        if not url.endswith(self.opts['project_id']):
#            url = ''.join([url, '/', self.opts['project_id']])
#        self.management_url = url

class CinderOpt(loading.Opt):
    @property
    def argparse_args(self):
        return ['--%s' % o.name for o in self._all_opts]

    @property
    def argparse_default(self):
        # select the first ENV that is not false-y or return None
        for o in self._all_opts:
            v = os.environ.get('Cinder_%s' % o.name.replace('-', '_').upper())
            if v:
                return v
        return self.default

class CinderNoAuthLoader(loading.BaseLoader):
    plugin_class = CinderNoAuthPlugin

    def get_options(self):
        options = super(CinderNoAuthLoader, self).get_options()
        options.extend([
            CinderOpt('user-id', help='User ID', required=True,
                      metavar="<cinder user id>"),
            CinderOpt('project-id', help='Project ID', required=True,
                      metavar="<cinder project id>"),
            CinderOpt('roles', help='Roles', default="admin",
                      metavar="<cinder roles>"),
            CinderOpt('endpoint', help='Gnocchi endpoint',
                       dest="endpoint", required=True,
                       metavar="<cinder endpoint>"),
        ])
        return options

#manager_class = NoAuthPlugin
#name = 'noauth'
