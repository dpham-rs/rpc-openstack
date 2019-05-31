#!/usr/bin/env python
# Copyright 2014, Rackspace US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# (c) 2014, Kevin Carter <kevin.carter@rackspace.com>
# Fork by David Pham <david.pham@rackspace.com>
# Yet again, completely buchered by Jonathan <jonathan.almaleh@rackspace.com>
# v5.4

import argparse
import json
import os
import netaddr

os.system ('clear')

print 'Hello, human'
print 'Welcome to the RPC "Leapfrog" ugrade script'
print 'For this you will need the f5 Administrative partition name used in the Openstack deployment.'
print 'Please get that information now...'

PART = 'RPC'
PREFIX_NAME = 'RPC'

print 'The current partition name is %s.' % PART
print 'Please enter the ACTUAL partition name or just hit enter to continue'
PART = raw_input ("/>")
if len(PART) == 0:
    print('the input is empty')
    print('defaulting to value RPC')
    PART = 'RPC'

ADDTCPMON = (
    # Adds TCP MONITORS to exisiting Pools
    r'modify ltm pool /' + PART + '/' + PREFIX_NAME + '_POOL_CINDER_API' + ' { monitor tcp }',
    r'modify ltm pool /' + PART + '/' + PREFIX_NAME + '_POOL_NOVA_API_OS_COMPUTE' + ' { monitor tcp }',
    r'modify ltm pool /' + PART + '/' + PREFIX_NAME + '_POOL_NEUTRON_SERVER' + ' { monitor tcp }',
    r'modify ltm pool /' + PART + '/' + PREFIX_NAME + '_POOL_KEYSTONE_SERVICE' + ' { monitor tcp }',
    r'modify ltm pool /' + PART + '/' + PREFIX_NAME + '_POOL_GLANCE_API' + ' { monitor tcp }',
    r'modify ltm pool /' + PART + '/' + PREFIX_NAME + '_POOL_GLANCE_REGISTRY' + ' { monitor tcp }',
    r'modify ltm pool /' + PART + '/' + PREFIX_NAME + '_POOL_HEAT_API' + ' { monitor tcp }',
    r'modify ltm pool /' + PART + '/' + PREFIX_NAME + '_POOL_SWIFT' + ' { monitor tcp }''\n'
    r'modify ltm pool /' + PART + '/' + PREFIX_NAME + '_POOL_HORIZON' + ' { monitor tcp }',
    r'modify ltm pool /' + PART + '/' + PREFIX_NAME + '_POOL_HORIZON_SSL' + ' { monitor tcp }''\n'
)

ADDNEWMON = (
    # Adds PROPER EXTERNAL and HTTP MONITOR NEWTON to exisiting Pools
    r'modify ltm pool /' + PART + '/' + PREFIX_NAME + '_POOL_CINDER_API' + ' { monitor ' + PREFIX_NAME + '-MON-EXT-ENDPOINT-NEWTON }',
    r'modify ltm pool /' + PART + '/' + PREFIX_NAME + '_POOL_NOVA_API_OS_COMPUTE' + ' { monitor ' + PREFIX_NAME + '-MON-EXT-ENDPOINT-NEWTON }',
    r'modify ltm pool /' + PART + '/' + PREFIX_NAME + '_POOL_NEUTRON_SERVER' + ' { monitor ' + PREFIX_NAME + '-MON-EXT-ENDPOINT-NEWTON }',
    r'modify ltm pool /' + PART + '/' + PREFIX_NAME + '_POOL_KEYSTONE_SERVICE' + ' { monitor ' + PREFIX_NAME + '-MON-EXT-ENDPOINT-NEWTON }',
    r'modify ltm pool /' + PART + '/' + PREFIX_NAME + '_POOL_GLANCE_API' + ' { monitor ' + PREFIX_NAME + '-MON-EXT-ENDPOINT-NEWTON }',
    r'modify ltm pool /' + PART + '/' + PREFIX_NAME + '_POOL_GLANCE_REGISTRY' + ' { monitor ' + PREFIX_NAME + '-MON-EXT-ENDPOINT-NEWTON }',
    r'modify ltm pool /' + PART + '/' + PREFIX_NAME + '_POOL_HEAT_API' + ' { monitor ' + PREFIX_NAME + '-MON-EXT-ENDPOINT-NEWTON }',
    r'modify ltm pool /' + PART + '/' + PREFIX_NAME + '_POOL_SWIFT' + ' { monitor ' + PREFIX_NAME + '-MON-EXT-ENDPOINT-NEWTON }',
    r'modify ltm pool /' + PART + '/' + PREFIX_NAME + '_POOL_HORIZON' + ' { monitor ' + PREFIX_NAME + '_MON_HTTP_HORIZON }',
    r'modify ltm pool /' + PART + '/' + PREFIX_NAME + '_POOL_HORIZON_SSL' + ' { monitor ' + PREFIX_NAME + '_MON_HTTP_HORIZON }'
)

MODMONS = [
### Modifications to existing monitores for POST Maintenance
    r'modify ltm monitor http /' + PART + '/' + PREFIX_NAME +
    '_MON_HTTP_HORIZON { recv "200 OK" send "HEAD /auth/login/ HTTP/1.1\\r\\nHost: rpc\\r\\n\\r\\n" }'
#D    '\n'
]

MONITORS = [
# NEW monitors for PRE Maint.
    r'create ltm monitor http /' + PART + '/' + PREFIX_NAME +
    '_MON_HTTP_NOVA_NOVNC_CONSOLE {'
    r' defaults-from http destination *:6080 recv "200 OK"' +
    ' send "HEAD /vnc_auto.html'
    r' HTTP/1.1\r\nHost: rpc\r\n\r\n" }',

    r'create ltm monitor http /' + PART + '/' + PREFIX_NAME +
    '_MON_HTTP_REPO_CACHE {'
    r' defaults-from http destination *:3142 recv "200 OK"' +
    ' send "HEAD /acng-report.html'
    r' HTTP/1.1\r\nHost: rpc\r\n\r\n" }',

    r'create ltm monitor tcp /' + PART + '/' + PREFIX_NAME +
    '_MON_TCP_REPO_GIT {'
    r' defaults-from tcp destination *:9418 }'
]

NEWTON_EXT_MON = [
        '   --> Upload External monitor file to disk <--',
        '       run util bash',
        '       curl -k -o /config/monitors/RPC-MON-EXT-ENDPOINT-NEWTON.monitor https://raw.githubusercontent.com/dpham-rs/rpc-openstack/master/scripts/f5-monitor-newton.sh',
        '       exit',

        '       create sys file external-monitor /' + PART + '/RPC-MON-EXT-ENDPOINT-NEWTON { source-path file:///config/monitors/RPC-MON-EXT-ENDPOINT-NEWTON.monitor }',
        '       save sys config',
        '       create ltm monitor external /' + PART + '/RPC-MON-EXT-ENDPOINT-NEWTON { interval 20 timeout 61 run /' + PART + '/RPC-MON-EXT-ENDPOINT-NEWTON }\n'
        '   --> UDPATE External monitor VARIABLES!!! <--',
]

NODES = (
    'create ltm node /' + PART +
    '/%(node_name)s { address %(container_address)s }'
)

SNAT_IDLE = (
    'modify ltm snat-translation /' + PART + '/%s { ip-idle-timeout 3600 }'
)

PRIORITY_ENTRY = '{ priority-group %(priority_int)s }'

POOL_NODE = {
    'beginning': 'create ltm pool /' + PART + '/%(pool_name)s {'
    ' load-balancing-mode least-connections-node members replace-all-with'
    ' { %(nodes)s }',
    'priority': 'min-active-members 1',
    'service-reset': 'service-down-action reset slow-ramp-time 0',
    'end': 'monitor %(mon_type)s }'
}

MODPOOL_NODE = {
    'beginning': 'modify ltm pool /' + PART + '/%(pool_name)s {'
    ' load-balancing-mode least-connections-node members replace-all-with'
    ' { %(nodes)s }',
    'priority': 'min-active-members 1',
    'service-reset': 'service-down-action reset slow-ramp-time 0',
    'end': 'monitor %(mon_type)s }'
}

VIRTUAL_ENTRIES_PARTS = {
    'command': 'create ltm virtual /' + PART + '/%(vs_name)s',
}

PERSIST_OPTION = 'persist replace-all-with { /' + PART + '/' + PREFIX_NAME + '_PROF_PERSIST_IP }'


END_COMMANDS = [
    'save sys config',
    'run cm config-sync to-group SYNC-FAILOVER'
]

VIRTUAL_ENTRIES = (
    'create ltm virtual /' + PART + '/%(vs_name)s {'
    ' destination %(internal_lb_vip_address)s:%(port)s'
    ' ip-protocol tcp mask 255.255.255.255'
    ' pool /' + PART + '/%(pool_name)s'
    r' profiles replace-all-with { /Common/fastL4 { } }'
    ' %(persist)s'
    ' %(mirror_status)s'
    ' source-address-translation { pool /' + PART + '/' + PREFIX_NAME + '_SNATPOOL type snat }'
    ' }'
)

PUB_SSL_VIRTUAL_ENTRIES = (
    'create ltm virtual /' + PART + '/%(vs_name)s {'
    ' destination %(ssl_public_ip)s:%(port)s ip-protocol tcp'
    ' pool /' + PART + '/%(pool_name)s'
    r' profiles replace-all-with { /Common/tcp { } %(ltm_profiles)s }'
    ' %(persist)s'
    ' source-address-translation { pool /' + PART + '/' + PREFIX_NAME + '_SNATPOOL type snat }'
    ' }'
)

PRI_SSL_VIRTUAL_ENTRIES = (
    'create ltm virtual /' + PART + '/%(vs_name)s {'
    ' destination %(internal_lb_vip_address)s:%(port)s ip-protocol tcp'
    ' pool /' + PART + '/%(pool_name)s'
    r' profiles replace-all-with { /Common/tcp { } %(ltm_profiles)s }'
    ' %(persist)s'
    ' source-address-translation { pool /' + PART + '/' + PREFIX_NAME + '_SNATPOOL type snat }'
    ' }'
)

PUB_NONSSL_VIRTUAL_ENTRIES = (
    'create ltm virtual /' + PART + '/%(vs_name)s {'
    ' destination %(ssl_public_ip)s:%(port)s ip-protocol tcp'
    ' pool /' + PART + '/%(pool_name)s'
    r' profiles replace-all-with { /Common/fastL4 { } }'
    ' %(persist)s'
    ' source-address-translation { pool /' + PART + '/' + PREFIX_NAME + '_SNATPOOL type snat }'
    ' }'
)

MOD_VIRTUALS = [
    'modify ltm virtual ' + '/' + PART + '/' + PREFIX_NAME + '_VS_HORIZON_SSL '
    '{ profiles replace-all-with '
    '{ /Common/tcp { } '
    '/' + PART + '/' + PREFIX_NAME + '_X-FORWARDED-PROTO { } '
    '/' + PART + '/' + PREFIX_NAME + '_PROF_SSL_%(ssl_domain_name)s { context clientside  } } }',
    'modify ltm virtual ' + '/' + PART + '/' + PREFIX_NAME + '_PUB_SSL_VS_HORIZON_SSL '
    '{ profiles replace-all-with '
    '{ /Common/tcp { } '
    '/' + PART + '/' + PREFIX_NAME + '_X-FORWARDED-PROTO { } '
    '/' + PART + '/' + PREFIX_NAME + '_PROF_SSL_%(ssl_domain_name)s { context clientside  } } }',
    'modify ltm virtual ' + '/' + PART + '/' + PREFIX_NAME + '_VS_GALERA { mirror enabled } '
]

CLEANUP = [
    'delete ltm virtual ' + '/' + PART + '/' + PREFIX_NAME + '_PUB_VS_NOVA_SPICE_CONSOLE',
    'delete ltm virtual ' + '/' + PART + '/' + PREFIX_NAME + '_VS_NOVA_SPICE_CONSOLE',
    'delete ltm pool ' + '/' + PART + '/' + PREFIX_NAME + '_POOL_NOVA_SPICE_CONSOLE'
]

POOL_PARTS = {
        'galera_read': {
        'port': 3307,
        'backend_port': 3306,
        'mon_type': '/' + PART + '/' + PREFIX_NAME + '_MON_GALERA',
        'priority': False,
        'group': 'galera',
        'connection-mirror': True,
        'hosts': []
    },
        'nova_novnc_console': {
        'port': 6080,
        'backend_port': 6080,
        'mon_type': '/' + PART + '/' + PREFIX_NAME + '_MON_HTTP_NOVA_NOVNC_CONSOLE',
        'group': 'nova_console',
        'hosts': [],
        'make_public': True,
        'persist': True
    },
        'repo_cache': {
        'port': 3142,
        'backend_port': 3142,
        'mon_type': '/' + PART + '/' + PREFIX_NAME + '_MON_HTTP_REPO_CACHE',
        'group': 'repo_all',
        'priority': True,
        'hosts': []
    },
        'repo_git': {
        'port': 9418,
        'backend_port': 9418,
        'mon_type': '/' + PART + '/' + PREFIX_NAME + '_MON_TCP_REPO_GIT',
        'group': 'pkg_repo',
        'hosts': []
    }
}

MODPOOL_PARTS = {
    'horizon_ssl': {
        'port': 443,
        'backend_port': 80,
        'mon_type': '/' + PART + '/' + PREFIX_NAME + '_MON_HTTP_HORIZON',
        'group': 'horizon',
        'hosts': [],
        'make_public': True,
        'ssl_private': True,
        'persist': True,
        'x-forwarded-proto': True
    },
        'galera': {
        'port': 3306,
        'backend_port': 3306,
        'mon_type': '/' + PART + '/' + PREFIX_NAME + '_MON_GALERA',
        'priority': True,
        'group': 'galera',
        'service-reset': True,
        'connection-mirror': True,
        'hosts': []
    }
}

def recursive_host_get(inventory, group_name, host_dict=None):
    if host_dict is None:
        host_dict = {}

    inventory_group = inventory.get(group_name)
    if not inventory_group:
        print('Inventory group "%s" not found, skipping.' % group_name)
        return host_dict

    if 'children' in inventory_group and inventory_group['children']:
        for child in inventory_group['children']:
            recursive_host_get(
                inventory=inventory, group_name=child, host_dict=host_dict
            )

    if inventory_group.get('hosts'):
        for host in inventory_group['hosts']:
            if host not in host_dict['hosts']:
                ca = inventory['_meta']['hostvars'][host]['container_address']
                node = {
                    'hostname': host,
                    'container_address': ca
                }
                host_dict['hosts'].append(node)

    return host_dict


def build_pool_parts(inventory):
    for key, value in POOL_PARTS.iteritems():
        recursive_host_get(
            inventory, group_name=value['group'], host_dict=value
        )

    return POOL_PARTS

def build_modpool_parts(inventory):
    for key, value in MODPOOL_PARTS.iteritems():
        recursive_host_get(
            inventory, group_name=value['group'], host_dict=value
        )

    return MODPOOL_PARTS

def file_find(filename, user_file=None, pass_exception=False):
    """Return the path to a file.

    If no file is found the system will exit.
    The file lookup will be done in the following directories:
      /etc/openstack_deploy/
      $HOME/openstack_deploy/
      $(pwd)/openstack_deploy/

    :param filename: ``str``  Name of the file to find
    :param user_file: ``str`` Additional localtion to look in FIRST for a file
    """
    file_check = [
        os.path.join(
            '/etc', 'openstack_deploy', filename
        ),
        os.path.join(
            os.environ.get('HOME'), 'openstack_deploy', filename
        ),
        os.path.join(
            os.getcwd(), filename
        )
    ]

    if user_file is not None:
        file_check.insert(0, os.path.expanduser(user_file))

    for f in file_check:
        if os.path.isfile(f):
            return f
    else:
        if pass_exception is False:
            raise SystemExit('No file found at: %s' % file_check)
        else:
            return False


def args():
    """Setup argument Parsing."""
    parser = argparse.ArgumentParser(
        usage='%(prog)s',
        description='Rackspace Openstack, Inventory Generator',
        epilog='Inventory Generator Licensed "Apache 2.0"')

    parser.add_argument(
        '-f',
        '--file',
        help='Inventory file. Default: [ %(default)s ]',
        required=False,
        default='openstack_inventory.json'
    )

    parser.add_argument(
        '-s',
        '--snat-pool-address',
        help='LB Main SNAT pool address for [ RPC_SNATPOOL ], for'
             ' multiple snat pool addresses comma seperate the ip'
             ' addresses. By default this IP will be .15 from within your'
             ' containers_cidr as found within inventory.',
        required=False,
        default=None
    )

    parser.add_argument(
        '--ssl-public-ip',
        help='Public IP address for the F5 to use.',
        required=False,
        default=None
    )

    parser.add_argument(
        '--ssl-domain-name',
        help='Name of the domain that will have an ssl cert.',
        required=True,
        default=None
    )

    parser.add_argument(
        '--sec-host-network',
        help='Security host network in CIDR format.'
             ' EXAMPLE: "192.168.1.0/24"',
        required=False,
        default=None
    )

    parser.add_argument(
        '--sec-container-network',
        help='Security container network in CIDR format.'
             ' EXAMPLE: "192.168.2.1/24',
        required=False,
        default=None
    )

    parser.add_argument(
        '--sec-public-vlan-name',
        help='Security container network address and netmask.'
             ' EXAMPLE: "FW-LB"',
        required=False,
        default=None
    )

    parser.add_argument(
        '--galera-monitor-user',
        help='Name of the user that will be available for the F5 to pull when'
             ' monitoring Galera.',
        required=False,
        default='openstack'
    )

    parser.add_argument(
        '--print',
        help='Print the script to screen, as well as write it out',
        required=False,
        default=False,
        action='store_true'
    )

    parser.add_argument(
        '-e',
        '--export',
        help='Export the generated F5 configuration script.'
             ' Default: [ %(default)s ]',
        required=False,
        default=os.path.join(
            os.path.expanduser('~/'), 'rpc_f5_config.sh'
        )
    )

    parser.add_argument(
        '--afm',
        help='Pass this argument if the f5 environment is using the Advanced Firewall Module.'
             'Adding this flag will create the required rules to open up the API to ALL SOURCES.'
             'It will also create a rule to block communication from the Provider Network to the Host network.',
        required=False,
        default=False,
        action='store_true'
    )

    parser.add_argument(
        '-S',
        '--Superman',
        help='Yes, its Superman ... strange visitor from another planet,'
             'who came to Earth with powers and abilities far beyond those of mortal men!  '
             'Superman ... who can change the course of mighty rivers, bend steel in his bare hands,'
             'and who, disguised as Clark Kent, mild-mannered reporter for a great metropolitan newspaper,'
             'fights a never-ending battle for truth, justice, and the American way!',
        required=False,
        default=False,
        action='store_true'
    )

    return vars(parser.parse_args())

def main():
    """Run the main application."""
    # Parse user args
    user_args = args()

    # Get the contents of the system environment json
    environment_file = file_find(filename=user_args['file'])
    with open(environment_file, 'rb') as f:
        inventory_json = json.loads(f.read())

    commands = []
    nodes = []
    pools = []
    modpools = []
    virts = []
    sslvirts = []
    pubvirts = []
    cleanup = []
    addnewmon = []

    if user_args['Superman']:
        print "       **************************       "
        print "    .*##*:*####***:::**###*:######*.    "
        print "   *##: .###*            *######:,##*   "
        print " *##:  :####:             *####*.  :##: "
        print "  *##,:########**********:,       :##:  "
        print "   .#########################*,  *#*    "
        print "     *#########################*##:     "
        print "       *##,        ..,,::**#####:       "
        print "        ,##*,*****,        *##*         "
        print "          *#########*########:          "
        print "            *##*:*******###*            "
        print "             .##*.    ,##*              "
        print "               :##*  *##,               "
        print "                 *####:                 "
        print "                   :,                   "
#       Kal-El
#       SUPERMAN
#       JNA
##########################################
    pool_parts = build_pool_parts(inventory=inventory_json)
    lb_vip_address = inventory_json['all']['vars']['internal_lb_vip_address']
    for key, value in pool_parts.iteritems():
        value['group_name'] = key.upper()
        value['vs_name'] = '%s_VS_%s' % (
            PREFIX_NAME, value['group_name']
        )
        value['pool_name'] = '%s_POOL_%s' % (
            PREFIX_NAME, value['group_name']
        )

        node_data = []
        priority = 100
        for node in value['hosts']:
            node['node_name'] = '%s_NODE_%s' % (PREFIX_NAME, node['hostname'])
            nodes.append(NODES % node)
            if value.get('persist'):
                persist = PERSIST_OPTION
            else:
                persist = str()
            if value.get('connection-mirror'):
                mirror_state = 'mirror enabled'
            else:
                mirror_state = str()

            virtual_dict = {
                'port': value['port'],
                'mirror_status': mirror_state,
                'vs_name': value['vs_name'],
                'pool_name': value['pool_name'],
                'internal_lb_vip_address': lb_vip_address,
                'persist': persist,
                'ssl_domain_name': user_args['ssl_domain_name'],
                'ssl_public_ip': user_args['ssl_public_ip'],
            }
            if not value.get('ssl_private'):
                virt = '%s' % VIRTUAL_ENTRIES % virtual_dict
                if virt not in virts:
                    virts.append(virt)
            if value.get('ssl_private'):
                virtual_dict['ltm_profiles'] = '/' + PART + '/' + PREFIX_NAME + '_X-FORWARDED-PROTO { } /' + PART + '/' + PREFIX_NAME + '_PROF_SSL_%(ssl_domain_name)s { context clientside }'% user_args
                'RPC_PRI_SSL', value['group_name']
                prisslvirt = '%s' % PRI_SSL_VIRTUAL_ENTRIES % virtual_dict
                if prisslvirt not in prisslvirts:
                    prisslvirts.append(prisslvirt)

            if user_args['ssl_public_ip']:
                if not value.get('backend_ssl'):
                    virtual_dict['ltm_profiles'] = (
                        '/' + PART + '/' + PREFIX_NAME + '_PROF_SSL_%(ssl_domain_name)s { context clientside }'
                    ) % user_args
                    if value.get ('x-forwarded-proto'):
                        virtual_dict['ltm_profiles'] = '/' + PART + '/' + PREFIX_NAME + '_X-FORWARDED-PROTO { } /' + PART + '/' + PREFIX_NAME + '_PROF_SSL_%(ssl_domain_name)s { context clientside }'% user_args
                else:
                    virtual_dict['ltm_profiles'] = '/' + PART + '/' + PREFIX_NAME + '_PROF_SSL_SERVER { context serverside } /' + PART + '/' + PREFIX_NAME + '_PROF_SSL_%(ssl_domain_name)s { context clientside }'% user_args
                if value.get('make_public'):
                    if value.get ('ssl_impossible'):
                        virtual_dict['vs_name'] = '%s_VS_%s' % (
                            'RPC_PUB', value['group_name']
                        )
                        pubvirt = (
                            '%s\n'
                        ) % PUB_NONSSL_VIRTUAL_ENTRIES % virtual_dict
                        if pubvirt not in pubvirts:
                            pubvirts.append(pubvirt)
                    else:
                        virtual_dict['vs_name'] = '%s_VS_%s' % (
                        'RPC_PUB_SSL', value['group_name']
                        )
                        sslvirt = '%s' % PUB_SSL_VIRTUAL_ENTRIES % virtual_dict
                        if sslvirt not in sslvirts:
                            sslvirts.append(sslvirt)
            if value.get('priority') is True:
                node_data.append(
                    '%s:%s %s' % (
                        node['node_name'],
                        value['backend_port'],
                        PRIORITY_ENTRY % {'priority_int': priority}
                    )
                )
                priority -= 5
            else:
                node_data.append(
                    '%s:%s' % (
                        node['node_name'],
                        value['backend_port']
                    )
                )
#------------------------------------------
        value['nodes'] = ' '.join(node_data)

        pool_node = [POOL_NODE['beginning'] % value]
        if value.get('priority') is True:
            pool_node.append(POOL_NODE['priority'])
        if value.get('service-reset') is True:
            pool_node.append(POOL_NODE['service-reset'])
        pool_node.append(POOL_NODE['end'] % value)
        pools.append('%s' % ' '.join(pool_node))
##########################################
    modpool_parts = build_modpool_parts(inventory=inventory_json)

    for key, value in modpool_parts.iteritems():
        value['group_name'] = key.upper()
        value['pool_name'] = '%s_POOL_%s' % (
            PREFIX_NAME, value['group_name']
        )
        node_data = []
        for node in value['hosts']:
            node['node_name'] = '%s_NODE_%s' % (PREFIX_NAME, node['hostname'])
            nodes.append(NODES % node)
            if value.get('priority') is True:
                node_data.append(
                    '%s:%s %s' % (
                        node['node_name'],
                        value['backend_port'],
                        PRIORITY_ENTRY % {'priority_int': priority}
                    )
                )
                priority -= 5
            else:
                node_data.append(
                    '%s:%s' % (
                        node['node_name'],
                        value['backend_port']
                    )
                )
#------------------------------------------
        value['nodes'] = ' '.join(node_data)

        modpool_node = [MODPOOL_NODE['beginning'] % value]
        if value.get('priority') is True:
            modpool_node.append(MODPOOL_NODE['priority'])
        if value.get('service-reset') is True:
            modpool_node.append(MODPOOL_NODE['service-reset'])
        modpool_node.append(MODPOOL_NODE['end'] % value)
        modpools.append('%s' % ' '.join(modpool_node))
##########################################

    script = []
#
#
#
    script.extend(['### PRE-MAINTENANCE TASKS -- PRE-MAINTENANCE TASKS -- PRE-MAINTENANCE TASKS -- PRE-MAINTENANCE TASKS ###'])
    script.extend(['### PRE-MAINTENANCE TASKS -- PRE-MAINTENANCE TASKS -- PRE-MAINTENANCE TASKS -- PRE-MAINTENANCE TASKS ###'])
    script.extend(['### PRE-MAINTENANCE TASKS -- PRE-MAINTENANCE TASKS -- PRE-MAINTENANCE TASKS -- PRE-MAINTENANCE TASKS ###'])
    script.extend([' '])
    script.extend([' '])
    script.extend(['### Lets BACKUP the current config - DO NOT SKIP THIS STEP!!!!! BACKUP BACKUP BACKUP ###'])
    script.extend(['save /sys ucs /var/local/ucs/KILO-LEAPFROG-1.ucs'])
    script.extend([' '])
    script.extend(['\n### Lets ADD some temporary TCP MONITORS ###'])
    script.extend(['%s' % i % user_args for i in ADDTCPMON])
    script.extend(['### Lets CREATE some Newton MONITORS ###'])
    script.extend(['%s' % i % user_args for i in MONITORS])
    script.extend(['%s' % i for i in commands])
    script.extend(['\n### Lets UPLOAD and CREATE some Newton EXT MONITORS ###'])
    script.extend(['%s' % i % user_args for i in NEWTON_EXT_MON])
    script.extend(['\n### Lets CREATE some Newton NODES -may already exist- ###'])
    script.extend(['%s' % i % user_args for i in nodes])
    script.extend(['\n### Lets CREATE some Newton POOLS ###'])
    script.extend(pools)
    script.extend(['\n### Lets CREATE some Newton VIRTUAL SERVERS ###'])
    script.extend(virts)
    script.extend(sslvirts)
    script.extend(pubvirts)
    script.extend(['\n### POST-MAINTENANCE TASKS -- POST-MAINTENANCE TASKS -- POST-MAINTENANCE TASKS -- POST-MAINTENANCE TASKS ###'])
    script.extend(['### POST-MAINTENANCE TASKS -- POST-MAINTENANCE TASKS -- POST-MAINTENANCE TASKS -- POST-MAINTENANCE TASKS ###'])
    script.extend(['### POST-MAINTENANCE TASKS -- POST-MAINTENANCE TASKS -- POST-MAINTENANCE TASKS -- POST-MAINTENANCE TASKS ###'])
    script.extend([' '])
    script.extend(['### Lets UPDATE some MONITORS ###'])
    script.extend(['%s' % i % user_args for i in MODMONS])
    script.extend(['\n### Lets USE some NEWTON MONITORS ###'])
    script.extend(['%s' % i % user_args for i in ADDNEWMON])
    script.extend(['\n### Lets MODIFY some NEWTON POOLS ###'])
    script.extend(modpools)
    script.extend(['\n### Lets MODIFY some NEWTON VIRTUALS ###'])
    script.extend(['%s' % i % user_args for i in MOD_VIRTUALS])
    script.extend(cleanup)
    script.extend(['\n### Lets CLEANUP some OLD STUFF ###'])
    script.extend(['%s' % i % user_args for i in CLEANUP])
    if user_args['print']:
        for i in script:
            print(i)

    with open(user_args['export'], 'w+') as f:
        f.writelines("\n".join(script))

if __name__ == "__main__":
    main()
