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

from static import OF_TABLE_ROUTING
from static import OF_TABLE_UES

from switch import OFRule

from event import *

from nmm.event import EventTopologyUpdate
from nmm.event import EventWriteOFRule
from nmm.event import EventDelOFRule

from amm.event import EventUEAnchorsUpdate
# End import from iJOIN solution files

# Start import from Ryu files
from ryu.base import app_manager

from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER

from ryu.ofproto import ether
from ryu.ofproto import inet

from ryu.lib.packet import icmpv6

from ryu.ofproto import ofproto_v1_3 as ofproto
from ryu.ofproto import ofproto_v1_3_parser as ofp_parser
# End import from Ryu files




class Teem(app_manager.RyuApp):
	"""
	================ =========================================================
	Attribute        Description
	================ =========================================================
	OFP_VERSIONS     Declaration of supported OFP version
	_EVENTS			 The list of events provided by the RyuApp
	================ =========================================================
	"""
	OFP_VERSIONS = [ofproto.OFP_VERSION]
	_EVENTS = [EventRoutingUpdate]

	
	def __init__(self, *args, **kwargs):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		switches         The dictionary storing the switches.
		previous         The previous dictionary calculated by Dijkstra
		distance         The distance dictionary calculated by Dijkstra		
		================ =========================================================
		"""	
		super(Teem, self).__init__(*args, **kwargs)
		self.logger = log.get_logger(self.name)
		self.switches = {}
		self.previous = {}
		self.distance = {}
		self.path = {}
		self.routing_ofr = {}
		self.ue_ofr = {}


	def _dijkstra(self, start_sw):
		"""
		Compute Dijkstra over the network topology starting from start_sw_dpid
		"""
		previous = {}
		distance = {}
		
		# Initialization
		for sw in self.switches.keys():
			distance[sw] = float('inf')
			previous[sw] = None
		distance[start_sw.switch.dp.id] = 0

		q = self.switches.keys()
		while q:
			u = q[0]
			for node in q[1:]:
				if (u not in distance) or ((node in distance) and (distance[node] < distance[u])):
					u = node
			q.remove(u)

			for v, link in self.switches[u].links.iteritems():
				for l in link:
					if v in q:
						alt = distance[u] + l.weight
						if (v not in distance) or (alt < distance[v]):
							distance[v] = alt
							previous[v] = l

		return distance, previous


	def _extract_path(self, start_sw, end_sw):
		"""
		Extract start<->end path composed by Link objects
		"""
		start = start_sw.switch.dp.id
		end = end_sw.switch.dp.id
		assert end in self.previous[start]

		path = []
		u = end

		while self.previous[start][u] is not None:
			path = [self.previous[start][u]] + path
			u = self.previous[start][u].link.src.dpid

		return path

	
	def _get_routing_of_rule(self, path):
		"""
		Write the OpenFlow rules along the computed routing path 
		"""
		ofrs = {}
		try:
			start_sw = self.switches[path[0].link.src.dpid]
			end_sw = self.switches[path[-1].link.dst.dpid]

			# Forwarding based on destination MAC unicast addr	
			match = ofp_parser.OFPMatch(eth_dst = end_sw.hw_addr)
			for p in path:
				out_port = p.link.src.port_no
				if match.get('in_port') == out_port:
					out_port = ofproto.OFPP_IN_PORT

				actions = [ofp_parser.OFPActionOutput(out_port)]
				instructions = [ofp_parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
				ofr = OFRule(self.switches[p.link.src.dpid], match, actions, instructions, table_id = OF_TABLE_ROUTING)
				ofrs[ofr.key] = ofr
				match = ofp_parser.OFPMatch(eth_dst = end_sw.hw_addr)
		except IndexError:
			self.logger.debug("Index error in _get_path_of_rule")

		return ofrs


	def _update_routing(self):
		"""
		Compute the routing on the network topology
		and send EventRoutingUpdate event
		"""
		for sw_dpid, sw in self.switches.iteritems():
			distance, previous = self._dijkstra(sw)
			self.previous[sw_dpid] = previous
			self.distance[sw_dpid] = distance


		ofrs = {}
		paths = {}
		for swa_dpid, swa in self.switches.iteritems():
			for swb_dpid, swb in self.switches.iteritems():
				if swa_dpid not in paths:
					paths[swa_dpid] = {}

				paths[swa_dpid][swb_dpid] = self._extract_path(swa, swb)
				ofrs_path = self._get_routing_of_rule(paths[swa_dpid][swb_dpid])
				ofrs = dict(ofrs.items() + ofrs_path.items())

		# Write new rules
		for ofr in ofrs.itervalues():
			req = EventWriteOFRule(ofr)
			self.send_event(req.dst, req)

		# Delete old rules
		diff = set(self.routing_ofr.keys()) - set(ofrs.keys())
		for key in diff:
			req = EventDelOFRule(self.routing_ofr[key])
			self.send_event(req.dst, req)

		self.routing_ofr = ofrs
		self.path = paths

		ev = EventRoutingUpdate(self.previous, self.distance)
		self.send_event_to_observers(ev)


	def _get_ue_ul_of_rule(self, ue, path, anchor):
		"""
		Write the OpenFlow rules along the computed routing path 
		"""
		ofrs = {}
		try:
			# Forwarding based on destination MAC unicast addr	
			in_port = [self.switches[path[0].link.src.dpid].ap_conf.port.port_no]
			for p in path:
				for inp in in_port:
					out_port = p.link.src.port_no
					if inp == out_port:
						out_port = ofproto.OFPP_IN_PORT

					match = ofp_parser.OFPMatch(in_port = inp,
												eth_type = ether.ETH_TYPE_IPV6,
												ipv6_src = (':'.join(anchor.nw_prefix), ipv6_utils.ipv6_mask_from_cidr(anchor.nw_prefix_len)))
					actions = [ofp_parser.OFPActionSetField(eth_src = self.switches[p.link.src.dpid].hw_addr),
								ofp_parser.OFPActionSetField(eth_dst = self.switches[p.link.dst.dpid].hw_addr),
								ofp_parser.OFPActionOutput(out_port)]
					instructions = [ofp_parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
				
					ofr = OFRule(self.switches[p.link.src.dpid], match, actions, instructions, table_id = OF_TABLE_UES)
					ofrs[ofr.key] = ofr

					in_port = [p.link.dst.port_no]

		except IndexError:
			self.logger.debug("Index error in _get_ue_ul_of_rule")

		return ofrs


	def _get_ue_dl_of_rule(self, ue, path, anchor):
		"""
		Write the OpenFlow rules along the computed routing path 
		"""
		ofrs = {}
		try:
			# Forwarding based on destination MAC unicast addr	
			in_port = [self.switches[path[0].link.src.dpid].gw_conf.port.port_no]
			for p in path:
				for inp in in_port:
					out_port = p.link.src.port_no
					if inp == out_port:
						out_port = ofproto.OFPP_IN_PORT
					
					for ipv6_addr in [ue.ipv6_addr, ipv6_utils.ipv6_global_from_mac(anchor.nw_prefix, anchor.nw_prefix_len, ue.hw_addr)]:
						match = ofp_parser.OFPMatch(in_port = inp,
													eth_type = ether.ETH_TYPE_IPV6,
													ipv6_dst = ipv6_addr)
						actions = [ofp_parser.OFPActionSetField(eth_src = self.switches[p.link.src.dpid].hw_addr),
									ofp_parser.OFPActionSetField(eth_dst = self.switches[p.link.dst.dpid].hw_addr),
									ofp_parser.OFPActionOutput(out_port)]
						instructions = [ofp_parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
				
						ofr = OFRule(self.switches[p.link.src.dpid], match, actions, instructions, table_id = OF_TABLE_UES)
						ofrs[ofr.key] = ofr
			
						# ICMPv6 target	
						for icmpv6_type in [icmpv6.ND_NEIGHBOR_SOLICIT, icmpv6.ND_NEIGHBOR_ADVERT]:
							match = ofp_parser.OFPMatch(in_port = inp,
														eth_type = ether.ETH_TYPE_IPV6,
														ip_proto = inet.IPPROTO_ICMPV6,
														icmpv6_type = icmpv6_type,
														ipv6_nd_target = ipv6_addr)
							actions = [ofp_parser.OFPActionOutput(out_port)]
							instructions = [ofp_parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
				
							ofr = OFRule(self.switches[p.link.src.dpid], match, actions, instructions, table_id = OF_TABLE_UES)
							ofrs[ofr.key] = ofr

				in_port = [p.link.dst.port_no]

			match = ofp_parser.OFPMatch(in_port = in_port[0],
										eth_type = ether.ETH_TYPE_IPV6,
										ipv6_dst = (':'.join(anchor.nw_prefix), ipv6_utils.ipv6_mask_from_cidr(anchor.nw_prefix_len)))
			actions = [ofp_parser.OFPActionSetField(eth_src = anchor.gw.hw_addr),
						ofp_parser.OFPActionSetField(eth_dst = ue.hw_addr),
						ofp_parser.OFPActionOutput(self.switches[path[-1].link.dst.dpid].ap_conf.port.port_no)]
			instructions = [ofp_parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
			
			ofr = OFRule(self.switches[path[-1].link.dst.dpid], match, actions, instructions, table_id = OF_TABLE_UES)
			ofrs[ofr.key] = ofr

		except IndexError:
			self.logger.debug("Index error in _get_ue_dl_of_rule")

		return ofrs


	@set_ev_cls(EventUEAnchorsUpdate, MAIN_DISPATCHER)
	def _handler_ue_anchor_update(self, ev):
		if ev.ue.hw_addr not in self.ue_ofr:
			self.ue_ofr[ev.ue.hw_addr] = {}

		ap = ev.ue.attachment.switch

		ofrs = {}
		for anch_dpid, anch in ev.ue.attachment.anchors.iteritems():		
			path_ul = self.path[ap.switch.dp.id][anch_dpid]
			path_dl = self.path[anch_dpid][ap.switch.dp.id]

			ofrs_ul = self._get_ue_ul_of_rule(ev.ue, path_ul, anch)
			ofrs_dl = self._get_ue_dl_of_rule(ev.ue, path_dl, anch)

			ofrs = dict(ofrs.items() + ofrs_ul.items() + ofrs_dl.items())

		# Write new rules
		for ofr in ofrs.itervalues():
			req = EventWriteOFRule(ofr)
			self.send_event(req.dst, req)

		# Delete old rules
		diff = set(self.ue_ofr[ev.ue.hw_addr].keys()) - set(ofrs.keys())
		for key in diff:
			req = EventDelOFRule(self.ue_ofr[ev.ue.hw_addr][key])
			self.send_event(req.dst, req)

		self.ue_ofr[ev.ue.hw_addr] = ofrs


	@set_ev_cls(EventTopologyUpdate, MAIN_DISPATCHER)
	def _handler_topology_update(self, ev):
		"""
		Handler for EventTopologyUpdate.
		Update the network topology stored locally.
		"""
		self.switches = ev.switches
		# Update the routing according to new topology
		self._update_routing()
