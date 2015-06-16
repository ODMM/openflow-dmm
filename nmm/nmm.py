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
import log

from static import OF_TABLE_NUM
from static import WLAN_IFACE
from static import GW_IFACE

from switch import OFRule
from switch import Switch
from switch import Link
from switch import AccessPointConf
from switch import GatewayConf

from event import *
# End import from iJOIN solution files

# Start import from Ryu files
from ryu.base import app_manager
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.ofproto import ofproto_v1_3 as ofproto
from ryu.ofproto import ofproto_v1_3_parser as ofp_parser
from ryu.topology.api import get_switch
from ryu.topology.event import EventSwitchEnter as RyuEventSwitchEnter
from ryu.topology.event import EventSwitchLeave as RyuEventSwitchLeave
from ryu.topology.event import EventLinkAdd as RyuEventLinkAdd
from ryu.topology.event import EventLinkDelete as RyuEventLinkDelete
from ryu.topology.event import EventPortAdd as RyuEventPortAdd
from ryu.topology.event import EventPortModify as RyuEventPortModify
from ryu.topology.event import EventPortDelete as RyuEventPortDelete
# End import from Ryu files




class Nmm(app_manager.RyuApp):
	"""
	================ =========================================================
	Attribute        Description
	================ =========================================================
	OFP_VERSIONS     Declaration of supported OFP version
	_EVENTS          The list of events provided by the RyuApp
	================ =========================================================
	"""
	OFP_VERSIONS = [ofproto.OFP_VERSION]
	_EVENTS = [EventTopologyUpdate, EventSwitchEnter, EventSwitchUpdate, 
				EventSwitchLeave, EventLinkAdd, EventLinkDelete]



	def __init__(self, *args, **kwargs):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		switches         The dictionary storing the switches as 
		                 custom Switch isntance
		================ =========================================================
		"""
		super(Nmm, self).__init__(*args, **kwargs)
		self.logger = log.get_logger(self.name)

		self.switches = {}
		self.accesspoints = {}
		self.gateways = {}

		self.of_rules = {}


	def _initialise_switch_of_tables(self, switch):
		"""
		Flush the flow table when the switch connects to the controller.
		"""
		# Flush OpenFlow entries
		match = ofp_parser.OFPMatch()
		instructions = []
		actions = []

		datapath = switch.switch.dp
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser

		for i in xrange(1, OF_TABLE_NUM):
			mod = parser.OFPFlowMod(datapath = datapath, cookie = 0,
							cookie_mask = 0, command = ofproto.OFPFC_DELETE,
							idle_timeout = 0, hard_timeout = 0, table_id = i,
							buffer_id = ofproto.OFPCML_NO_BUFFER, out_port = ofproto.OFPP_ANY,
							out_group = ofproto.OFPG_ANY, match = match, instructions = instructions)
			datapath.send_msg(mod)
		
		for i in xrange(0, OF_TABLE_NUM-1):
			instructions = [ofp_parser.OFPInstructionGotoTable(i+1)]
			req = EventWriteOFRule(OFRule(switch, match, actions, instructions, table_id = i, priority = 0))
			self.send_event(req.dst, req)


	def _check_if_ap_port(self, port):
		"""
		Check if a switch port is an access port.
		"""
		return port.name.startswith(WLAN_IFACE)


	def _check_if_gw_port(self, port):
		"""
		Check if a switch port is a gateway port.
		"""
		return port.name.startswith(GW_IFACE)


	def _get_ap_conf(self, switch, port):
		"""
		Get AP configuration.
		"""
		ap_conf = AccessPointConf()
		ap_conf.port = port

		return ap_conf

	
	def _get_gw_conf(self, switch, port):
		"""
		Get GW configuration.
		"""
		gw_conf = GatewayConf()
		gw_conf.port = port
		# FIXME	HARDCODED
		gw_conf.nw_prefix = ('2020', str(hex(switch.switch.dp.id))[-4:],'0','0','0','0','0','0')
		gw_conf.nw_prefix_len = 32

		return gw_conf


	@set_ev_cls(EventPushPacket)
	def _handler_push_packet(self, ev):
		"""
		Send the Packet pkt through the OFPort port.
		"""
		datapath = ev.switch.switch.dp
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser

		actions = [parser.OFPActionOutput(port = ev.port.port_no)]
		out = parser.OFPPacketOut(datapath = datapath,
					buffer_id = ofproto.OFP_NO_BUFFER,
					in_port = ofproto.OFPP_CONTROLLER,
					actions = actions, data = ev.pkt.data)
		datapath.send_msg(out)


	@set_ev_cls(EventProcessPacket)
	def _handler_process_packet(self, ev):
		"""
		Send the Packet pkt through the OFPP_TABLE.
		"""
		datapath = ev.switch.switch.dp
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser

		actions = [parser.OFPActionOutput(port = ofproto.OFPP_TABLE)]
		out = parser.OFPPacketOut(datapath = datapath,
					buffer_id = ofproto.OFP_NO_BUFFER,
					in_port = ofproto.OFPP_CONTROLLER,
					actions = actions, data = ev.pkt.data)
		datapath.send_msg(out)


	@set_ev_cls(EventWriteOFRule)
	def _handler_write_of_rule(self, ev):
		"""
		Write OpenFlow rule on switch.
		If the rule is already present in the switch,
		don't write it again
		"""
		try:
			if ev.of_rule.key not in self.of_rules \
				or self.of_rules[ev.of_rule.key].actions != ev.of_rule.actions:

				datapath = ev.of_rule.switch.switch.dp
				ofproto = datapath.ofproto
				parser = datapath.ofproto_parser

				mod = parser.OFPFlowMod(datapath = datapath, table_id = ev.of_rule.table_id, priority = ev.of_rule.priority, match = ev.of_rule.match, instructions = ev.of_rule.instructions, cookie = ev.of_rule.cookie)
				datapath.send_msg(mod)

				self.of_rules[ev.of_rule.key] = ev.of_rule
		except KeyError:
			pass


	@set_ev_cls(EventDelOFRule)
	def _handler_del_of_rule(self, ev):
		"""
		Delete OpenFlow rule on switch.
		If the rule has been already deleted from the switch,
		don't delete it again
		"""
		try:
			if ev.of_rule.key in self.of_rules:
				datapath = ev.of_rule.switch.switch.dp
				ofproto = datapath.ofproto
				parser = datapath.ofproto_parser

				inst = []
				mod = parser.OFPFlowMod(datapath = datapath, cookie = ev.of_rule.cookie,
									cookie_mask = ev.of_rule.cookie_mask, table_id = ev.of_rule.table_id, 
									command = ofproto.OFPFC_DELETE, idle_timeout = 0, hard_timeout = 0, 
									priority = ev.of_rule.priority, buffer_id = ofproto.OFPCML_NO_BUFFER, 
									out_port = ofproto.OFPP_ANY, out_group = ofproto.OFPG_ANY, 
									match = ev.of_rule.match, instructions = inst)
				datapath.send_msg(mod)

				del self.of_rules[ev.of_rule.key]
		except KeyError:
			pass


	@set_ev_cls(EventSwitchRequest)
	def _handler_switch_request(self, req):
		"""
		Get a switch object given the dpid.
		"""
		switches = []
		try:
			if req.dpid is None:
				# reply all list
				switches = self.switches.values()
			elif req.dpid in self.switches:
				switches = [self.switches[req.dpid]]
		except KeyError:
			pass

		rep = EventSwitchReply(req.src, switches)
		self.reply_to_request(req, rep)


	@set_ev_cls(EventLinkRequest)
	def _handler_link_request(self, req):
		"""
		Get switch's links.
		"""
		links = []
		try:
			if req.dpid is None:
				# reply all list
				links = [in_li for sw in self.switches.itervalues() for li_li in sw.links.itervalues() for in_li in li_li]
			elif req.dpid in self.switches:
				links = [in_li for li_li in self.switches[req.dpid].links.itervalues() for in_li in li_li]
		except KeyError:
			pass

		rep = EventLinkReply(req.src, links)
		self.reply_to_request(req, rep)


	@set_ev_cls(RyuEventSwitchEnter, MAIN_DISPATCHER)
	def _handler_switch_enter(self, ev):
		"""
		Handler for event.EventSwitchEnter
		Add a node to the topology.
		"""
		switch = Switch(ev.switch)
		# Check switch capabilities
		self.switches[ev.switch.dp.id] = switch
		# HARDCODED
		for p in switch.switch.ports:
			if self._check_if_ap_port(p):
				ap_conf = self._get_ap_conf(switch, p)
				switch.is_ap = True
				switch.ap_conf = ap_conf
				self.accesspoints[ev.switch.dp.id] = switch
			elif self._check_if_gw_port(p):
				gw_conf = self._get_gw_conf(switch, p)
				switch.is_gw = True
				switch.gw_conf = gw_conf
				self.gateways[ev.switch.dp.id] = switch
							
		self._initialise_switch_of_tables(switch)

		ev_tu = EventSwitchEnter(switch)
		self.send_event_to_observers(ev_tu)

		ev_tu = EventTopologyUpdate(self.switches)
		self.send_event_to_observers(ev_tu)
		self.logger.info("Switch <" + str(hex(switch.switch.dp.id)) + "> connected")
	

	@set_ev_cls(RyuEventSwitchLeave, MAIN_DISPATCHER)
	def _handler_switch_leave(self, ev):
		"""
		Handler for event.EventSwitchLeave
		Delete a node from the topology.
		"""
		try:
			ev_tu = EventSwitchLeave(self.switches[ev.switch.dp.id])
			self.send_event_to_observers(ev_tu)

			del self.switches[ev.switch.dp.id]

			ev_tu = EventTopologyUpdate(self.switches)
			self.send_event_to_observers(ev_tu)
			self.logger.info("Switch <" + str(hex(ev.switch.dp.id)) + "> disconnected")
		except KeyError:
			pass
	
	
	@set_ev_cls(RyuEventLinkAdd, MAIN_DISPATCHER)
	def _handler_link_add(self, ev):
		"""
		Handler for event.EventLinkAdd
		Add a link to the topology.
		"""
		if ev.link.dst.dpid not in self.switches[ev.link.src.dpid].links:
			self.switches[ev.link.src.dpid].links[ev.link.dst.dpid] = []
		link = Link(ev.link)
		self.switches[ev.link.src.dpid].links[ev.link.dst.dpid].append(link)

		ev_tu = EventLinkAdd(link)
		self.send_event_to_observers(ev_tu)

		ev_tu = EventTopologyUpdate(self.switches)
		self.send_event_to_observers(ev_tu)

		self.logger.info("Link <" + str(hex(ev.link.src.dpid)) + ":" + ev.link.src.name + "> => <" +
						str(hex(ev.link.dst.dpid)) + ":" + ev.link.dst.name +"> appeared")
	
	
	@set_ev_cls(RyuEventLinkDelete, MAIN_DISPATCHER)
	def _handler_link_delete(self, ev):
		"""
		Handler for event.EventLinkDelete
		Delete a link from the topology.
		"""
		try:
			tmp_links = []
			link_to_del = None
			for l in self.switches[ev.link.src.dpid].links[ev.link.dst.dpid]:
				if ((ev.link.src.dpid == l.link.src.dpid and ev.link.src.port_no == l.link.src.port_no)
						and (ev.link.dst.dpid == l.link.dst.dpid and ev.link.dst.port_no == l.link.dst.port_no)):
					link_to_del = l
				else:
					tmp_links.append(l)

			if link_to_del:
				self.switches[ev.link.src.dpid].links[ev.link.dst.dpid] = tmp_links
				
				ev_tu = EventLinkDelete(link_to_del)
				self.send_event_to_observers(ev_tu)

				ev_tu = EventTopologyUpdate(self.switches)
				self.send_event_to_observers(ev_tu)
				self.logger.info("Link <" + str(hex(ev.link.src.dpid)) + ":" + ev.link.src.name + "> => <" +
							str(hex(ev.link.dst.dpid)) + ":" + ev.link.dst.name +"> disappeared")
		except KeyError:
			pass
	
	
	@set_ev_cls(RyuEventPortAdd, MAIN_DISPATCHER)
	def _handler_port_add(self, ev):
		"""
		Overwrite the legacy Ryu Event.
		"""
		try:
			switch = self.switches[ev.port.dpid]
			if self._check_if_ap_port(ev.port):
				ap_conf = self._get_ap_conf(switch, ev.port)
				switch.is_ap = True
				switch.ap_conf = ap_conf
				self.accesspoints[ev.port.dpid] = switch
			elif self._check_if_gw_port(ev.port):
				gw_conf = self._get_gw_conf(switch, ev.port)
				switch.is_gw = True
				switch.gw_conf = gw_conf
				self.gateways[ev.port.dpid] = switch
			
			switch.switch = get_switch(self, ev.port.dpid)[0]
		
			ev_tu = EventSwitchUpdate(switch)
			self.send_event_to_observers(ev_tu)

			self.logger.info("Port add: " + str(ev.port))
		except KeyError:
			pass
		
	
	
	@set_ev_cls(RyuEventPortModify, MAIN_DISPATCHER)
	def _handler_port_modify(self, ev):
		"""
		Overwrite the legacy Ryu Event.
		"""
		try:
			switch = self.switches[ev.port.dpid]
			switch.switch = get_switch(self, ev.port.dpid)[0]
	
			ev_tu = EventSwitchUpdate(switch)
			self.send_event_to_observers(ev_tu)

			self.logger.info("Port modify: " + str(ev.port))
		except KeyError:
			pass
	
	
	@set_ev_cls(RyuEventPortDelete, MAIN_DISPATCHER)
	def _handler_port_delete(self, ev):
		"""
		Overwrite the legacy Ryu Event.
		"""
		try:
			switch = self.switches[ev.port.dpid]
			if self._check_if_ap_port(ev.port):
				switch.is_ap = False
				switch.ap_conf = AccessPointConf()
				del self.accesspoints[ev.port.dpid]
			elif self._check_if_gw_port(ev.port):
				switch.is_gw = False
				switch.gw_conf = GatewayConf()
				del self.gateways[ev.port.dpid]
		
			switch.switch = get_switch(self, ev.port.dpid)[0]
		
			ev_tu = EventSwitchUpdate(switch)
			self.send_event_to_observers(ev_tu)

			self.logger.info("Port delete: " + str(ev.port))
		except KeyError:
			pass
