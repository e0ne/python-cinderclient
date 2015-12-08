
# Copyright 2011-2014 OpenStack Foundation
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

from cinderclient import exceptions
from cinderclient.v2.contrib.brick import utils

try:
    from os_brick.initiator import connector
except ImportError:
    raise exceptions.CommandError(utils.OS_BRICK_INSTALL_ERROR_MSG)


def get_connector(self, multipath=False, enforce_multipath=False):
    conn_prop = connector.get_connector_properties(utils.get_root_helper(),
                                                   utils.get_my_ip(),
                                                   multipath=multipath,
                                                   enforce_multipath=
                                                   enforce_multipath)
    return conn_prop
