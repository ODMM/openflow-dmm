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
import log
import ipv6_utils

from static import OF_TABLE_UES
from static import OF_TABLE_NEIGH
from static import OF_TABLE_ROUTING

from switch import OFRule

from event import *

from mme.event import EventUEConnected
from mme.event import EventUEDisconnected

from nmm.event import EventWriteOFRule
from nmm.event import EventDelOFRule

from ndisc.event import EventEnableNdiscOnSwitch
from ndisc.event import EventDisableNdiscOnSwitch
from ndisc.event import EventAddNeighborNode
from ndisc.event import EventRemoveNeighborNode
from ndisc.event import EventNodeUnreachable

from nmm.event import EventSwitchEnter
from nmm.event import EventSwitchUpdate
from nmm.event import EventSwitchLeave

from amm.event import EventUEAnchorsUpdate
# End import from iJOIN solution files

# Start import from Ryu files
from ryu.base import app_manager

from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER

from ryu.ofproto import ofproto_v1_3 as ofproto
from ryu.ofproto import ofproto_v1_3_parser as ofp_parser

from ryu.ofproto import ether
from ryu.ofproto import inet

from ryu.lib.packet import icmpv6
# End import from Ryu files




class AccessPoint(app_manager.RyuApp):
	"""
	================ =========================================================
	Attribute        Description
	================ =========================================================
	OFP_VERSIONS     Declaration of supported OFP version
	_EVENTS          The list of events provided by the RyuApp
	================ =========================================================
	"""
	OFP_VERSIONS = [ofproto.OFP_VERSION]
	_EVENTS = []


	def __init__(self, *args, **kwargs):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		access_points    The dictionary storing the switches enabled with access
						 point functionalities
		================ =========================================================
		"""	
		super(AccessPoint, self).__init__(*args, **kwargs)
		self.logger = log.get_logger(self.name)
		self.access_points = {}
		self.connected_ues = {}


	def _add_switch_ap(self, switch):
		"""
		Add the switch to the AP list
		"""
		self.access_points[switch.switch.dp.id] = switch
		self._write_ap_rules(switch)

		req = EventEnableNdiscOnSwitch(switch)
		self.send_event(req.dst, req)

		self.logger.info("Switch <" + str(hex(switch.switch.dp.id)) + "> offers access point capabilities")

	
	def _del_switch_ap(self, switch):
		"""
		Del the switch from the AP list
		"""
		req = EventDisableNdiscOnSwitch(switch)
		self.send_event(req.dst, req)

		del self.access_points[switch.switch.dp.id]

		self.logger.info("Switch <" + str(hex(switch.switch.dp.id)) + "> does no longer offers access point capabilities")


	def _write_ap_rules(self, switch):
		"""
		Initialiaze APs OpenFlow rules
		"""
		# Send Router Solicitations to the Controller
		match = ofp_parser.OFPMatch(in_port = switch.ap_conf.port.port_no, 
									eth_type = ether.ETH_TYPE_IPV6,
									ip_proto = inet.IPPROTO_ICMPV6,
									icmpv6_type = icmpv6.ND_ROUTER_SOLICIT)
		actions = [ofp_parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
		instructions = [ofp_parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
		req = EventWriteOFRule(OFRule(switch, match, actions, instructions, table_id = OF_TABLE_NEIGH))
		self.send_event(req.dst, req)


	@set_ev_cls(EventUEConnected, MAIN_DISPATCHER)
	def _handler_ue_connected(self, ev):
		"""
		Handler for EventUEConnected
		1) Add the UE to UE's attachment point served UEs
		2) Add UE's IPv6 local address to current UE's attachment 
		   point neighbors
		3) Remove UE's IPv6 local address from previous UE's attachment 
		   point neighbors
		"""
		self.connected_ues[ev.ue.hw_addr] = ev.ue

		# Add IPv6 local address
		req = EventAddNeighborNode(ev.ue.attachment.switch, ev.ue.attachment.port, ev.ue.ipv6_addr, ev.ue.hw_addr)
		self.send_event(req.dst, req)

		# Remove the old rules
		prev_att = ev.ue.get_prev_attachment()
		if prev_att and prev_att.switch != ev.ue.attachment.switch and prev_att.port != ev.ue.attachment.port:
			# Remove IPv6 local address
			req = EventRemoveNeighborNode(prev_att.switch, prev_att.port, ev.ue.ipv6_addr, ev.ue.hw_addr)
			self.send_event(req.dst, req)


	@set_ev_cls(EventUEDisconnected, MAIN_DISPATCHER)
	def _handler_ue_disconnected(self, ev):
		"""
		Handler for EventUEDisconnected
		1) Remove UE's IPv6 local address from current UE's attachment 
		   point neighbors
		2) Remove UE's IPv6 global addresses from current UE's attachment 
		   point neighbors
		3) Remove the UE from UE's attachment point served UEs
		"""
		prev_att = ev.ue.get_prev_attachment()
		if prev_att:
			# Remove IPv6 local address
			req = EventRemoveNeighborNode(prev_att.switch, prev_att.port, ev.ue.ipv6_addr, ev.ue.hw_addr)
			self.send_event(req.dst, req)

		try:
			del self.connected_ues[ev.ue.hw_addr]
		except KeyError:
			pass


	@set_ev_cls(EventNodeUnreachable, MAIN_DISPATCHER)
	def _handler_node_unreachable(self, ev):
		"""
		Handler for EventNodeUnreachable
		When a node becomes unreachable, if the node is an active UE,
		raise an EventUEUnreachable
		"""
		if ev.node.hw_addr in self.connected_ues \
		and ev.switch.switch.dp.id == self.connected_ues[ev.node.hw_addr].attachment.switch.switch.dp.id \
		and ev.port.port_no == self.connected_ues[ev.node.hw_addr].attachment.port.port_no:
			req = EventUEUnreachable(self.connected_ues[ev.node.hw_addr])
			self.send_event(req.dst, req)


	@set_ev_cls(EventSwitchEnter, MAIN_DISPATCHER)
	def _handler_switch_enter(self, ev):
		"""
		Handler for EventSwitchEnter.
		Update the network topology stored locally.
		"""
		if ev.switch.is_ap and ev.switch.switch.dp.id not in self.access_points:
			self._add_switch_ap(ev.switch)
	
	
	@set_ev_cls(EventSwitchUpdate, MAIN_DISPATCHER)
	def _handler_switch_update(self, ev):
		if ev.switch.is_ap and ev.switch.switch.dp.id not in self.access_points:
			self._add_switch_ap(ev.switch)
		elif not ev.switch.is_ap and ev.switch.switch.dp.id in self.access_points:
			self._del_switch_ap(ev.switch)
	

	@set_ev_cls(EventSwitchLeave, MAIN_DISPATCHER)
	def _handler_switch_leave(self, ev):
		"""
		Handler for EventSwitchLeave.
		Update the network topology stored locally.
		"""
		if ev.switch.switch.dp.id in self.access_points:
			self._del_switch_ap(ev.switch)
