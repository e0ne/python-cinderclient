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


from cinderclient.tests.functional import base


class CinderBackupTests(object):
    """Check of base cinder backup commands."""

    BACKUP_PROPERTY = ('id', 'name', 'volume_id')

    def test_backup_create_and_delete(self):
        """Create a volume backup and then delete."""
        volume = self.object_create('volume', 1)
        volume_id = self.get_object_id(volume)
        backup = self.object_create('backup', volume_id)
        self.assert_object_details(self.BACKUP_PROPERTY, backup)
        self.object_delete('volume', volume)
        self.object_delete('backup', backup)


class CinderBackupCLITests(base.ClientCLITestBase, CinderBackupTests):
    pass


class CinderBackupAPITests(base.ClientAPITestBase, CinderBackupTests):
    pass

