**WARNING**: This repository is outedated and has moved to 
* https://opendev.org/openstack/charm-cinder-nfs



# Overview

The cinder charm is the Openstack block storage (i.e: Volume) service, whereas the cinder-nfs charm works as a subordinate of cinder, implementing a NFS backend.

# Usage

## Configuration

This section covers common and/or important configuration options. See file `config.yaml` for the full list of options, along with their descriptions and default values.

### `nfs-shares`

A list of nfs shares that NFS driver should attempt to provision new Cinder volumes into

Multiple nfs shares can be provided, each on its own line, in a format of `<host>:<share path>`
```
  192.168.1.200:/storage
  192.168.1.201:/storage
```

The content will be written to /etc/cinder/nfs_shares by default or the file specified in nfs-shares-config option

### `nfs-shares-config`

The file that contain a list of NFS shares.  Cinder-volume will read this file to get its NFS backend detail


### `nfs-mount-options`

Specify mount options. See section of the NFS man page for details.


## Deployment

This charm's primary use is as a backend for the cinder charm. To do so, add a relation betweeen both charms:

```
  juju add-relation cinder-nfs:storage-backend cinder:storage-backend
```

# Developing

Create and activate a virtualenv with the development requirements:
```
  virtualenv -p python3 venv
  source venv/bin/activate
  pip3 install -r requirements.txt
  pip3 install -r test-requirements.txt
```

# Documentation

The OpenStack Charms project maintains two documentation guides:

* [OpenStack Charm Guide][cg]: for project information, including development
  and support notes
* [OpenStack Charms Deployment Guide][cdg]: for charm usage information

# Bugs

Please report bugs on [Launchpad][lp-bugs-charm-cinder-netapp].

[cg]: https://docs.openstack.org/charm-guide
[cdg]: https://docs.openstack.org/project-deploy-guide/charm-deployment-guide
[lp-bugs-charm-cinder-netapp]: https://bugs.launchpad.net/charm-cinder-nfs/+filebug
