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


import six
import ddt

from tempest.lib import exceptions

from cinderclient.tests.functional import base


class CinderVolumeTests(object):
    """Check of base cinder volume commands."""

    VOLUME_PROPERTY = ('attachments', 'availability_zone', 'bootable',
                       'created_at', 'description', 'encrypted', 'id',
                       'metadata', 'name', 'size', 'status',
                       'user_id', 'volume_type')

    def test_volume_create_delete_id(self):
        """Create and delete a volume by ID."""
        volume = self.object_create('volume', 1)
#        self.assert_object_details(self.VOLUME_PROPERTY, volume.keys())
        self.assert_object_details(self.VOLUME_PROPERTY, volume)
        self.object_delete('volume', volume)
        self.check_object_deleted('volume', volume)

    def test_volume_create_delete_name(self):
        """Create and delete a volume by name."""
#        import pdb; pdb.set_trace()
        volume = self.object_create('volume', 1, name='TestVolumeNamedCreate')

        self.object_delete('volume', volume)
        self.check_object_deleted('volume', volume)

    # def test_volume_show(self):
    #     """Show volume details."""
    #     volume = self.object_create('volume', params='1 --name TestVolumeShow')
    #     output = self.cinder('show', params='TestVolumeShow')
    #     volume = self._get_property_from_output(output)
    #     self.assertEqual('TestVolumeShow', volume['name'])
    #     self.assert_object_details(self.VOLUME_PROPERTY, volume.keys())

    #     self.object_delete('volume', volume['id'])
    #     self.check_object_deleted('volume', volume['id'])

    def test_volume_extend(self):
        """Extend a volume size."""
        volume = self.object_create('volume',
                                    1, name='TestVolumeExtend')
        self.volume_extend(volume, 2)
#        import pdb;pdb.set_trace()
        self.wait_for_object_status('volume', volume, 'available')
        self.assertPropertyEquals(volume, 'size', 2)
#        output = self.cinder('show', params=volume['id'])
#        volume = self._get_property_from_output(output)
#        self.assertEqual('2', volume['size'])

        self.object_delete('volume', volume)
        self.check_object_deleted('volume', volume)

    def test_volume_create_from_snapshot(self):
        """Test steps:

        1) create volume in Setup()
        2) create snapshot
        3) create volume from snapshot
        4) check that volume from snapshot has been successfully created
        """
        volume = self.object_create('volume', 1)
        volume_id = self.get_object_id(volume)
        snapshot = self.object_create('snapshot', volume_id)
        snapshot_id = self.get_object_id(snapshot)
        volume_from_snapshot = self.object_create('volume', 1,
                                           snapshot_id=snapshot_id)
        self.object_delete('snapshot', snapshot)
        self.object_delete('volume', volume)
        self.object_delete('volume', volume_from_snapshot)

    def test_volume_create_from_volume(self):
        """Test steps:

        1) create volume in Setup()
        2) create volume from volume
        3) check that volume from volume has been successfully created
        """
        volume = self.object_create('volume', 1)
        volume_id = self.get_object_id(volume)
        volume_from_volume = self.object_create('volume', 1,
                                         source_volid=volume_id)

        self.object_delete('volume', volume)
        self.object_delete('volume', volume_from_volume)


@ddt.ddt
class CinderVolumeCLITests(base.ClientCLITestBase, CinderVolumeTests):
    @ddt.data(
        ('', (r'Size is a required parameter')),
        ('-1', (r'Invalid volume size provided for create request')),
        ('0', (r'Invalid input received')),
        ('size', (r'invalid int value')),
        ('0.2', (r'invalid int value')),
        ('2 GB', (r'unrecognized arguments')),
        ('999999999', (r'VolumeSizeExceedsAvailableQuota')),
    )
    @ddt.unpack
    def test_volume_create_with_incorrect_size(self, value, ex_text):

        six.assertRaisesRegex(self, exceptions.CommandFailed, ex_text,
                              self.object_create, 'volume', value)


@ddt.ddt
class CinderVolumeExtendNegativeTests(base.ClientCLITestBase):
    """Check of cinder volume extend command."""

    def setUp(self):
        super(CinderVolumeExtendNegativeTests, self).setUp()
        self.volume = self.object_create('volume', 1)

    @ddt.data(
        ('', (r'too few arguments')),
        ('-1', (r'New size for extend must be greater than current size')),
        ('0', (r'Invalid input received')),
        ('size', (r'invalid int value')),
        ('0.2', (r'invalid int value')),
        ('2 GB', (r'unrecognized arguments')),
        ('999999999', (r'VolumeSizeExceedsAvailableQuota')),
    )
    @ddt.unpack
    def test_volume_extend_with_incorrect_size(self, value, ex_text):

        six.assertRaisesRegex(
            self, exceptions.CommandFailed, ex_text, self.cinder, 'extend',
            params='{0} {1}'.format(self.volume['id'], value))

    @ddt.data(
        ('', (r'too few arguments')),
        ('1234-1234-1234', (r'No volume with a name or ID of')),
        ('my_volume', (r'No volume with a name or ID of')),
        ('1234 1234', (r'unrecognized arguments'))
    )
    @ddt.unpack
    def test_volume_extend_with_incorrect_volume_id(self, value, ex_text):

        six.assertRaisesRegex(
            self, exceptions.CommandFailed, ex_text, self.cinder, 'extend',
            params='{0} 2'.format(value))


class CinderVolumeAPITests(base.ClientAPITestBase, CinderVolumeTests):
    pass

# class CinderSnapshotTests(base.ClientCLITestBase):
#     """Check of base cinder snapshot commands."""

#     SNAPSHOT_PROPERTY = ('created_at', 'description', 'metadata', 'id',
#                          'name', 'size', 'status', 'volume_id')

#     def test_snapshot_create_and_delete(self):
#         """Create a volume snapshot and then delete."""
#         volume = self.object_create('volume', params='1')
#         snapshot = self.object_create('snapshot', params=volume['id'])
#         self.assert_object_details(self.SNAPSHOT_PROPERTY, snapshot.keys())
#         self.object_delete('snapshot', snapshot['id'])
#         self.check_object_deleted('snapshot', snapshot['id'])
#         self.object_delete('volume', volume['id'])
#         self.check_object_deleted('volume', volume['id'])


# class CinderBackupTests(base.ClientCLITestBase):
#     """Check of base cinder backup commands."""

#     BACKUP_PROPERTY = ('id', 'name', 'volume_id')

#     def test_backup_create_and_delete(self):
#         """Create a volume backup and then delete."""
#         volume = self.object_create('volume', params='1')
#         backup = self.object_create('backup', params=volume['id'])
#         self.assert_object_details(self.BACKUP_PROPERTY, backup.keys())
#         self.object_delete('volume', volume['id'])
#         self.check_object_deleted('volume', volume['id'])
#         self.object_delete('backup', backup['id'])
#         self.check_object_deleted('backup', backup['id'])
