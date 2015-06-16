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




# Start import from Ryu files
from ryu.controller import event
# End import from Ryu files




class EventEnableNdiscOnSwitch(event.EventRequestBase):
	"""
	This Event is triggered for enabling Neighbor Discovery on a switch.
	"""
	def __init__(self, switch):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		switch           Switch instance, enable Neighbor Discovery on the Switch
		================ =========================================================
		"""	
		super(EventEnableNdiscOnSwitch, self).__init__()
		self.dst = 'Ndisc'
		self.switch = switch


class EventDisableNdiscOnSwitch(event.EventRequestBase):
	"""
	This Event is triggered for disabling Neighbor Discovery on a switch.
	"""
	def __init__(self, switch):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		switch           Switch instance, disable Neighbor Discovery on the Switch
		================ =========================================================
		"""	
		super(EventDisableNdiscOnSwitch, self).__init__()
		self.dst = 'Ndisc'
		self.switch = switch


class EventAddNeighborNode(event.EventRequestBase):
	"""
	This Event is triggered for adding a neighbor to a switch.
	"""
	def __init__(self, switch, port, ipv6_addr, hw_addr = None):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		node             Node instance, add Node as switch's neighbor
		================ =========================================================
		"""	
		super(EventAddNeighborNode, self).__init__()
		self.dst = 'Ndisc'
		self.switch = switch
		self.port = port
		self.ipv6_addr = ipv6_addr
		self.hw_addr = hw_addr


class EventRemoveNeighborNode(event.EventRequestBase):
	"""
	This Event is triggered for removing a neighbor from a switch.
	"""
	def __init__(self, switch, port, ipv6_addr, hw_addr = None):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		node             Node instance, remove Node from switch's neighbors
		================ =========================================================
		"""	
		super(EventRemoveNeighborNode, self).__init__()
		self.dst = 'Ndisc'
		self.switch = switch
		self.port = port
		self.ipv6_addr = ipv6_addr
		self.hw_addr = hw_addr


class EventNodeReachable(event.EventBase):
	"""
	This Event is triggered when a Node becomes reachable
	"""
	def __init__(self, switch, port, node):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		node             The node became unreachable
		================ =========================================================
		"""	
		super(EventNodeReachable, self).__init__()
		self.switch = switch
		self.port = port
		self.node = node


class EventNodeUnreachable(event.EventBase):
	"""
	This Event is triggered when a Node becomes unreachable
	"""
	def __init__(self, switch, port, node):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		node             The node became unreachable
		================ =========================================================
		"""	
		super(EventNodeUnreachable, self).__init__()
		self.switch = switch
		self.port = port
		self.node = node


class EventSendNS(event.EventRequestBase):
	"""
	This Event is triggered when fro senfing a Neighbor Solicitation packet
	"""
	def __init__(self, switch, port, ipv6_dst):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		switch           Switch instance
		port			 Port instance
		ipv6_addr		 The destination IPv6 address, String instance
		================ =========================================================
		"""	
		super(EventSendNS, self).__init__()
		self.dst = 'Ndisc'
		self.switch = switch
		self.port = port
		self.ipv6_dst = ipv6_dst


class EventSendRA(event.EventRequestBase):
	"""
	This Event is triggered for sending a Router Advertisement packet
	"""
	def __init__(self, switch, port, anch, eth_dst, ipv6_dst):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		switch           Switch instance
		port			 Port instance
		anch	         Anchor instance
		eth_dst			 The destination Ethernet address, String instance
		ipv6_addr		 The destination IPv6 address, String instance
		================ =========================================================
		"""	
		super(EventSendRA, self).__init__()
		self.dst = 'Ndisc'
		self.switch = switch
		self.port = port
		self.anch = anch
		self.eth_dst = eth_dst
		self.ipv6_dst = ipv6_dst


class EventNeighRequest(event.EventRequestBase):
	"""
	This Event is triggered for requesting the neighors of a switch.
	"""
	def __init__(self, dpid):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		dpid             The switch dpid.
		================ =========================================================
		"""	
		super(EventNeighRequest, self).__init__()
		self.dst = 'Ndisc'
		self.dpid = dpid


class EventNeighReply(event.EventReplyBase):
	"""
	This Event contains the requested neighors of a switch.
	"""
	def __init__(self, dst, neigh):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		neigh            The switch's neighbor list.
		================ =========================================================
		"""	
		super(EventNeighReply, self).__init__(dst)
		self.neigh = neigh
