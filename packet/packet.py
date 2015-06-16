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

from event import *
# End import from iJOIN solution files

# Start import from Ryu files
from ryu.base import app_manager

from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER

from ryu.ofproto import ofproto_v1_3 as ofproto
from ryu.controller.ofp_event import EventOFPPacketIn

from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import icmpv6
from ryu.lib.packet import ipv6
# End import from Ryu files




class Packet(app_manager.RyuApp):
	"""
	================ =========================================================
	Attribute        Description
	================ =========================================================
	OFP_VERSIONS     Declaration of supported OFP version
	_EVENTS          The events' list to which the RyuApp is subscribed to
	================ =========================================================
	"""
	OFP_VERSIONS = [ofproto.OFP_VERSION]
	_EVENTS = [EventRSReceived, EventNSReceived, EventNAReceived, EventUnknownIPReceived]


	def __init__(self, *args, **kwargs):
		super(Packet, self).__init__(*args, **kwargs)
		self.logger = log.get_logger(self.name)


	@set_ev_cls(EventOFPPacketIn, MAIN_DISPATCHER)
	def _handler_packet_in(self, ev):
		"""
		Handler for ofp_event.EventOFPPacketIn
		In this function raw packets are captured.
		Once a meaningful packet is detected, raise the associated event.
		"""
		msg = ev.msg
		pkt = packet.Packet(msg.data)
		
		p_eth = pkt.get_protocol(ethernet.ethernet)
		p_ipv6 = pkt.get_protocol(ipv6.ipv6)
		p_icmpv6 = pkt.get_protocol(icmpv6.icmpv6)
		if p_eth and p_ipv6 and p_icmpv6 and p_icmpv6.type_ == icmpv6.ND_ROUTER_SOLICIT:
			ev = EventRSReceived(msg)
			self.send_event_to_observers(ev)
		elif p_eth and p_ipv6 and p_icmpv6 and p_icmpv6.type_ == icmpv6.ND_NEIGHBOR_SOLICIT:
			ev = EventNSReceived(msg)
			self.send_event_to_observers(ev)
		elif p_eth and p_ipv6 and p_icmpv6 and p_icmpv6.type_ == icmpv6.ND_NEIGHBOR_ADVERT:
			ev = EventNAReceived(msg)
			self.send_event_to_observers(ev)
		elif p_eth and p_ipv6:
			ev = EventUnknownIPReceived(msg)
			self.send_event_to_observers(ev)
