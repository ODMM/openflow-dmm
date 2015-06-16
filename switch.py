# Copyright (C) IMDEA Networks Institute and NETCOM research group, Department of 
# Telematics Engineering, University Carlos III of Madrid.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# IMDEA Networks Institute and NETCOM research group, Department of 
# Telematics Engineering, University Carlos III of Madrid, hereby disclaims all 
# copyright interest in the program 'OpenFlow-DMM', released by the Open Platform 
# for DMM solutions (ODMM), written by Luca Cominardi <odmm-support@odmm.net>.
#
# signature of IMDEA Networks Institute and NETCOM research group, Department of 
# Telematics Engineering, University Carlos III of Madrid, 12 June 2015.
# Albert Banchs, Deputy director of IMDEA Networks Institute and Titular professor
# at University Carlos III of Madrid.




# Start import from iJOIN solution files
import ipv6_utils

from static import COOKIE
from static import COOKIE_MASK
from static import OF_TABLE_DEFAULT
# End import from iJOIN solution files

# Start import from Ryu files
import time

from ryu.lib.dpid import dpid_to_str

from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import icmpv6
from ryu.lib.packet import ipv6

from ryu.ofproto import ether
from ryu.ofproto import inet
from ryu.ofproto import ofproto_v1_3 as ofproto
from ryu.ofproto import ofproto_v1_3_parser as ofp_parser
# End import from Ryu files


class OFRule:
	"""
	This class represents an OpenFlow Rule
	"""
	def __init__(self, switch, match, actions, instructions = [], table_id = OF_TABLE_DEFAULT, 
				priority = ofproto.OFP_DEFAULT_PRIORITY, cookie = COOKIE, cookie_mask = COOKIE_MASK):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		switch			 The switch involved, Switch instance
		match			 The OpenFlow matching rule, OFPMatch instance
		actions	         The OpenFlow actions rule, OFPAction instance
		priority		 The OpenFlow rule's priority, Int isntance
		================ =========================================================
		"""
		self.key = str(switch.switch.dp.id) + ':' + str(table_id) + ':' + str(match)
		self.switch = switch
		self.match = match
		self.actions = actions
		self.instructions = instructions
		self.table_id = table_id
		self.priority = priority
		self.cookie = cookie
		self.cookie_mask = cookie_mask


class Link:
	"""
	This class represents a link in the network extending Ryu Link class.
	"""
	def __init__(self, link, weight = 1):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		link             Ryu Link instance
		weight			 The link's weight
		================ =========================================================
		"""
		self.link = link
		self.weight = weight

	
	def to_dict(self):
		d = self.link.to_dict()
		d['weight'] = self.weight

		return d


class AccessPointConf:
	"""
	This class includes all configuration for access point switches
	"""
	def __init__(self):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		port             Wireless port, is a Port instance
		served_ues	     The dictionary storing the UEs being served by the 
						 access point
		================ =========================================================
		"""
		self.port = None
		self.served_ues = {}

	
	def to_dict(self):
		# FIXME
		d = {'port': self.port.port_no,
		}

		return d


class GatewayConf:
	"""
	This class includes all configuration for gateway switches
	"""
	def __init__(self):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		port             Gateway port, is a Port instance
		nw_prefix        tuple instance.
						 IPv6 prefix, each octet is an element of the tuple:
                         ('0','1','2','3','4','5','6','7')
		nw_prefix_len    int instance.
						 CIDR netmask to apply to network_prefix.
		served_ues	     The dictionary storing the UEs being served by the 
						 gateway
		================ =========================================================
		"""
		self.port = None
		self.nw_prefix = None
		self.nw_prefix_len = 0
		self.served_ues = {}

	
	def to_dict(self):
		# FIXME
		d = {'port': self.port.port_no,
			'nw_prefix': ipv6_utils.ipv6_prefix_string(self.nw_prefix, self.nw_prefix_len)
			}

		return d


class Switch:
	"""
	This class represents a switch in the network extending Ryu Switch class.
	"""
	def __init__(self, switch):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		switch           Ryu Switch instance
		hw_addr			 Switch's Hardware address
		hw_addr_mcast	 Switch's Ethernet solicited node multicast address
		ipv6_local_ucast Switch's IPv6 local unicast address
		_addr
		ipv6_local_mcast Switch's IPv6 solicited node multicast address
		_addr
		links			 Switch's links available on the switch
		is_gw			 Mark the switch as Gateway, Boolean instance
		gw_conf			 Gateway configuration
		is_ap			 Mark the switch as Access Point, Boolean instance
		ap_conf			 Access Point configuration
		layer			 Layer of the switch in the newtork topology
		================ =========================================================
		"""
		self.switch = switch

		hw_addr = '{0:012x}'.format(self.switch.dp.id)
		self.hw_addr = ':'.join(a+b for a, b in zip(hw_addr[::2], hw_addr[1::2]))

		self.ipv6_local_ucast_addr = ipv6_utils.ipv6_local_ucast_from_mac(self.hw_addr)
		self.ipv6_local_mcast_addr = ipv6_utils.ipv6_local_mcast_from_mac(self.hw_addr)

		self.hw_addr_mcast = ipv6_utils.mac_mcast_from_ipv6_local_mcast(self.ipv6_local_mcast_addr)	

		self.links = {}

		self.is_gw = False
		self.gw_conf = GatewayConf()

		self.is_ap = False
		self.ap_conf = AccessPointConf()

		self.layer = float('inf')


	def get_port(self, port_no):
		"""
		Return the Port instance given the port number
		"""
		for p in self.switch.ports:
			if p.port_no == port_no:
				return p

	def to_dict(self):
		d = self.switch.to_dict()
		if self.is_ap:
			d['ap_conf'] = self.ap_conf.to_dict()
		if self.is_gw:
			d['gw_conf'] = self.gw_conf.to_dict()

		return d
