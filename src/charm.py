#!/usr/bin/env python3
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

"""Charm for deploying and maintaining the Cinder NFS backend driver."""

from ops.main import main
from ops.model import ActiveStatus, BlockedStatus
from ops_openstack.plugins.classes import CinderStoragePluginCharm

import os
import io
import shutil


def _check_config(charm_config):
    """
    These checks are in addition to the parent class checks
    for MANDATORY_CONFIG.
    """
    if not charm_config["nfs-shares"]:
        return BlockedStatus("NFS shares not configured")

    return ActiveStatus("Unit is ready")


class CharmCinderNFSCharm(CinderStoragePluginCharm):
    """Charm the Cinder NFS driver."""

    PACKAGES = ["cinder-common"]

    MANDATORY_CONFIG = [
        "nfs-shares",
        "nfs-shares-config",
        "volume-backend-name",
        "nfs-mount-point-base",
        "nfs-mount-attempts",
        "nfs-snapshot-support",
        "nfs-qcow2-volumes",
        "nfs-sparsed-volumes",
    ]

    def on_config(self, event):
        status = _check_config(self.framework.model.config)
        if not isinstance(status, ActiveStatus):
            self.unit.status = status
            return

        super().on_config(event)

    def cinder_configuration(self, charm_config):
        options = []
        nfs_shares = ""

        volumedriver = "cinder.volume.drivers.nfs.NfsDriver"
        options.append(("volume_driver", volumedriver))

        for key, value in charm_config.items():
            # if volume-backend-name is empty, set to application name
            if key == "volume-backend-name" and not value:
                value = self.framework.model.app.name

            if key == "nfs-shares":
                nfs_shares = os.linesep.join([s for s in value.splitlines() if s])
                buff = io.StringIO(nfs_shares)
                continue

            if key == "nfs-shares-config":
                path = value
                with open(path, "w+") as f:
                    print(buff.getvalue(), file=f)
                os.chmod(path, 0o640)
                shutil.chown(path, user="root", group="cinder")

            options.append((key.replace("-", "_"), value))

        return options


if __name__ == "__main__":
    main(CharmCinderNFSCharm)
