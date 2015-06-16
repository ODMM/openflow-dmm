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
from static import OF_TABLE_ROUTING
from static import OF_TABLE_UNKNOWN

from switch import OFRule

from event import *

from timer.event import EventTimer1sec

from mme.event import EventUEConnected
from mme.event import EventUEDisconnected

from nmm.event import EventWriteOFRule
from nmm.event import EventDelOFRule
from nmm.event import EventSwitchEnter
from nmm.event import EventSwitchUpdate
from nmm.event import EventSwitchLeave

from packet.event import EventUnknownIPReceived

from ndisc.event import EventEnableNdiscOnSwitch
from ndisc.event import EventDisableNdiscOnSwitch
from ndisc.event import EventSendRA

from amm.event import EventUEAnchorsUpdate
# End import from iJOIN solution files

# Start import from Ryu files
import time
import threading

from ryu.base import app_manager

from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER

from ryu.ofproto import ofproto_v1_3 as ofproto
from ryu.ofproto import ofproto_v1_3_parser as ofp_parser

from ryu.ofproto import ether
from ryu.ofproto import inet

from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv6
from ryu.lib.packet import icmpv6
# End import from Ryu files




class Gateway(app_manager.RyuApp):
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
		gateways         The dictionary storing the switches enabled with gateway
						 functionalities
		_check_ue_advert The dictionary storing the UEs being advertised
		isement
		================ =========================================================
		"""	
		super(Gateway, self).__init__(*args, **kwargs)
		self.logger = log.get_logger(self.name)
		self.gateways = {}

		self._check_ue_advertisement = {}


	@set_ev_cls(EventTimer1sec, MAIN_DISPATCHER)
	def _handler_timer_1_sec(self, ev):
		"""
		Check periodically if a UE must be advertised
		"""
		for ue in self._check_ue_advertisement.values():
			for anch in ue.attachment.anchors.itervalues():
				tdiff = time.time() - anch.last_time_advertised
				if (tdiff > (anch.valid_lft - 5) and tdiff < anch.valid_lft):
					self._send_router_advertisement(ue.attachment.switch, ue.attachment.port, anch, ue.hw_addr, ue.ipv6_addr)


	def _send_router_advertisement(self, switch, port, anch, eth_dst, ipv6_dst):
		"""
		Send a Router Advertisement packet
		"""
		req = EventSendRA(switch, port, anch, eth_dst, ipv6_dst)
		self.send_event(req.dst, req)

		anch.last_time_advertised = time.time()


	def _add_switch_gw(self, switch):
		"""
		Add switch to GW list
		"""
		self.gateways[switch.switch.dp.id] = switch
		self._write_gw_rules(switch)

		req = EventEnableNdiscOnSwitch(switch)
		self.send_event(req.dst, req)

		self.logger.info("Switch <" + str(hex(switch.switch.dp.id)) + "> offers gateway capabilities")

	
	def _del_switch_gw(self, switch):
		"""
		Del switch to GW list
		"""
		req = EventDisableNdiscOnSwitch(switch)
		self.send_event(req.dst, req)

		del self.gateways[switch.switch.dp.id]

		self.logger.info("Switch <" + str(hex(switch.switch.dp.id)) + "> does no longer offers gateway capabilities")


	def _write_gw_rules(self, switch):
		"""
		Initialiaze Gateway OpenFlow rules
		"""
		# Send unkown IP dst packets to the controller
		match = ofp_parser.OFPMatch(eth_dst = switch.hw_addr,
									eth_type = ether.ETH_TYPE_IPV6,
									ipv6_src = (':'.join(switch.gw_conf.nw_prefix), ipv6_utils.ipv6_mask_from_cidr(switch.gw_conf.nw_prefix_len)))
		actions = [ofp_parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
		instructions = [ofp_parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
		req = EventWriteOFRule(OFRule(switch, match, actions, instructions, table_id = OF_TABLE_UNKNOWN))
		self.send_event(req.dst, req)


	@set_ev_cls(EventUEAnchorsUpdate, MAIN_DISPATCHER)
	def _handler_ue_anchors_update(self, ev):
		"""
		Handler for EventUEAnchorsUpdate
		Update rules on UE's gateways
		"""
		for anch_dpid, anch in ev.ue.attachment.anchors.iteritems():
			self._send_router_advertisement(ev.ue.attachment.switch, ev.ue.attachment.port, anch, ev.ue.hw_addr, ev.ue.ipv6_addr)


	@set_ev_cls(EventUEConnected, MAIN_DISPATCHER)
	def _handler_ue_conncted(self, ev):
		"""
		Handler for EventUEConnected
		Register the UE
		"""
		self._check_ue_advertisement[ev.ue.id] = ev.ue


	@set_ev_cls(EventUEDisconnected, MAIN_DISPATCHER)
	def _handler_ue_disconncted(self, ev):
		"""
		Handler for EventUEDisconnected
		Remove UE's rules from each gateway
		"""
		try:
			del self._check_ue_advertisement[ev.ue.id]
		except KeyError:
			pass

	
	@set_ev_cls(EventSwitchEnter, MAIN_DISPATCHER)
	def _handler_switch_enter(self, ev):
		"""
		Handler for EventSwitchEnter.
		Update the network topology stored locally.
		"""
		if ev.switch.is_gw and ev.switch.switch.dp.id not in self.gateways:
			self._add_switch_gw(ev.switch)


	@set_ev_cls(EventSwitchUpdate, MAIN_DISPATCHER)
	def _handler_switch_update(self, ev):
		if ev.switch.is_gw and ev.switch.switch.dp.id not in self.gateways:
			self._add_switch_gw(ev.switch)
		elif not ev.switch.is_gw and ev.switch.switch.dp.id in self.gateways:
			self._del_switch_gw(ev.switch)


	@set_ev_cls(EventSwitchLeave, MAIN_DISPATCHER)
	def _handler_switch_leave(self, ev):
		"""
		Handler for EventSwitchLeave.
		Update the network topology stored locally.
		"""
		if ev.switch.switch.dp.id in self.gateways:
			self._del_switch_gw(ev.switch)
