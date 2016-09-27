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
import time

from cinderclient import client
from cinderclient import exceptions as cinder_exceptions
import six
from tempest.lib import base
from tempest.lib.cli import base as base_cli
from tempest.lib.cli import output_parser
from tempest.lib import exceptions

_CREDS_FILE = 'functional_creds.conf'


def credentials():
    """Retrieves credentials to run functional tests

    Credentials are either read from the environment or from a config file
    ('functional_creds.conf'). Environment variables override those from the
    config file.

    The 'functional_creds.conf' file is the clean and new way to use (by
    default tox 2.0 does not pass environment variables).
    """

    username = os.environ.get('OS_USERNAME')
    password = os.environ.get('OS_PASSWORD')
    tenant_name = (os.environ.get('OS_TENANT_NAME')
                   or os.environ.get('OS_PROJECT_NAME'))
    auth_url = os.environ.get('OS_AUTH_URL')
    volume_api_version = os.environ.get('OS_VOLUME_API_VERSION')

    config = six.moves.configparser.RawConfigParser()
    if config.read(_CREDS_FILE):
        username = username or config.get('admin', 'user')
        password = password or config.get('admin', 'pass')
        tenant_name = tenant_name or config.get('admin', 'tenant')
        auth_url = auth_url or config.get('auth', 'uri')

    return {
        'username': username,
        'password': password,
        'tenant_name': tenant_name,
        'uri': auth_url,
        'vol_api_version': volume_api_version
    }


class ClientCLITestBase(base_cli.ClientTestBase):
    """Cinder base class, issues calls to cinderclient.

    """
    def setUp(self):
        super(ClientCLITestBase, self).setUp()
        self.clients = self._get_clients()
        self.parser = output_parser

    def _get_clients(self):
        cli_dir = os.environ.get(
            'OS_CINDERCLIENT_EXEC_DIR',
            os.path.join(os.path.abspath('.'), '.tox/functional/bin'))

        return base_cli.CLIClient(cli_dir=cli_dir, **credentials())

    def cinder(self, *args, **kwargs):
        return self.clients.cinder(*args,
                                   **kwargs)

    def assertTableHeaders(self, output_lines, field_names):
        """Verify that output table has headers item listed in field_names.

        :param output_lines: output table from cmd
        :param field_names: field names from the output table of the cmd
        """
        table = self.parser.table(output_lines)
        headers = table['headers']
        for field in field_names:
            self.assertIn(field, headers)

    def assertTableStruct(self, items, field_names):
        """Verify that all items has keys listed in field_names.

        :param items: items to assert are field names in the output table
        :type items: list
        :param field_names: field names from the output table of the cmd
        :type field_names: list
        """
        # Strip off the --- if present

        for item in items:
            for field in field_names:
                self.assertIn(field, item)

    def assert_object_details(self, expected, items):
        """Check presence of common object properties.

        :param expected: expected object properties
        :param items: object properties
        """
        for value in expected:
            self.assertIn(value, items)

    def _get_property_from_output(self, output):
        """Create a dictionary from an output

        :param output: the output of the cmd
        """
        obj = {}
        items = self.parser.listing(output)
        for item in items:
            obj[item['Property']] = six.text_type(item['Value'])
        return obj

    def object_cmd(self, object_name, cmd):
        return (object_name + '-' + cmd if object_name != 'volume' else cmd)

    def wait_for_object_status(self, object_name, obj, status,
                               timeout=60):
        """Wait until object reaches given status.

        :param object_name: object name
        :param object_id: uuid4 id of an object
        :param status: expected status of an object
        :param timeout: timeout in seconds
        """
        cmd = self.object_cmd(object_name, 'show')
        start_time = time.time()
        while time.time() - start_time < timeout:
            if status in self.cinder(cmd, params=obj['id']):
                break
        else:
            self.fail("%s %s did not reach status %s after %d seconds."
                      % (object_name, object_id, status, timeout))

    def check_object_deleted(self, object_name, obj, timeout=60):
        """Check that object deleted successfully.

        :param object_name: object name
        :param object_id: uuid4 id of an object
        :param timeout: timeout in seconds
        """
        cmd = self.object_cmd(object_name, 'show')
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                if obj['id'] not in self.cinder(cmd, params=obj['id']):
                    break
        except exceptions.CommandFailed:
            pass
        else:
            self.fail("%s %s not deleted after %d seconds."
                      % (object_name, object_id, timeout))

    def object_create(self, object_name, *args, **kwargs):
        """Create an object.

        :param object_name: object name
        :param params: parameters to cinder command
        :return: object dictionary
        """
        required = ' '.join(map(lambda i: str(i), args))
        optional = ' '.join(map(lambda i: '--{0} {1}'.format(i[0],i[1]), kwargs.items()))
        params = ' '.join([required, optional])
        cmd = self.object_cmd(object_name, 'create')
        output = self.cinder(cmd, params=params)
        obj = self._get_property_from_output(output)
        self.addCleanup(self.object_delete, object_name, obj)
        self.wait_for_object_status(object_name, obj, 'available')
        return obj

    def object_delete(self, object_name, obj):
        """Delete specified object by ID.

        :param object_name: object name
        :param object_id: uuid4 id of an object
        """
        cmd = self.object_cmd(object_name, 'list')
        cmd_delete = self.object_cmd(object_name, 'delete')
#        import pdb;pdb.set_trace()
        if obj['id'] in self.cinder(cmd):
            self.cinder(cmd_delete, params=obj['id'])
        self.check_object_deleted(object_name, obj)

    def assertPropertyEquals(self, obj, prop, value):
        output = self.cinder('show', params=obj['id'])
        volume = self._get_property_from_output(output)
        self.assertEqual(six.text_type(value), volume[prop]) 

    def volume_extend(self, volume, new_size):
        self.cinder('extend', params="%s %s" % (volume['id'], new_size))

    def get_object_id(self, obj):
        return obj['id']


class ClientAPITestBase(base.BaseTestCase):
    def setUp(self):
        super(ClientAPITestBase, self).setUp()
        creds = credentials()
        self._client = client.Client(creds['vol_api_version'],
                                     creds['username'],
                                     creds['password'],
                                     creds['tenant_name'],
                                     creds['uri'])

    def cinder(self, *args, **kwargs):
        return self._client(*args, **kwargs)

    def _get_manager(self, resource_name):
        mapper = {'volume': 'volumes',
                  'snapshot': 'volume_snapshots',
                  'backup': 'backups'}
        return getattr(self._client, mapper[resource_name])

    def wait_for_object_status(self, object_name, obj, status,
                               timeout=60):
        """Wait until object reaches given status.

        :param object_name: object name
        :param object_id: uuid4 id of an object
        :param status: expected status of an object
        :param timeout: timeout in seconds
        """
        manager = self._get_manager(object_name)
        start_time = time.time()
        while time.time() - start_time < timeout:
            obj = manager.get(obj.id)
            if obj.status == status:
                break
        else:
            self.fail("%s %s did not reach status %s after %d seconds."
                      % (object_name, obj.id, status, timeout))

    def check_object_deleted(self, object_name, obj, timeout=60):
        """Check that object deleted successfully.

        :param object_name: object name
        :param object_id: uuid4 id of an object
        :param timeout: timeout in seconds
        """
        manager = self._get_manager(object_name)
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                o = manager.get(obj.id)
        except cinder_exceptions.NotFound:
            pass
        else:
            self.fail("%s %s not deleted after %d seconds."
                      % (object_name, obj.id, timeout))

    def object_create(self, object_name, *args, **kwargs):
        """Create an object.

        :param object_name: object name
        :param params: parameters to cinder command
        :return: object dictionary
        """
        manager = self._get_manager(object_name)
        obj = manager.create(*args, **kwargs)
        self.addCleanup(self.object_delete, object_name, obj)
        self.wait_for_object_status(object_name, obj, 'available')
        return obj

    def object_delete(self, object_name, obj):
        """Delete specified object by ID.

        :param object_name: object name
        :param object_id: uuid4 id of an object
        """
        manager = self._get_manager(object_name)
        print(obj)
        from cinderclient import utils
        import six
#        import pdb;pdb.set_trace()
        if isinstance(obj, six.string_types):
            o = utils.find_resource(manager, obj)
        else:
            o = obj
        try:
            manager.delete(o)
        except cinder_exceptions.NotFound:
            pass
        # cmd_delete = self.object_cmd(object_name, 'delete')
        # if object_id in self.cinder(cmd):
        #     self.cinder(cmd_delete, params=object_id)
        self.check_object_deleted(object_name, obj)

    def assertPropertyEquals(self, obj, prop, value):
        manager = self._get_manager('volume')
        volume = manager.get(obj.id)
        self.assertEqual(value, getattr(volume,prop))

    def assert_object_details(self, expected, items):
        """Check presence of common object properties.

        :param expected: expected object properties
        :param items: object properties
        """
        for value in expected:
            attr = getattr(items, value)
            self.assertTrue(hasattr(items, value))

    def volume_extend(self, volume, new_size):
        manager = self._get_manager('volume')
        manager.extend(volume, new_size)

    def get_object_id(self, obj):
        return obj.id
