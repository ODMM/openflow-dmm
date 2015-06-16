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
import time
import threading

from static import OF_TABLE_NEIGH

from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv6
from ryu.lib.packet import icmpv6

from ryu.base import app_manager

from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER

from ryu.ofproto import ether
from ryu.ofproto import inet
from ryu.ofproto import ofproto_v1_3 as ofproto
from ryu.ofproto import ofproto_v1_3_parser as ofp_parser
# End import from Ryu files

# Start import from iJOIN solution files
import log

import ipv6_utils

from node import Node
from node import Attachment

from switch import OFRule

from event import *

from timer.event import EventTimer1sec

from nmm.event import EventWriteOFRule
from nmm.event import EventDelOFRule
from nmm.event import EventPushPacket
from nmm.event import EventProcessPacket

from packet.event import EventNSReceived
from packet.event import EventNAReceived
from packet.event import EventUnknownIPReceived
# End import from iJOIN solution files




class NeighborAdvertisement:
	"""
	Build a Neighbor Advertisement Packet
	"""
	def __init__(self, mac_src, mac_dst, ipv6_src, ipv6_dst, is_router):
		"""
		================ =========================================================
		Input Parameter  Description
		================ =========================================================
		mac_src			 String instance
		mac_dst			 String instance
		ipv6_src		 String instance
		ipv6_dst		 String instance
		is_router		 Boolean instance.
		================ =========================================================
		================ =========================================================
		Attribute        Description
		================ =========================================================
		pkt              The Neighbor Advertisement generated packet
		================ =========================================================
		"""
		self.pkt = packet.Packet()

		e = ethernet.ethernet(mac_dst, mac_src, ether.ETH_TYPE_IPV6)
		i6 = ipv6.ipv6(src = ipv6_src, dst = ipv6_dst, nxt = inet.IPPROTO_ICMPV6)

		if is_router:
			res = 7
		else:
			res = 3

		ic = icmpv6.icmpv6(type_ = icmpv6.ND_NEIGHBOR_ADVERT,
				data = icmpv6.nd_neighbor(dst = ipv6_src, option = icmpv6.nd_option_tla(hw_src = mac_src), res = res))

		self.pkt.add_protocol(e)
		self.pkt.add_protocol(i6)
		self.pkt.add_protocol(ic)


class NeighborSolicitation:
	"""
	Build a Neighbor Solicitation Packet
	"""
	def __init__(self, mac_src, mac_dst, ipv6_src, ipv6_dst, ipv6_tgt):
		"""
		================ =========================================================
		Input Parameter  Description
		================ =========================================================
		mac_src			 String instance
		mac_dst			 String instance
		ipv6_src		 String instance
		ipv6_dst		 String instance
		ipv6_tgt		 String instance
		================ =========================================================
		================ =========================================================
		Attribute        Description
		================ =========================================================
		pkt              The Neighbor Solicitation generated packet
		================ =========================================================
		"""
		self.pkt = packet.Packet()

		e = ethernet.ethernet(mac_dst, mac_src, ether.ETH_TYPE_IPV6)
		i6 = ipv6.ipv6(src = ipv6_src, dst = ipv6_dst, nxt = inet.IPPROTO_ICMPV6)
		ic = icmpv6.icmpv6(type_ = icmpv6.ND_NEIGHBOR_SOLICIT,
				data = icmpv6.nd_neighbor(dst = ipv6_tgt, option = icmpv6.nd_option_sla(hw_src = mac_src)))

		self.pkt.add_protocol(e)
		self.pkt.add_protocol(i6)
		self.pkt.add_protocol(ic)




class RouterAdvertisement:
	"""
	Build a Router Advertisement Packet
	"""
	def __init__(self, mac_src, mac_dst, ipv6_src, ipv6_dst, rou_l, ipv6_options):
		"""
		================ =========================================================
		Input Parameter  Description
		================ =========================================================
		mac_src			 String instance
		mac_dst			 String instance
		ipv6_src		 String instance
		ipv6_dst		 String instance
		rou_l			 Int instance
		ipv6_options	 Tuple instance: (prefix, prefix_length, valid_lft,
										  preferred_lft)
		================ =========================================================
		================ =========================================================
		Attribute        Description
		================ =========================================================
		pkt              The Neighbor Solicitation generated packet
		================ =========================================================
		"""
		self.pkt = packet.Packet()

		e = ethernet.ethernet(mac_dst, mac_src, ether.ETH_TYPE_IPV6)
		i6 = ipv6.ipv6(src = ipv6_src, dst = ipv6_dst, nxt = inet.IPPROTO_ICMPV6)

		# ipv6_options element structure: (prefix, prefix_length, valid_lft, preferred_lft)
		options = []
		for ipv6_opt in ipv6_options:
			options.append(icmpv6.nd_option_pi(prefix = ipv6_opt[0], pl = ipv6_opt[1], val_l = ipv6_opt[2], pre_l = ipv6_opt[3], res1 = 2))
		options.append(icmpv6.nd_option_sla(hw_src = mac_src))

		ic = icmpv6.icmpv6(type_ = icmpv6.ND_ROUTER_ADVERT,
				data = icmpv6.nd_router_advert(rou_l = rou_l, options = options))

		self.pkt.add_protocol(e)
		self.pkt.add_protocol(i6)
		self.pkt.add_protocol(ic)




class Ndisc(app_manager.RyuApp):
	"""
	================ =========================================================
	Attribute        Description
	================ =========================================================
	OFP_VERSIONS     Declaration of supported OFP version
	_EVENTS          The list of events provided by the RyuApp
	================ =========================================================
	"""
	OFP_VERSIONS = [ofproto.OFP_VERSION]
	_EVENTS = [EventNodeReachable, EventNodeUnreachable]


	def __init__(self, *args, **kwargs):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		switches         The dictionary storing the switches enabled for Ndisc
		_pending_solicit The dictionary storing the nodes being solicited
		_unknown_packets The dictionary storing the packets with unkwon dst.
		================ =========================================================
		"""	
		super(Ndisc, self).__init__(*args, **kwargs)
		self.logger = log.get_logger(self.name)
		self.switches = {}

		self.ndisc_of_rule = {}

		self._known_nodes = {}
		self._known_solicit_counter = {}

		self._unknown_nodes = {}
		self._unknown_packets = {}
		self._unknown_solicit_counter = {}
	

	@set_ev_cls(EventTimer1sec, MAIN_DISPATCHER)
	def _handler_timer_1_sec_a(self, ev):
		"""
		Discover if there are new neighbors
		When the UE does not respond for 5 times in a row,
		remove the UE from ues dictionaty and trigger an 
		EventUEDisconnected event.
		"""
		node_unreachable = []
		for sw_dpid, u_ipv6_addr in self._unknown_nodes.iteritems():
			# Solicit unknown nodes
			for node in self._unknown_nodes[sw_dpid].itervalues():
				if self._unknown_solicit_counter[sw_dpid][node.ipv6_addr] >= 5:
					node_unreachable.append(node)
				else:
					self._unknown_solicit_counter[sw_dpid][node.ipv6_addr] += 1
				# I don't know where the node is, let's try on all ports
				switch = self.switches[sw_dpid]
				for port in switch.switch.ports:
					self._send_neighbor_solicitation(switch, port, node.ipv6_addr)

		for node in node_unreachable:
			self._miss_neighbor_node(node.attachment.switch, node.ipv6_addr)


	@set_ev_cls(EventTimer1sec, MAIN_DISPATCHER)
	def _handler_timer_1_sec_b(self, ev):
		"""
		Check periodically if a UE responds to Neighbor	Soliciations. 
		When the UE does not respond for 5 times in a row,
		remove the UE from ues dictionaty and trigger an 
		EventUEDisconnected event.
		"""
		node_unreachable = []
		for sw_dpid, neighbors in self._known_nodes.iteritems():
			# Solicit well-known neighbors
			for node in neighbors.itervalues():
				if self._known_solicit_counter[sw_dpid][node.ipv6_addr] >= 5:
					node_unreachable.append(node)
				else:
					self._known_solicit_counter[sw_dpid][node.ipv6_addr] += 1
					self._send_neighbor_solicitation(node.attachment.switch, node.attachment.port, node.ipv6_addr)
		
		for node in node_unreachable:
			ev = EventNodeUnreachable(node.attachment.switch, node.attachment.port, node)
			self.send_event_to_observers(ev)

			self._remove_neighbor_node(node.attachment.switch, node.attachment.port, node.ipv6_addr, node.hw_addr)
	

	def _send_router_advertisement(self, switch, port, anch, eth_dst, ipv6_dst):
		"""
		Send a Router Advertisement packet to the node 
		announcing anch's prefix.
		"""
		options = [(':'.join(anch.nw_prefix), anch.nw_prefix_len, anch.valid_lft, anch.preferred_lft)]

		eth_src = anch.gw.hw_addr
		ipv6_src = anch.gw.ipv6_local_ucast_addr

		# Create a router advertisment with the extracted info
		router_advert = RouterAdvertisement(eth_src, eth_dst, ipv6_src, ipv6_dst, anch.router_lft, options)
		# Send the router advertisment
		pkt = router_advert.pkt
		pkt.serialize()

		req = EventPushPacket(switch, port, pkt)
		self.send_event(req.dst, req)


	def _send_neighbor_solicitation(self, switch, port, ipv6_target):
		"""
		Send a Neighbor Solicitation packet to ipv6_target.
		The packet is sent through the the switch's port.
		"""
		eth_src = switch.hw_addr
		ipv6_src = switch.ipv6_local_ucast_addr

		eth_dst = '33:33:00:00:00:01'
		ipv6_dst = 'ff02::1'

#		# A Solicited-Node multicast address
#		ipv6_mst = ipv6_utils.ipv6_local_mcast_from_local(ipv6_dst)
#		# Ethernet Solicited-Node multicast address
#		mac_dst = ipv6_utils.mac_mcast_from_ipv6_local_mcast(ipv6_mst)

		# Create a Neighbor Soliciation with the extracted info      
		neighbor_solicit = NeighborSolicitation(eth_src, eth_dst, ipv6_src, ipv6_dst, ipv6_target)
		# Send the Neighbor Solicitation
		pkt = neighbor_solicit.pkt
		pkt.serialize()
		
		req = EventPushPacket(switch, port, pkt)
		self.send_event(req.dst, req)

			
	def _send_neighbor_advertisement(self, switch, port, eth_dst):
		"""
		Send a Neighbor Advertisement packet to eth_dst.
		The packet is sent through the the switch.
		The switch uses the installed OpenFlow rules to decide
		where to send the Neighbor Advertisement packet.
		"""
		eth_src = switch.hw_addr
		ipv6_src = switch.ipv6_local_ucast_addr

		eth_dst = eth_dst
		ipv6_dst = ipv6_utils.ipv6_local_ucast_from_mac(eth_dst)

		# Create a Neighbor Advertisment with the extracted info      
		nd_neighbor_adv = NeighborAdvertisement(eth_src, eth_dst, ipv6_src, ipv6_dst, switch.is_gw)
		pkt = nd_neighbor_adv.pkt
		pkt.serialize()
		# Send the Neighbor Advertisment
		req = EventPushPacket(switch, port, pkt)
		self.send_event(req.dst, req)

	
	def _get_ndisc_of_rule(self, switch):
		"""
		Write the OpenFlow rules required for enabling Ndisc on the switch.
		1) Send to the Controller all Neighbor Solicitation having switch's 
		   ipv6 local address as icmpv6 target
		2) Send to the Controller all Neighbor Advertisement having swwitch's
		   ipv6 local address as destination ipv6 address
		"""
		ofrs = {}

		# Rule for Neighbor Solicitation
		match = ofp_parser.OFPMatch(eth_type = ether.ETH_TYPE_IPV6,
									ip_proto = inet.IPPROTO_ICMPV6,
									icmpv6_type = icmpv6.ND_NEIGHBOR_SOLICIT,
									ipv6_nd_target = switch.ipv6_local_ucast_addr)
		actions = [ofp_parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
		instructions = [ofp_parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
		ofr = OFRule(switch, match, actions, instructions, table_id = OF_TABLE_NEIGH)
		ofrs[ofr.key] = ofr

		# Rule for Neighbor Advertisment
		match = ofp_parser.OFPMatch(eth_type = ether.ETH_TYPE_IPV6,
									ip_proto = inet.IPPROTO_ICMPV6,
									ipv6_dst = switch.ipv6_local_ucast_addr,
									icmpv6_type = icmpv6.ND_NEIGHBOR_ADVERT)
		actions = [ofp_parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
		instructions = [ofp_parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
		ofr = OFRule(switch, match, actions, instructions, table_id = OF_TABLE_NEIGH)
		ofrs[ofr.key] = ofr

		return ofrs

	
	def _add_neighbor_node(self, switch, port, ipv6_addr, hw_addr):
		"""
		Add a node having ipv6_addr as ipv6 addr and hw_addr as
		hardware address to switch port's neighbors
		"""
		node = Node(hw_addr, ipv6_addr)
		node.set_attachment(Attachment(switch, port))

		self._known_nodes[switch.switch.dp.id][ipv6_addr] = node
		self._known_solicit_counter[switch.switch.dp.id][ipv6_addr] = 0
		ofrs = self._get_neigh_of_rule(node)

		for ofr in ofrs.itervalues():			
			req = EventWriteOFRule(ofr)
			self.send_event(req.dst, req)


	def _remove_neighbor_node(self, switch, port, ipv6_addr, hw_addr):
		"""
		Remove a node having ipv6_addr as ipv6 addr from switch port's neighbors
		"""
		node = Node(hw_addr, ipv6_addr)
		node.set_attachment(Attachment(switch, port))

		ofrs = self._get_neigh_of_rule(node)
		for ofr in ofrs.itervalues():			
			req = EventDelOFRule(ofr)
			self.send_event(req.dst, req)

		try:
			del self._known_solicit_counter[switch.switch.dp.id][ipv6_addr]
			del self._known_nodes[switch.switch.dp.id][ipv6_addr]
		except KeyError:
			pass


	def _discover_neighbor_node(self, switch, ipv6_addr):
		"""
		Discover if there is a neighbor with ipv6 addr ipv6_addr connected to the switch
		"""
		node = Node(ipv6_addr = ipv6_addr)
		node.set_attachment(Attachment(switch, None))
		self._unknown_nodes[switch.switch.dp.id][ipv6_addr] = node
		self._unknown_solicit_counter[switch.switch.dp.id][ipv6_addr] = 0
		# I don't know where the destination node is, let's try on all ports
		for port in switch.switch.ports:
			self._send_neighbor_solicitation(switch, port, ipv6_addr)

	
	def _add_discovered_neighbor_node(self, switch, port, ipv6_addr, hw_addr):
		"""
		Add a neighbor to be discovered on the switch
		"""
		try:
			del self._unknown_nodes[switch.switch.dp.id][ipv6_addr]
			self._add_neighbor_node(switch, port, ipv6_addr, hw_addr)

			for p in self._unknown_packets[switch.switch.dp.id][ipv6_addr]:
				req = EventProcessPacket(switch, p)
				self.send_event(req.dst, req)
		except KeyError:
			pass
		finally:
			node = Node(hw_addr, ipv6_addr)
			node.set_attachment(Attachment(switch, port))			

			ev = EventNodeReachable(switch, port, node)
			self.send_event_to_observers(ev)

			self.logger.info("Node <" + hw_addr + "><" + ipv6_addr + "> discovered on switch " + \
							str(hex(switch.switch.dp.id)) + " port " + str(port.name))


	def _miss_neighbor_node(self, switch, ipv6_addr):
		"""
		Discovery procedure has failed, there is no neighbor with ipv6 addr connected to the switch
		"""
		try:
			del self._unknown_packets[switch.switch.dp.id][ipv6_addr]
			del self._unknown_solicit_counter[switch.switch.dp.id][ipv6_addr]
			del self._unknown_nodes[switch.switch.dp.id][ipv6_addr]
		except KeyError:
			pass


	def _get_neigh_of_rule(self, node):
		"""
		Write the OpenFlow rule for forwarding the packet to the node
		(ipv6, hw_addr) lookup and eth_dst address translation
		"""
		ofrs = {}

		match = ofp_parser.OFPMatch(eth_type = ether.ETH_TYPE_IPV6,
									ipv6_dst = node.ipv6_addr)
		actions = [ofp_parser.OFPActionSetField(eth_src = node.attachment.switch.hw_addr),
					ofp_parser.OFPActionSetField(eth_dst = node.hw_addr),
					ofp_parser.OFPActionOutput(node.attachment.port.port_no)]
		instructions = [ofp_parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
		ofr = OFRule(node.attachment.switch, match, actions, instructions, table_id = OF_TABLE_NEIGH)

		ofrs[ofr.key] = ofr

		return ofrs


	@set_ev_cls(EventNSReceived, MAIN_DISPATCHER)
	def _handler_neighbor_solicitation_received(self, ev):
		"""
		Handler for EventNSReceived.
		Send a Neighbor Advertisement upon Neighbor Solicitation reception
		"""
		# Check if the switch is enabled for Ndisc
		if ev.msg.datapath.id in self.switches:
			sw = self.switches[ev.msg.datapath.id]
			port = sw.get_port(ev.msg.match.get("in_port"))

			pkt = packet.Packet(ev.msg.data)
			p_eth = pkt.get_protocol(ethernet.ethernet)
			p_ipv6 = pkt.get_protocol(ipv6.ipv6)
			p_icmpv6 = pkt.get_protocol(icmpv6.icmpv6)

			target_ipv6 = p_icmpv6.data.dst

			if target_ipv6 == sw.ipv6_local_ucast_addr:
				target_hw = p_eth.src
				if p_ipv6.dst == sw.ipv6_local_mcast_addr:
					target_hw = p_icmpv6.data.option.hw_src
				# Add the node as Neighbor
				self._send_neighbor_advertisement(sw, port, target_hw)
			


	@set_ev_cls(EventNAReceived, MAIN_DISPATCHER)
	def _handler_neighbor_advertisement_received(self, ev):
		"""
		Handler for EventNAReceived.
		Add neighbor to switch's neighbors and add OpenFlow rule 
		upon Neighbor Advertisement reception
		Reset also _pending_solicit counter
		"""
		if ev.msg.datapath.id in self.switches:
			sw = self.switches[ev.msg.datapath.id]
			port = sw.get_port(ev.msg.match.get("in_port"))
			
			pkt = packet.Packet(ev.msg.data)
			p_icmpv6 = pkt.get_protocol(icmpv6.icmpv6)

			target_ipv6 = p_icmpv6.data.dst

			if target_ipv6 in self._known_nodes[sw.switch.dp.id]:
				self._known_solicit_counter[sw.switch.dp.id][target_ipv6] = 0
			elif target_ipv6 in self._unknown_nodes[sw.switch.dp.id]:				
				self._add_discovered_neighbor_node(sw, port, target_ipv6, p_icmpv6.data.option.hw_src)


	@set_ev_cls(EventUnknownIPReceived, MAIN_DISPATCHER)
	def _handler_unknown_ip_received(self, ev):
		"""
		Handler for EventUnknownIPReceived.
		Start Neighbor Discovery procedure when 
		a packet with unkwnon IPv6 dst in received 
		"""
		if ev.msg.datapath.id in self.switches:
			sw = self.switches[ev.msg.datapath.id]

			pkt = packet.Packet(ev.msg.data)
			p_ipv6 = pkt.get_protocol(ipv6.ipv6)

			if p_ipv6.dst not in self._unknown_packets[sw.switch.dp.id]:
				self._unknown_packets[sw.switch.dp.id][p_ipv6.dst] = []
			self._unknown_packets[sw.switch.dp.id][p_ipv6.dst].append(pkt)

			self._discover_neighbor_node(sw, p_ipv6.dst)


	@set_ev_cls(EventNeighRequest)
	def _handler_neigh_request(self, req):
		"""
		Handler for EventNeighRequest.
		Get the neighbors of a given switch.
		"""
		neighs = []
		try:
			if req.dpid is None:
				neighs = neighs = [n for sw in self._known_nodes.itervalues() for n in sw.itervalues()]
			else:
				neighs = self._known_nodes[req.dpid].values()
		except KeyError:
			pass

		rep = EventNeighReply(req.src, neighs)
		self.reply_to_request(req, rep)


	@set_ev_cls(EventAddNeighborNode)
	def _handler_add_neighbor_node(self, ev):
		"""
		Handler for EventAddNeighbor
		Populate switch's neighbors.
		"""
		self._add_neighbor_node(ev.switch, ev.port, ev.ipv6_addr, ev.hw_addr)


	@set_ev_cls(EventRemoveNeighborNode)
	def _handler_remove_neighbor(self, ev):
		"""
		Handler for EventRemoveNeighbor
		Depopulate switch's neighbors.
		"""
		self._remove_neighbor_node(ev.switch, ev.port, ev.ipv6_addr, ev.hw_addr)


	@set_ev_cls(EventEnableNdiscOnSwitch)
	def _enable_ndisc_on_switch(self, ev):
		"""
		Handler for EventEnableNdiscOnSwitch.
		Enable Neighbor Discovery on the switch.
		"""
		self.switches[ev.switch.switch.dp.id] = ev.switch

		self._known_nodes[ev.switch.switch.dp.id] = {}
		self._known_solicit_counter[ev.switch.switch.dp.id] = {}

		self._unknown_nodes[ev.switch.switch.dp.id] = {}
		self._unknown_packets[ev.switch.switch.dp.id] = {}
		self._unknown_solicit_counter[ev.switch.switch.dp.id] = {}		

		self.ndisc_of_rule[ev.switch.switch.dp.id] = {}

		ofrs = self._get_ndisc_of_rule(ev.switch)

		# Write new rules
		for ofr in ofrs.itervalues():
			req = EventWriteOFRule(ofr)
			self.send_event(req.dst, req)

		self.ndisc_of_rule[ev.switch.switch.dp.id] = ofrs


	@set_ev_cls(EventDisableNdiscOnSwitch)
	def _disable_ndisc_on_switch(self, ev):
		"""
		Handler for EventDisableNdiscOnSwitch.
		Disable Neighbor Discovery on the switch.
		"""
		try:
			for ofr in self.ndisc_of_rule[ev.switch.switch.dp.id].itervalues():
				req = EventDelOFRule(ofr)
				self.send_event(req.dst, req)

			del self.ndisc_of_rule[ev.switch.switch.dp.id]

			del self._unknown_nodes[ev.switch.switch.dp.id]
			del self._unknown_packets[ev.switch.switch.dp.id]
			del self._unknown_solicit_counter[ev.switch.switch.dp.id]

			del self._known_solicit_counter[ev.switch.switch.dp.id]
			del self._known_nodes[ev.switch.switch.dp.id]

			del self.switches[ev.switch.switch.dp.id]
		except KeyError:
			self.logger.error("Error in _disable_ndisc_on_switch")


	@set_ev_cls(EventSendNS)
	def _send_ns(self, ev):
		"""
		Handler for EventSendNS.
		Send a Neighbor Solicitation
		"""
		self._send_neighbor_solicitation(ev.switch, ev.port, ev.ipv6_dst)


	@set_ev_cls(EventSendRA)
	def _send_ns(self, ev):
		"""
		Handler for EventSendRA.
		Send a Router Advertisement
		"""
		self._send_router_advertisement(ev.switch, ev.port, ev.anch, ev.eth_dst, ev.ipv6_dst)
