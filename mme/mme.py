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

from static import MN_ETH

from node import UE
from node import Association 

from event import *

from amm.event import EventUEAnchorsUpdate

from teem.event import EventRoutingUpdate

from accesspoint.event import EventUEUnreachable

from packet.event import EventRSReceived

from nmm.event import EventTopologyUpdate
# End import from iJOIN solution files

# Start import from Ryu files
from ryu.base import app_manager

from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls

from ryu.lib.packet import packet
from ryu.lib.packet import ethernet

from ryu.ofproto import ofproto_v1_3 as ofproto
# End import from Ryu files




class Mme(app_manager.RyuApp):
	"""
	================ =========================================================
	Attribute        Description
	================ =========================================================
	OFP_VERSIONS     Declaration of supported OFP version
	_EVENTS          The events' list to which the RyuApp is subscribed to
	================ =========================================================
	"""
	OFP_VERSIONS = [ofproto.OFP_VERSION]
	_EVENTS = [EventUEConnected, EventUEDisconnected]


	def __init__(self, *args, **kwargs):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		switches         The dictionary storing the switches.
		last_ue_id		 The last id assigned to an UE.
		ues              The dictionary storing the UEs.
		================ =========================================================
		"""	
		super(Mme, self).__init__(*args, **kwargs)
		self.logger = log.get_logger(self.name)
		self.switches = {}
		self.last_ue_id = 0
		self.ues = {}


	def manage_association(self, switch, port, ue_hw_addr):
		"""
		Manage a UE association. 
		Create a new association or update the existing one.
		"""
		# Check if UE is already in self.ues dictionary
		if ue_hw_addr in self.ues:
			# Update UE Association
			self.ues[ue_hw_addr].set_attachment(Association(switch, port))
			self.logger.info("UE <%s> connected to <%s>, port %s", ue_hw_addr, str(hex(switch.switch.dp.id)), str(port.port_no))
		else:
			self.last_ue_id += 1
			# Add a new UE creating and a new Association
			self.ues[ue_hw_addr] = UE(self.last_ue_id, ue_hw_addr, ipv6_utils.ipv6_local_ucast_from_mac(ue_hw_addr))
			self.ues[ue_hw_addr].set_attachment(Association(switch, port))
			self.logger.info("UE <%s> connected to <%s>, port %s", ue_hw_addr, str(hex(switch.switch.dp.id)), str(port.port_no))

		ev = EventUEConnected(self.ues[ue_hw_addr])
		self.send_event_to_observers(ev)


	@set_ev_cls(EventUEDisconnected, MAIN_DISPATCHER)
	def _ue_disconnected(self, ev):
		"""
		Handler for EventUEDisconnected.
		"""
		pass


	@set_ev_cls(EventUEProfileUpdateRequest)
	def _handler_ue_profile_update_request(self, req):
		"""
		Handler for EventUEProfileUpdateRequest.
		"""
		pass


	@set_ev_cls(EventUERequest)
	def _handler_ue_request(self, req):
		"""
		Handler for EventUERequest.
		Get UE entry.
		"""
		ues = []
		try:
			if req.ue_id is None:
				# reply all list
				ues = self.ues.values()
			elif req.ue_id in self.ues:
				ues = [self.ues[req.ue_id]]
		except KeyError:
			pass

		rep = EventUEReply(req.src, ues)
		self.reply_to_request(req, rep)


	@set_ev_cls(EventUEAnchorsUpdate, MAIN_DISPATCHER)
	def _handler_ue_anchors_update(self, ev):
		"""
		Handler for EventUEAnchorsUpdate.
		Update UE's anchors.
		"""
		self.ues[ev.ue.hw_addr].attachment.anchors = ev.ue.attachment.anchors


	@set_ev_cls(EventUEUnreachable)
	def _handler_ue_unreachable(self, ev):
		"""
		Handler for EventUEUnreachable.
		Reset UE's attachment and raise EventUEDisconnected event.
		"""
		if ev.ue.hw_addr in self.ues:
			self.ues[ev.ue.hw_addr].attachment.anchors = {}
			self.ues[ev.ue.hw_addr].set_attachment(None)
			ev_ud = EventUEDisconnected(ev.ue)
			self.send_event_to_observers(ev_ud)

			prev_att = ev.ue.get_prev_attachment()
			if prev_att:
				self.logger.info("UE <%s> disconnected from <%s>, port %s", ev.ue.hw_addr, 
						str(hex(prev_att.switch.switch.dp.id)), str(prev_att.port.port_no))


	@set_ev_cls(EventRSReceived)
	def _handler_rs_received(self, ev):
		"""
		Handler for EventRSReceived.
		UE attachment is identified by a Router Solicitation sent by the UE.
		"""
		pkt = packet.Packet(ev.msg.data)
		p_eth = pkt.get_protocol(ethernet.ethernet)
		# Check if the UE has mobility support
		if p_eth.src in MN_ETH:
			switch = self.switches[ev.msg.datapath.id]
			port = switch.get_port(ev.msg.match.get("in_port"))
			self.manage_association(switch, port, p_eth.src)
	
	
	@set_ev_cls(EventTopologyUpdate, MAIN_DISPATCHER)
	def _handler_topology_update(self, ev):
		"""
		Handler for EventTopologyUpdate.
		Update the network topology stored locally.
		"""	
		self.switches = ev.switches
