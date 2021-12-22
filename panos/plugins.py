#!/usr/bin/env python

# Copyright (c) 2021, Palo Alto Networks
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.


"""Prisma Access module contains objects that exist in the 'Plugins/Cloud Services' tab in the Panorama GUI"""

import logging
import re
import xml.etree.ElementTree as ET

import panos
import panos.errors as err
from panos import device, getlogger, string_or_list
from panos.base import ENTRY, MEMBER, PanObject, Root
from panos.base import VarPath as Var
from panos.base import VersionedPanObject, VersionedParamPath, VsysOperations


class CloudServicesPlugin(VersionedPanObject):
    """Prisma Access configuration base object

    Args:
        all_traffic_to_dc(bool): Send All Traffic to DC Option

    """

    ROOT = Root.DEVICE
    SUFFIX = None
    CHILDTYPES = (
        "plugins.RemoteNetworks",
        "plugins.RoutingPreference",

    )

    def _setup(self):
        # xpaths
        self._xpaths.add_profile(value="/plugins/cloud_services")

        # params
        params = []

        params.append(
            VersionedParamPath("all_traffic_to_dc", vartype="yesno",
                               path="traffic-steering/All-Traffic-To-DC", version="9.1.0")
        )

        self._params = tuple(params)


class AggBandwidth(VersionedPanObject):
    """Prisma Access remote networks Aggregated Bandwidth configuration base object

    Args:
        enabled(bool): Whether Aggregated BW mode is enabled or not
    """
    # TODO: Add support for QoS Here ?
    ROOT = Root.DEVICE
    SUFFIX = None
    CHILDTYPES = (
        "plugins.Region",
    )

    def _setup(self):
        # xpaths
        self._xpaths.add_profile(
            value="/agg-bandwidth")

        # params
        params = []

        params.append(
            VersionedParamPath("enabled", vartype="yesno",
                               path="enabled", version="9.1.0")
        )

        self._params = tuple(params)


class Region(VersionedPanObject):
    """Prisma Access remote networks Aggregated Bandwidth configuration base object

    Args:
        allocated_bw(int): Allocated BW in Mbps
        spn_name_list(list/str): Names of the SPN for the region
    """
    ROOT = Root.DEVICE
    SUFFIX = ENTRY
    CHILDTYPES = (

    )

    def _setup(self):
        # xpaths
        self._xpaths.add_profile(
            value="/region")

        # params
        params = []
        params.append(
            VersionedParamPath(
                "allocated_bw", vartype="int", path="allocated-bw", version="9.1.0")
        )
        params.append(
            VersionedParamPath(
                "spn_name_list", path="spn-name-list", vartype="member", version="9.1.0")
        )
        self._params = tuple(params)


class RemoteNetworks(VersionedPanObject):
    """Prisma Access Remote-Networks configuration base object

    Args:
        overlapped_subnets(bool): Whether or not overlapped subnets are enabled
        template_stack(str): Remote Networks Template stack
        device_group(str): Remote Networks device group
        trusted_zones(list/str): Remote Networks trusted zones

    """

    ROOT = Root.DEVICE
    SUFFIX = None
    CHILDTYPES = (
        "plugins.RemoteNetwork",
        "plugins.AggBandwidth",
        "plugins.DnsServers",
        "plugins.UdpQueries"
    )
    # TODO Add support for inbound remote network later

    def _setup(self):
        # xpaths
        self._xpaths.add_profile(
            value="/remote-networks")

        # params
        params = []

        params.append(
            VersionedParamPath("overlapped_subnets", vartype="yesno",
                               path="overlapped-subnets", version="9.1.0")
        )
        params.append(
            VersionedParamPath(
                "template_stack", path="template-stack", version="9.1.0")
        )
        params.append(
            VersionedParamPath(
                "device_group", path="device-group", version="9.1.0")
        )
        params.append(
            VersionedParamPath("trusted_zones", vartype="member",
                               path="trusted-zones", version="9.1.0")
        )

        self._params = tuple(params)


class InternalDnsMatch(VersionedPanObject):
    """Prisma Access remote-networks Internal DNS entry configuration base object

    Args:
        domain_list(list/str): Internal Domains names

    """
    ROOT = Root.DEVICE
    SUFFIX = ENTRY
    CHILDTYPES = (
        "plugins.PrimaryInternalDNSServer",
        "plugins.SecondaryInternalDNSServer",
    )

    def _setup(self):
        # xpaths
        self._xpaths.add_profile(
            value="/internal-dns-match")

        # params
        params = []

        params.append(
            VersionedParamPath("domain_list", vartype="member",
                               path="domain-list", version="9.1.0")
        )


        self._params = tuple(params)


class DNSServerBase(VersionedPanObject):
    """Abstract DNS Class, will be inherited for correct XPATH

    Args:
        dns_server(str): IP of DNS Server
        use-cloud-default(bool): Use cloud default DNS
        same_as_internal(bool): Use same DNS server as Internal 

    """
    ROOT = Root.DEVICE

    def __init__(self, *args, **kwargs):
        if type(self) == DNSServerBase:
            raise err.PanDeviceError(
                "Do not instantiate class. Please use a subclass.")
        super(DNSServerBase, self).__init__(*args, **kwargs)

    def add_dns_params(self, same_as_internal):
        params = []

        params.append(
            VersionedParamPath(
                "dns_server", path="dns-server", version="9.1.0")
        )
        params.append(
            VersionedParamPath("use-cloud-default", vartype="exist",
                               path="use_cloud_default", version="9.1.0")
        )
        if same_as_internal:
            params.append(
                VersionedParamPath(
                    "same_as_internal", vartype="exist", path="same-as-internal", version="9.1.0")
            )
        self._params = tuple(params)


class PrimaryInternalDNSServer(DNSServerBase):
    """A primary Internal DNS Server for remote networks
    """

    def _setup(self):
        # xpaths
        self._xpaths.add_profile(value="/primary")
        self.add_dns_params(False)


class SecondaryInternalDNSServer(DNSServerBase):
    """A Secondary Internal DNS Server for remote networks
    """

    def _setup(self):
        # xpaths
        self._xpaths.add_profile(value="/secondary")
        self.add_dns_params(False)


class PrimaryPublicDNSServer(DNSServerBase):
    """A primary Public DNS Server for remote networks
    """

    def _setup(self):
        # xpaths
        self._xpaths.add_profile(value="/primary-public-dns")
        self.add_dns_params(True)


class SecondaryPublicDNSServer(DNSServerBase):
    """A secondary Internal DNS Server for remote networks
    """

    def _setup(self):
        # xpaths
        self._xpaths.add_profile(value="/secondary-public-dns")
        self.add_dns_params(True)


class DnsServers(VersionedPanObject):  # TODO : shoud it be sth else ?
    """Prisma Access remote-networks DNS Servers configuration base object

    Args:
        name: (unused, and may be omitted)

    """
    ROOT = Root.DEVICE
    SUFFIX = ENTRY
    CHILDTYPES = (
        "plugins.InternalDnsMatch",
        "plugins.PrimaryPublicDNSServer",
        "plugins.SecondaryPublicDNSServer",
    )

    def _setup(self):
        # xpaths
        self._xpaths.add_profile(
            value="/dns-servers")

        # params
        params = []

        self._params = tuple(params)


class UdpQueries(VersionedPanObject):
    """Prisma Access remote-networks DNS Servers retries configuration base object

    Args:
        interval(int): Interval between DNS retries
        attempts(int): Number of attempts

    """
    ROOT = Root.DEVICE
    CHILDTYPES = (

    )

    def _setup(self):
        # xpaths
        self._xpaths.add_profile(
            value="/udp-queries")

        # params
        params = []
        params.append(
            VersionedParamPath("interval", vartype="int",
                               path="retries/interval", default=2, version="9.1.0")
        )
        params.append(
            VersionedParamPath("attempts", vartype="int",
                               path="retries/attempts", default=5, version="9.1.0")
        )
        self._params = tuple(params)


class Bgp(VersionedPanObject):  # TODO : shoud it be protcol-bgp ?
    """Prisma Access BGP configuration object

    Args:
        enable(bool): Whether BGP is enabled or not.
        originate_default_route(bool): Originate default route
        summarize_mobile_user_routes(bool): Summarize mobile users routes or not 
        do_not_export_routes(bool): Do not export routes
        peer_as(int): Peer AS
        peer_ip_address(str): Peer IP Address
        local_ip_address(str): Local IP Address
        secret(str): BGP Password

    """
    ROOT = Root.DEVICE
    SUFFIX = None
    CHILDTYPES = (

    )

    def _setup(self):
        # xpaths
        self._xpaths.add_profile(
            value="/protocol/bgp")

        # params
        params = []

        params.append(
            VersionedParamPath("enable", vartype="yesno",
                               path="enable", version="9.1.0")
        )

        params.append(
            VersionedParamPath("originate_default_route", vartype="yesno",
                               path="originate-default-route", version="9.1.0")
        )
        params.append(
            VersionedParamPath("summarize_mobile_user_routes", vartype="yesno",
                               path="summarize-mobile-user-routes", version="9.1.0")
        )
        params.append(
            VersionedParamPath("do_not_export_routes", vartype="yesno",
                               path="do-not-export-routes", version="9.1.0")
        )

        params.append(
            VersionedParamPath("peer_as", vartype="int",
                               path="peer-as", version="9.1.0")
        )
        params.append(
            VersionedParamPath("peer_ip_address",
                               path="peer-ip-address", version="9.1.0")
        )
        params.append(
            VersionedParamPath("local_ip_address",
                               path="local-ip-address", version="9.1.0")
        )
        params.append(
            VersionedParamPath("secret", vartype="encrypted",
                               path="secret", version="9.1.0")
        )

        self._params = tuple(params)


class BgpPeer(VersionedPanObject):
    """Prisma Access BGP Peer configuration object

    Args:
        same_as_primary(bool) Same AS as primary WAN Peer.
        peer_as(int): Peer AS
        peer_ip_address(str): Peer IP Address
        local_ip_address(str): Local IP Address
        secret(str): BGP Password

    """
    ROOT = Root.DEVICE
    SUFFIX = None
    CHILDTYPES = (

    )

    def _setup(self):
        # xpaths
        self._xpaths.add_profile(
            value="/bgp-peer")

        # params
        params = []

        params.append(
            VersionedParamPath("same_as_primary", vartype="yesno",
                               path="same-as-primary", version="9.1.0")
        )
        params.append(
            VersionedParamPath("peer_ip_address",
                               path="peer-ip-address", version="9.1.0")
        )
        params.append(
            VersionedParamPath("local_ip_address",
                               path="local-ip-address", version="9.1.0")
        )
        params.append(
            VersionedParamPath("secret", vartype="encrypted",
                               path="secret", version="9.1.0")
        )
        self._params = tuple(params)


class RoutingPreference(VersionedPanObject):
    """Prisma Access routing-preference configuration base object

    Args:
        default(bool): Default Routing Mode
        hot_potato_routing(bool): Hot Potato Routing Mode

    """
    ROOT = Root.DEVICE
    SUFFIX = None
    CHILDTYPES = (

    )

    def _setup(self):
        # xpaths
        self._xpaths.add_profile(
            value="/routing-preference")

        # params
        params = []

        params.append(
            VersionedParamPath("default", vartype="exist",
                               path="default", default=True, version="9.1.0")
        )
        params.append(
            VersionedParamPath("hot_potato_routing", vartype="exist",
                               path="Hot-Potato-Routing", version="9.1.0")
        )
        
        self._params = tuple(params)


class Link(VersionedPanObject):
    """Prisma Access ECMP Links config object

    Args:
        ipsec_tunnel(str): IPSEC Tunnel Name

    """
    # NAME = None #Not needed, default value
    ROOT = Root.DEVICE
    SUFFIX = ENTRY
    CHILDTYPES = (
        "plugins.Bgp",
    )

    def _setup(self):
        # xpaths
        self._xpaths.add_profile(value="/link")

        # params
        params = []

        params.append(
            VersionedParamPath(
                "ipsec_tunnel", path="ipsec-tunnel", version="9.1.0")
        )

        # TODO QOS HERE
        self._params = tuple(params)


class RemoteNetwork(VersionedPanObject):
    """Prisma Access Remote-Networks Onboarding configuration base object

    Args:
        subnets(list/str): Static Routes
        region(str): Remote Network Region Name
        license_type(str): License Type
        ipsec_tunnel(str): IPSEC tunnel Name
        secondary_wan_enabled(bool): Secondary WAN Enabled ?
        ecmp_load_balancing(bool):Enabled ECMP or not
        spn_name(str): SPN Name of the remote network
        inbound_flow_over_pa_backbone(bool): inbound flow over pa backbone
    """
    ROOT = Root.DEVICE
    SUFFIX = ENTRY
    CHILDTYPES = (
        "plugins.Bgp",
        "plugins.BgpPeer",
        "plugins.Link",
    )

    def _setup(self):
        # xpaths
        self._xpaths.add_profile(
            value="/onboarding")

        # params
        params = []

        params.append(
            VersionedParamPath("subnets", vartype="member",
                               path="subnets", version="9.1.0")
        )
        params.append(
            VersionedParamPath("region", path="region", version="9.1.0")
        )
        params.append(
            VersionedParamPath(
                "license_type", path="license-type", version="9.1.0")
        )
        params.append(
            VersionedParamPath(
                "ipsec_tunnel", path="ipsec-tunnel", version="9.1.0")
        )
        params.append(
            VersionedParamPath("secondary_wan_enabled", vartype="yesno",
                               path="secondary-wan-enabled", version="9.1.0")
        )
        params.append(
            VersionedParamPath("ecmp_load_balancing", path="ecmp-load-balancing",
                               version="9.1.0",  values=("enabled-with-symmetric-return", "disabled"))
        )
        params.append(
            VersionedParamPath("secondary_ipsec_tunnel",
                               path="secondary-ipsec-tunnel", version="9.1.0")
        )
        params.append(
            VersionedParamPath("spn_name", path="spn-name", version="9.1.0")
        )
        params.append(
            VersionedParamPath("inbound_flow_over_pa_backbone", vartype="yesno",
                               path="inbound-flow-over-pa-backbone", version="9.1.0")
        )

        # TODO Add QoS Support

        self._params = tuple(params)
