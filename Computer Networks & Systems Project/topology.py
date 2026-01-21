from mininet.topo import Topo
from mininet.node import Node


class LinuxRouter(Node):
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        if 'routes' in params:
            for (ip, gateway) in params['routes']:
                self.cmd('ip route add {} via {}'.format(ip, gateway))
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()


class courseworkTopo(Topo):

    def build(self):
        host1 = self.addHost('host1', ip="192.168.0.2/24",
                             defaultRoute='via 192.168.0.1')

        host2 = self.addHost('host2', ip="192.168.0.3/24",
                             defaultRoute='via 192.168.0.1')

        host3 = self.addHost('host3', ip="192.168.2.2/24",
                             defaultRoute='via 192.168.2.1')

        host4 = self.addHost('host4', ip="192.168.2.3/24",
                             defaultRoute='via 192.168.2.1')

        host5 = self.addHost('host5', ip="192.168.3.2/24",
                             defaultRoute='via 192.168.3.1')

        router1 = self.addHost('router1', ip=None, cls=LinuxRouter, routes=[
            ('192.168.3.0/24', '10.10.1.2'),
            ('192.168.2.0/24', '10.10.0.1')
        ])

        router2 = self.addHost('router2', ip=None, cls=LinuxRouter, routes=[
            ('192.168.0.0/24', '10.10.0.2'),
            ('10.10.1.0/24', '10.10.0.2'),
            ('192.168.3.0/24', '10.10.0.2')
        ])

        router3 = self.addHost('router3', ip=None, cls=LinuxRouter, routes=[
            ('192.168.0.0/24', '10.10.1.1'),
            ('10.10.0.0/24', '10.10.1.1'),
            ('192.168.2.0/24', '10.10.1.1')
        ])

        # add a switch to the network
        switch1 = self.addSwitch('switch1')
        switch2 = self.addSwitch('switch2')

        # add a link between the host `h1` and the `s1` switch
        self.addLink(host1, switch1)
        self.addLink(host2, switch1)
        self.addLink(switch1, router1,
                     intfName1='switch1-router1',  #TODO change here
                     params2={'ip': '192.168.0.1/24'},
                     delay='0ms', loss=0)

        # Straight path
        self.addLink(router1, router3,
                     intfName1='router1-eth3',
                     intfName2='router3-eth2',
                     params1={'ip': '10.10.1.1/24'},
                     params2={'ip': '10.10.1.2/24'},
                     bw=100, delay='100ms', loss=0)
        self.addLink(router3, host5,
                     intfName1='router3-eth0',
                     params1={'ip': '192.168.3.1/24'},
                     delay='0ms', loss=0)

        # Downwards path
        self.addLink(router1, router2,
                     intfName1='router1-eth2',
                     intfName2='router2-eth2',
                     params1={'ip': '10.10.0.2/24'},
                     params2={'ip': '10.10.0.1/24'},
                     delay='10ms', loss=1)
        self.addLink(router2, switch2,
                     intfName1='router3-eth0',
                     params1={'ip': '192.168.2.1/24'},
                     delay='0ms', loss=0)
        self.addLink(host3, switch2)
        self.addLink(host4, switch2)


# the topologies accessible to the mn tool's `--topo` flag
# note: if using the Dockerfile, this must be the same as in the Dockerfile
topos = {'courseworkTopo': (lambda: courseworkTopo())}