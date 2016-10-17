import socket
import subprocess

import charmhelpers.core.hookenv as hookenv
import charmhelpers.contrib.network.ip as ch_ip
import charms_openstack.charm
# import charms_openstack.sdn.odl as odl
# import charms_openstack.sdn.ovs as ovs


class {{ charm_class }}(charms_openstack.charm.OpenStackCharm):

    # Internal name of charm
    service_name = name = '{{ metadata.package }}'

    # First release supported
    release = '{{ release }}'

    # List of packages to install for this charm
    packages = {{ packages }}
