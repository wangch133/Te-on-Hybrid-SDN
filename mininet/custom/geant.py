#!/usr/bin/env python
# -*- coding:utf-8 -*-

# 2020/9/23 by wangch

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.util import dumpNodeConnections

class MyTopo(Topo):

    def __init__(self):
        super(MyTopo,self).__init__()

        # read topo from file
        with open('./topo/geant01.txt') as fp:
            dm_list = fp.readlines()
        for i in range(len(dm_list)-1, -1, -1):
            dm_list[i] = dm_list[i].strip()
            if dm_list[i].startswith('#') or len(dm_list[i]) == 0:
                del dm_list[i]
        
        node = []
        node_flag = 0
        link = []
        link_flag = 0
        for line in dm_list:
            if line.startswith('NODES'):
                node_flag = 1
                continue
            elif node_flag and line.startswith(')'):
                node_flag = 0
                continue
            if line.startswith('LINKS'):
                link_flag = 1
                continue
            elif link_flag and line.startswith(')'):
                link_flag = 0
                continue

            line = line.replace('(', '')
            line = line.replace(')', '')
            tmp = line.split(' ')
            while '' in tmp:
                tmp.remove('')

            if node_flag:
                node.append(tmp[0][0:3])
            if link_flag:
                link.append({'src': tmp[1][0:3], 'dst': tmp[2][0:3], 'cap': tmp[7], 'cost': tmp[8]})

        # print(node)
        # print(link)

        # for i in range(0, 2):
        #     dpid = '%016X'%(i+1)
        #     print(dpid)
        #     self.addSwitch(node[i], dpid=dpid)
        #     host = self.addHost('h_{}'.format(node[i]))
        #     self.addLink(node[i], host)
        # self.addLink(node[0], node[1])

        for index,n in enumerate(node):
            self.addSwitch(n, dpid='%016X'%(index+1))
            host = self.addHost('h_{}'.format(n))
            self.addLink(host, n)

        for l in link:
            self.addLink(l['src'], l['dst'])


topos = {"mytopo":(lambda:MyTopo())}