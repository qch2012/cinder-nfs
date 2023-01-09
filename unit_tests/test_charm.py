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
import json

from ops.model import Relation, BlockedStatus, ActiveStatus
from ops.testing import Harness
from src.charm import CharmCinderNFSCharm


class TestCharm(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.harness = Harness(CharmCinderNFSCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()
        self.harness.set_leader(True)
        self.model = self.harness.model
        self.storage_backend = self.harness.add_relation("storage-backend", "cinder")
        self.harness.add_relation_unit(self.storage_backend, "cinder/0")
        self.harness.update_config(
            {
                "volume-backend-name": "cinder-nfs",
                "nfs-shares": "172.18.18.61:/srv/test",
                "nfs-mount-point-base": "/var/lib/cinder/nfs",
                "nfs-mount-options": "vers=3",
                "nfs-mount-attempts": 3,
            }
        )

    def _get_sub_conf(self):
        rel = self.model.get_relation("storage-backend", 0)
        self.assertIsInstance(rel, Relation)
        rdata = rel.data[self.model.unit]
        rdata = json.loads(rdata["subordinate_configuration"])
        return dict(
            rdata["cinder"]["/etc/cinder/cinder.conf"]["sections"]["cinder-nfs"]
        )

    def test_backend_name_in_data(self):
        rel = self.model.get_relation("storage-backend", 0)
        rdata = rel.data[self.model.unit]
        self.assertEqual(rdata["backend_name"], "cinder-nfs")

    def test_config_changed(self):
        self.harness.update_config(
            {
                "nfs-mount-point-base": "/var/lib/cinder/nfsmount",
                "nfs-mount-options": "vers=4.1,proto=tcp,retry=4,",
                "nfs-mount-attempts": 4,
            }
        )
        self.assertEqual(
            self._get_sub_conf(),
            {
                "volume_driver": "cinder.volume.drivers.nfs.NfsDriver",
                "nfs_mount_point_base": "/var/lib/cinder/nfsmount",
                "nfs_mount_options": "vers=4.1,proto=tcp,retry=4,",
                "nfs_mount_attempts": 4,
            },
        )

    def test_blocked_status(self):
        self.harness.update_config(unset=["nfs-shares"])
        self.assertIsInstance(self.harness.charm.unit.status, BlockedStatus)
        message = self.harness.charm.unit.status.message
        self.assertIn("NFS shares not configured", message)

    def test_status_with_mandatory_config(self):
        self.assertEqual(self.harness.charm.unit.status.message, "Unit is ready")
        self.assertIsInstance(self.harness.charm.unit.status, ActiveStatus)
        self.harness.update_config(
            unset=["nfs-shares-config"],
        )
        self.assertEqual(
            self.harness.charm.unit.status.message,
            "Missing option(s): nfs-shares-config",
        )
        self.assertIsInstance(self.harness.charm.unit.status, BlockedStatus)

    def test_volume_backend_name_config(self):
        self.assertEqual(self._get_sub_conf().get("volume_backend_name"), "cinder-nfs")

        self.harness.update_config(
            {
                "volume-backend-name": "test-backend",
            }
        )
        self.assertEqual(
            self._get_sub_conf().get("volume_backend_name"), "test-backend"
        )
