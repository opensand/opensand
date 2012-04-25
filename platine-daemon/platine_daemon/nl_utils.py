#!/usr/bin/env python 
# -*- coding: utf-8 -*-
# Author: Julien BERNARD / <jbernard@toulouse.viveris.com>

"""
netlink.py - interface with netlink adresses and routes
"""

import netlink.route.capi as capi
import netlink.route.link as link
import netlink.core as netlink
import netlink.route.address as address

class NlError(netlink.NetlinkError):
    pass


# dissociate the Object exists error
class NlExists(netlink.NetlinkError):
    pass


class NlRoute(object):
    """Route object"""

    def __init__(self, iface_name):
        self._link = link.resolve(iface_name)

    def add(self, dst, gw=None):
        """ add a new route """
        nh = capi.rtnl_route_nh_alloc()
        route = capi.rtnl_route_alloc()
        sock = netlink.Socket()
        sock.connect(netlink.NETLINK_ROUTE)

        addr_dst = netlink.AbstractAddress(dst)
        ifidx = self._link.ifindex

        capi.rtnl_route_set_dst(route, addr_dst._nl_addr)
        capi.rtnl_route_nh_set_ifindex(nh, ifidx)
        if gw is not None:
            addr_gw = netlink.AbstractAddress(gw)
            capi.rtnl_route_nh_set_gateway(nh, addr_gw._nl_addr)
        capi.rtnl_route_add_nexthop(route, nh)
        ret = capi.rtnl_route_add(sock._sock, route, 0)
        if ret == -6:
            raise NlExists(ret)
        if ret < 0:
            raise NlError(ret)
        

    def delete(self, dst, gw=None):
        """ delete a route """
        nh = capi.rtnl_route_nh_alloc()
        route = capi.rtnl_route_alloc()
        sock = netlink.Socket()
        sock.connect(netlink.NETLINK_ROUTE)

        addr_dst = netlink.AbstractAddress(dst)
        ifidx = self._link.ifindex

        capi.rtnl_route_set_dst(route, addr_dst._nl_addr)
        capi.rtnl_route_nh_set_ifindex(nh, ifidx)
        if gw is not None:
            addr_gw = netlink.AbstractAddress(gw)
            capi.rtnl_route_nh_set_gateway(nh, addr_gw._nl_addr)
        capi.rtnl_route_add_nexthop(route, nh)
        ret = capi.rtnl_route_delete(sock._sock, route, 0)
        if ret == -6:
            raise NlExists(ret)
        if ret < 0:
            raise NlError(ret)


class NlAddress(object):
    """Address object"""

    def __init__(self):
        pass

    def add(self, addr, iface):
        """ add a new route """
        ifidx = link.resolve(iface).ifindex
        ad = address.Address()
        sock = netlink.Socket()
        sock.connect(netlink.NETLINK_ROUTE)
        ad.local = addr
        ad.ifindex = ifidx
        ret = capi.rtnl_addr_add(sock._sock, ad._rtnl_addr, 0)
        if ret == -6:
            raise NlExists(ret)
        if ret < 0:
            raise NlError(ret)

    def delete(self, addr, iface):
        """ delete a route """
        ifidx = link.resolve(iface).ifindex
        ad = address.Address()
        sock = netlink.Socket()
        sock.connect(netlink.NETLINK_ROUTE)
        ad.local = addr
        ad.ifindex = ifidx
        ret = capi.rtnl_addr_delete(sock._sock, ad._rtnl_addr, 0)
        if ret == -6:
            raise NlExists(ret)
        if ret < 0:
            raise NlError(ret)


if __name__ == '__main__':
    ### ADDRESSES ###
    ADDR = NlAddress()
    try:
        ADDR.add('192.168.18.5/24','eth0')
    except NlError, msg:
        print "cannot add address:", msg
    else:
        print "Address added"

    try:
        ADDR.delete('192.168.18.5/24','eth0')
    except NlError, msg:
        print "cannot remove address:", msg
    else:
        print "Address removed"

    try:
        ADDR.add('2001:660:6602:101::5/64','eth0')
    except NlError, msg:
        print "cannot add address:", msg
    else:
        print "Address added"

    try:
        ADDR.delete('2001:660:6602:101::5/64','eth0')
    except NlError, msg:
        print "cannot remove address:", msg
    else:
        print "Address removed"

    ### ROUTES ###
    ROUTE = NlRoute("eth0")
    try:
        ROUTE.add("192.168.18.0/24")
    except NlError, msg:
        print "cannot add route: ", msg
    else:
        print "Route added"

    try:
        ROUTE.delete("192.168.18.0/24")
    except NlError, msg:
        print "cannot delete route: ", msg
    else:
        print "Route removed"

    try:
        ROUTE.add("2001:660:6602::101:5")
    except NlError, msg:
        print "cannot add route: ", msg
    else:
        print "Route added"

    try:
        ROUTE.delete("2001:660:6602::101:5")
    except NlError, msg:
        print "cannot delete route: ", msg
    else:
        print "Route removed"

