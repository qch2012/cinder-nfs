# Copyright 2022 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from unittest.mock import patch
import json

from ops.model import Relation, BlockedStatus
from ops.testing import Harness
from src.charm import CharmCinderNFSCharm
from src.charm import _write_config


class TestCharm(unittest.TestCase):
    maxDiff = None

    @patch("src.charm.shutil.chown")
    @patch("src.charm.os.chmod")
    @patch("src.charm.open", new_callable=unittest.mock.mock_open)
    def setUp(self, mock_open, mock_chmod, mock_chown):
        self.harness = Harness(CharmCinderNFSCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()
        self.harness.set_leader(True)
        self.model = self.harness.model
        self.storage_backend = self.harness.add_relation("storage-backend",
                                                         "cinder")
        self.harness.add_relation_unit(self.storage_backend, "cinder/0")
        self.harness.update_config(
            {
                "volume-backend-name": "cinder-nfs",
                "nfs-shares": "172.18.18.61:/srv/test",
                "nfs-shares-config": "/test/nfs_shares",
                "nfs-mount-point-base": "/var/lib/cinder/nfs",
                "nfs-mount-options": "vers=3",
                "nfs-mount-attempts": 3,
                "nfs-snapshot-support": True,
            }
        )

    def _get_sub_conf(self):
        # return relation data
        rel = self.model.get_relation("storage-backend", 0)
        self.assertIsInstance(rel, Relation)
        rdata = rel.data[self.model.unit]
        rdata = json.loads(rdata["subordinate_configuration"])
        return dict(
            (rdata["cinder"]["/etc/cinder/cinder.conf"]["sections"]
             ["cinder-nfs"])
        )

    @patch("src.charm.shutil.chown")
    @patch("src.charm.os.chmod")
    @patch("src.charm.open", new_callable=unittest.mock.mock_open)
    def test_write_config(self, mock_open, mock_chmod, mock_chown):
        path = "/etc/cinder/nfs-shares"
        data = "172.17.17.61:/srv/test"
        permission = 0o640

        _write_config(data, path)

        mock_open.assert_called_once_with(path, "w+")
        mock_open().write.assert_called_once_with(data)
        mock_chmod.assert_called_once_with(path, permission)
        mock_chown.assert_called_once_with(path, user="root", group="cinder")

    def test_backend_name_in_data(self):
        rel = self.model.get_relation("storage-backend", 0)
        rdata = rel.data[self.model.unit]
        self.assertEqual(rdata["backend_name"], "cinder-nfs")

    @patch("src.charm.shutil.chown")
    @patch("src.charm.os.chmod")
    @patch("src.charm.open", new_callable=unittest.mock.mock_open)
    def test_config_changed(self, mock_open, mock_chmod, mock_chown):
        shares_config = "/tmp/nfs-shares"
        mount_point_base = "/var/lib/cinder/nfsmount"
        mount_options = "vers=4.1,proto=tcp,retry=4"
        mount_attempts = 4
        self.harness.update_config(
            {
                "nfs-shares-config": shares_config,
                "nfs-mount-point-base": mount_point_base,
                "nfs-mount-options": mount_options,
                "nfs-mount-attempts": mount_attempts,
            }
        )
        self.assertEqual(
            self._get_sub_conf(),
            {
                "nfs_shares_config": shares_config,
                "nfs_mount_point_base": mount_point_base,
                "nfs_mount_options": mount_options,
                "nfs_mount_attempts": mount_attempts,
                # default value
                "volume_backend_name": "cinder-nfs",
                "volume_driver": "cinder.volume.drivers.nfs.NfsDriver",
                "nfs_sparsed_volumes": True,
                "nfs_snapshot_support": True,
                "nfs_qcow2_volumes": False,
            },
        )

    def test_blocked_status(self):
        self.harness.update_config(unset=["nfs-shares"])
        self.assertIsInstance(self.harness.charm.unit.status, BlockedStatus)
        message = self.harness.charm.unit.status.message
        self.assertIn("NFS shares not configured", message)

    @patch("src.charm.shutil.chown")
    @patch("src.charm.os.chmod")
    @patch("src.charm.open", new_callable=unittest.mock.mock_open)
    def test_volume_backend_name_config(self, mock_open, mock_chmod,
                                        mock_chown):
        self.assertEqual(self._get_sub_conf().get("volume_backend_name"),
                         "cinder-nfs")

        self.harness.update_config(
            {
                "volume-backend-name": "test-backend",
            }
        )
        self.assertEqual(
            self._get_sub_conf().get("volume_backend_name"), "test-backend"
        )
