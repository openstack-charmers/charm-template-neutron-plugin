# Neutron Plugin Charm

This template is designed to help in writing a charm which configures an
SDN provider on a unit. This charm is a
[subordinate charm](https://jujucharms.com/docs/2.0/authors-subordinate-services)
and would normally be related to the
[nova-compute](https://github.com/openstack/charm-nova-compute) application via
the
[neutron-plugin interface](https://github.com/openstack/charm-interface-neutron-plugin).

# Charm Preperation

The first step in writing the charm is think about which applications the charm
needs to relate to for it to be fully configured eg The charm may need to
relate to the message bus, database or identity service. A full list of
interfaces can be found [here](http://interfaces.juju.solutions/).

# Writing the charm

This template uses the [reactive framework](https://pythonhosted.org/charms.reactive/)
for charms. An excellent introduction on the reactive framework and building
charms from layers can be found
[here](https://jujucharms.com/docs/devel/authors-charm-building)

## layers.yaml

The **layers.yaml** file defines what layers and interfaces will be imported
and included in the charm when the charm is built. The template is configured
to pull in the [Openstack Layer](https://github.com/openstack/charm-layer-openstack)
and the [neutron-plugin interface](https://github.com/openstack/charm-interface-neutron-plugin)

The Openstack layer includes templates and also template fragments which can
be used inside this charms templates. These cover the common configuration
syntax for  sections e.g. [oslo\_messaging\_rabbit], [database],
[keystone\authtoken] etc

The Openstack layer also pulls in the
[charms.openstack](https://github.com/openstack/charms.openstack) package. This
provides most of the classes and methods used to handle the charms hooks events
and the configuration of the service.

If additional interfaces or layers are needed edit **layers.yaml** and add them
to the **includes** list.

## config.yaml

The config.yaml defines what configuration option can be configured at charm
runtime. The options set here are available to any templates eg if the
config.yaml incudes a **foo** option the value of that option can be rendered
inside a template by including ``{{ options.foo }}`` in a template.

## metadata.yaml

The charm
[metadata.yaml](https://jujucharms.com/docs/2.0/authors-charm-metadata)
describes the charm and how it relates to other charms. This must be updated to
refelct the charm being written.

## Charm Class

The **src/lib/charm/openstack/sdn\_charm.py** file contains a class which
should be used to define some of the attributes of this application like charm
name, the earliest OpenStack release this charm can be used with (defaults to
Essex!) and the packages that should be installed for this charm. Its good
practise to rename the class to reflect the name of the application being
installed and rename the **sdn\_charm.py** file. At this point
the charm could be built, deployed and related to a principle charm and the
default handlers would install the packages listed in the SDN charm class.

```
class SDNCharm(charms_openstack.charm.OpenStackCharm):

    # Internal name of charm
    service_name = name = 'sdn'

    # First release supported
    release = 'liberty'

    # List of packages to install for this charm
    packages = ['sdn-pkg']

```

If configure\_foo() should only be run once then the handler can emit a new
state and the running of configure\_foo gated on the state not being present

## Adding a new handler

Once the packages are installed it is likely that additional configuration is
needed e.g. rendering config, configuring bridges or updating remote services
via their interfaces. To perform an action once the initial package
installation has been done a handler needs to be added to listen for the
**charm.install** event. To do this edit
**src/reactive/sdn\_charm\_handlers.py** and add the reactive handler:

```
@reactive.when('charm.installed')
def configure_foo():
    with charm.provide_charm_instance() as sdn_charm:
        sdn_charm.configure_foo()
```

Now add the **configure\_foo** class to the charm class definition in
**src/lib/charm/openstack/sdn\_charm.py**

```
class SDNCharm(charms_openstack.charm.OpenStackCharm):

    # Internal name of charm
    service_name = name = 'sdn'

    # First release supported
    release = 'liberty'

    # List of packages to install for this charm
    packages = ['sdn-pkg']

    def configure_foo(self):
        ...

```

If configure\_foo() should only be run once then the handler can emit a new
state and the running of configure\_foo gated on the state not being present
e.g.


```
@reactive.when_not('foo.configured')
@reactive.when('charm.installed')
def configure_foo():
    with charm.provide_charm_instance() as sdn_charm:
        sdn_charm.configure_foo()
    reactive.set_state('foo.configured')
```

## Template properties from Interfaces

By default some interfaces are automatically allocated a namespace within the
template context. Those namespaces are also automatically populated with some
options directly from the interface. For example if a charm is related to
Keystones
[keystone interface](https://github.com/openstack/charm-interface-keystone)
then a number of **service\_** variables are set in the
identity\_service namespace. So, charm template could contain the following to
access those variables:

```
[keystone_authtoken]
auth_uri = {{ identity_service.service_protocol }}://{{ identity_service.service_host }}:{{ identity_service.service_port }}
auth_url = {{ identity_service.auth_protocol }}://{{ identity_service.auth_host }}:{{ identity_service.auth_port }}
```

See the **auto\_accessors** list in
[charm-interface-keystone](https://github.com/openstack/charm-interface-keystone/blob/master/requires.py)
for a complete list

## Template properties from Adapters

Adapters are used to take the data from an interface and create new variables
in the template context. For example the **RabbitMQRelationAdapter** (which can
be found in the
[adapters.py](https://github.com/openstack/charms.openstack/blob/master/charms_openstack/adapters.py)
from charms.openstack.) adds an **ssl\_ca\_file** variable to the amqp
namespace. This setting is really independant of the interface with rabbit but
should be consistant accross the OpenStack deployment. This variable can then
be accessed in the same way as the rest of the amqp setting ```{{ amqp.ssl_ca_file }}```

## Template properties from user config

The settings exposed to the user via the config.yaml are added to the
**options** namespace.  The value the user has set for option  **foo** can be
retrieved inside a template by including ``{{ options.foo }}``

## Adding a new setting derived from config

It is useful to be able to set a property based on examining multiple config
options or examining other aspects of the runtime system. The
**charms_openstack.adapters.config_property** decorator can be used to achieve
this. In the example below if the user has set the boolean config option
**angry** to **True** and set the **radiation** string config option to
**gamma** then the **hulk_mode** property is set to True.

```
@charms_openstack.adapters.config_property
def hulk_mode(config):
    if config.angry and config.radiation =='gamma':
        return True
    else:
        return False
```

This can be accessed in the templates with ```{{ options.hulk_mode }}```

## Adding a new setting to an interface

It is useful to be able to set a property based on the settings retrieved from
an interface. In the example below the charm sets a pipeline based on the
Keystone API version advertised by the keystone interface,

```
@charms_openstack.adapters.adapter_property('identity_service')
def charm_pipeline(keystone):
    return {
        "2": "cors keystone_authtoken context apiapp",
        "3": "cors keystone_v3_authtoken context apiapp",
        "none": "cors unauthenticated-context apiapp"
    }[keystone.api_version]
```

This can be accessed in the templates with ```{{ identity_service.charm_pipeline }}```

## Sending data to remote application

Some interfaces are used to send as well as recieve data. The interface will
expose a methode for sending data to a remote application if it is supported.
For example the [neutron-plugin interface](https://github.com/openstack/charm-interface-neutron-plugin)
can be used to send configuration to the principle charm.

The handler below waits for the neutron-plugin relation with the principle to
be complete at which point the **neutron-plugin.connected** state will be set
which will fire this trigger. An instance of the interface is passed by the
decorator to the **configure_neutron_plugin** method. This is inturn passed to
the **configure_neutron_plugin** method in the charm class.

```
@reactive.when('neutron-plugin.connected')
def configure_neutron_plugin(neutron_plugin):
    with charm.provide_charm_instance() as sdn_charm:
        sdn_charm.configure_neutron_plugin(neutron_plugin)
```

In the charm class the instance of the interface is used to update the
principle

```
    def configure_neutron_plugin(self, neutron_plugin):
        neutron_plugin.configure_plugin(
            plugin='mysdn',
            config={
                "nova-compute": {
                    "/etc/nova/nova.conf": {
                        "sections": {
                            'DEFAULT': [
                                ('firewall_driver',
                                 'nova.virt.firewall.'
                                 'NoopFirewallDriver'),
                                ('libvirt_vif_driver',
                                 'nova.virt.libvirt.vif.'
                                 'LibvirtGenericVIFDriver'),
                                ('security_group_api', 'neutron'),
                            ],
                        }
                    }
                }
            })
```

On recieving this data from the neutron_plugin relation the principle will add
the requested config into **/etc/nova/nova.conf**

## README.md

Update the **src/README.md** with information on how to deploy and configure
the charm and where to file bugs.

## Unit Tests

Unit tests should be added to the **unit_tests** folder. There are some helpers
for writing these in charms.openstack

## Functional Tests

Functinal tests are currently written in Amulet which requires Juju 1.X at the
present.

# Example Charm

The [openvswitch-odl](https://github.com/openstack/charm-openvswitch-odl) is a
good example of a charm which plugs into nova-compute via the neutron-plugin
relation
