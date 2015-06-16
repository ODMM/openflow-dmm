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




class EventTopologyUpdate(event.EventBase):
	"""
	This Event is triggered when a topology change occurs in the network.
	"""
	def __init__(self, switches):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		switches         The dictionary storing the switches
		================ =========================================================
		"""	
		super(EventTopologyUpdate, self).__init__()
		self.switches = switches.copy()


class EventSwitchEnter(event.EventBase):
	"""
	This Event is triggered when a switch enters the network.
	"""
	def __init__(self, switch):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		switch           The Switch object.
		================ =========================================================
		"""	
		super(EventSwitchEnter, self).__init__()
		self.switch = switch


class EventSwitchUpdate(event.EventBase):
	"""
	This Event is triggered when a switch updates its features.
	"""
	def __init__(self, switch):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		switch           The Switch object.
		================ =========================================================
		"""	
		super(EventSwitchUpdate, self).__init__()
		self.switch = switch


class EventSwitchLeave(event.EventBase):
	"""
	This Event is triggered when a switch leaves the network.
	"""
	def __init__(self, switch):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		switch           The Switch object.
		================ =========================================================
		"""	
		super(EventSwitchLeave, self).__init__()
		self.switch = switch


class EventLinkAdd(event.EventBase):
	"""
	This Event is triggered when a link appears in the network.
	"""
	def __init__(self, link):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		link             The Link object.
		================ =========================================================
		"""	
		super(EventLinkAdd, self).__init__()
		self.link = link


class EventLinkDelete(event.EventBase):
	"""
	This Event is triggered when a link disappears in the network.
	"""
	def __init__(self, link):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		link             The Link object.
		================ =========================================================
		"""	
		super(EventLinkDelete, self).__init__()
		self.link = link


class EventWriteOFRule(event.EventRequestBase):
	"""
	This Event is triggered when a module wants to write an OpenFlow rule
	"""
	def __init__(self, of_rule):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		of_rule          The OpenFlow rule to write, OFRule instance
		================ =========================================================
		"""	
		super(EventWriteOFRule, self).__init__()
		self.dst = 'Nmm'
		self.of_rule = of_rule


class EventDelOFRule(event.EventRequestBase):
	"""
	This Event is triggered when a module wants to write an OpenFlow rule
	"""
	def __init__(self, of_rule = None):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		of_rule          The OpenFlow rule to delete, OFRule instance
		================ =========================================================
		"""	
		super(EventDelOFRule, self).__init__()
		self.dst = 'Nmm'
		self.of_rule = of_rule


class EventWriteOFRule(event.EventRequestBase):
	"""
	This Event is triggered when a module wants to write an OpenFlow rule
	"""
	def __init__(self, of_rule):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		of_rule          The OpenFlow rule to write, OFRule instance
		================ =========================================================
		"""	
		super(EventWriteOFRule, self).__init__()
		self.dst = 'Nmm'
		self.of_rule = of_rule


class EventDelOFRule(event.EventRequestBase):
	"""
	This Event is triggered when a module wants to write an OpenFlow rule
	"""
	def __init__(self, of_rule = None):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		of_rule          The OpenFlow rule to delete, OFRule instance
		================ =========================================================
		"""	
		super(EventDelOFRule, self).__init__()
		self.dst = 'Nmm'
		self.of_rule = of_rule


class EventPushPacket(event.EventRequestBase):
	"""
	This Event is triggered when a module wants to push a packet through a switch's interface
	"""
	def __init__(self, switch, port, pkt):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		switch           Switch instance
		port			 Port instance
		pkt				 Serialized Packet instance
		================ =========================================================
		"""	
		super(EventPushPacket, self).__init__()
		self.dst = 'Nmm'
		self.switch = switch
		self.port = port
		self.pkt = pkt


class EventProcessPacket(event.EventRequestBase):
	"""
	This Event is triggered when a module wants to push a packet through switch's OFTable
	"""
	def __init__(self, switch, pkt):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		switch           Switch instance
		pkt				 Serialized Packet instance
		================ =========================================================
		"""	
		super(EventProcessPacket, self).__init__()
		self.dst = 'Nmm'
		self.switch = switch
		self.pkt = pkt


class EventSwitchRequest(event.EventRequestBase):
	# If dpid is None, reply all list
	def __init__(self, dpid = None):
		super(EventSwitchRequest, self).__init__()
		self.dst = 'Nmm'
		self.dpid = dpid


class EventSwitchReply(event.EventReplyBase):
	def __init__(self, dst, switch):
		super(EventSwitchReply, self).__init__(dst)
		self.switch = switch


class EventLinkRequest(event.EventRequestBase):
	# If dpid is None, reply all list
	def __init__(self, dpid = None):
		super(EventLinkRequest, self).__init__()
		self.dst = 'Nmm'
		self.dpid = dpid


class EventLinkReply(event.EventReplyBase):
	def __init__(self, dst, link):
		super(EventLinkReply, self).__init__(dst)
		self.link = link
