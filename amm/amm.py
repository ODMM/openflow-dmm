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

from node import Anchor

from event import *

from nmm.event import EventTopologyUpdate

from teem.event import EventRoutingUpdate

from mme.event import EventUEConnected
from mme.event import EventUEDisconnected
# End import from iJOIN solution files

# Start import from Ryu files
import numpy

from ryu.base import app_manager
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.ofproto import ofproto_v1_3 as ofproto
# End import from Ryu files




class Amm(app_manager.RyuApp):
	"""
	================ =========================================================
	Attribute        Description
	================ =========================================================
	OFP_VERSIONS     Declaration of supported OFP version
	_EVENTS          The list of events provided by the RyuApp
	================ =========================================================
	"""
	OFP_VERSIONS = [ofproto.OFP_VERSION]
	_EVENTS = [EventUEAnchorsUpdate]


	def __init__(self, *args, **kwargs):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		switches         The dictionary storing the switches
		gateways         The dictionary storing the switches enabled with
						 gateway functionalities
		================ =========================================================
		"""	
		super(Amm, self).__init__(*args, **kwargs)
		self.logger = log.get_logger(self.name)
		self.ues = {}
		self.switches = {}
		self.gateways = {}
		self.pgw = None


	def _assign_ue_anchors(self, ue):
		"""
		This function selects the gateways for the UE.
		The selection is based on the UE profile.
		An UE can have multiple gateways at the same time but
		only one gateway can be used as default gateway (the 
		others are deprecated gateways).
		"""
		a_dict = {}
		
		prev_att = self.ues[ue.id].get_prev_attachment()
		if prev_att:
			for anch in prev_att.anchors.itervalues():
				a_dict[anch.gw.switch.dp.id] = anch
				a_dict[anch.gw.switch.dp.id].preferred_lft = 0
				self.logger.info("Switch <" + str(hex(anch.gw.switch.dp.id)) + "> " + \
								 "is a deprecated gateway for UE <" + str(self.ues[ue.id].hw_addr) + ">")

		# The default gw
		anch = self._get_closest_ue_anchor(ue)
		if anch:
			a_dict[anch.gw.switch.dp.id] = anch
			self.logger.info("Switch <" + str(hex(anch.gw.switch.dp.id)) + "> " + \
							 "selected as default gateway for UE <" + str(self.ues[ue.id].hw_addr) + ">")

		# Assign the selected gateways to the UE
		self.ues[ue.id].attachment.anchors = a_dict

		ev = EventUEAnchorsUpdate(self.ues[ue.id])
		self.send_event_to_observers(ev)

	
	def _get_closest_ue_anchor(self, ue):
		"""
		Find the Local GW
		"""
		# Find the Local-GW
		dists = {}
		for gw_dpid in self.gateways.keys():
			try:
				dists[gw_dpid] = self.distance[self.ues[ue.id].attachment.switch.switch.dp.id][gw_dpid]
			except KeyError:
				pass

		if dists:
			index = min(dists, key=dists.get)
			if index in self.switches:
				return self._get_anchor_from_gw_ue(self.switches[min(dists, key=dists.get)], ue)

		return self.pgw


	def _get_anchor_from_gw_ue(self, gw, ue):
		"""
		Return an Anchor object.
		"""
		nw_prefix = (gw.gw_conf.nw_prefix[0], 
						gw.gw_conf.nw_prefix[1],
						'{0:08x}'.format(ue.id)[-8:-4], 
						'{0:08x}'.format(ue.id)[-4:], 
						'0', '0', '0', '0')
		return Anchor(gw, nw_prefix)


	@set_ev_cls(EventUEConnected, MAIN_DISPATCHER)
	def _handler_ue_connected(self, ev):
		"""
		Manage UE connection
		"""
		self.ues[ev.ue.id] = ev.ue
		self._assign_ue_anchors(ev.ue)


	@set_ev_cls(EventUEDisconnected, MAIN_DISPATCHER)
	def _handler_ue_disconnected(self, ev):
		"""
		Manage UE disconnection
		"""
		try:
			del self.ues[ev.ue.id]
		except KeyError:
			pass


	@set_ev_cls(EventRoutingUpdate, MAIN_DISPATCHER)
	def _handler_routing_update(self, ev):
		"""
		Handler for EventRoutingUpdate.
		Update the routing stored locally and find the P-GW.
		"""
		self.previous = ev.previous
		self.distance = ev.distance

		# Find the P-GW
		dists = {}
		for gw_dpid in self.gateways.keys():
			try:
				ap_dist = [ap_dist for ap_dpid, ap_dist in self.distance[gw_dpid].iteritems() if ap_dpid in self.switches and self.switches[ap_dpid].is_ap]
				if ap_dist and float('inf') not in ap_dist:
					dists[gw_dpid] = numpy.median(ap_dist)/(1+numpy.var(ap_dist)) 

				if dists:
					index = max(dists, key=dists.get)
					if index in self.switches:
						self.pgw = self.switches[index]
			except KeyError:
				pass

		# Update UE anchors, the topology changed, so select the best anchor
		for ue in self.ues.itervalues():
			self._assign_ue_anchors(ue)


	@set_ev_cls(EventTopologyUpdate, MAIN_DISPATCHER)
	def _handler_topology_update(self, ev):
		"""
		Handler for EventTopologyUpdate.
		Update the network topology stored locally.
		"""
		self.switches = ev.switches

		for sw_dpid, sw in ev.switches.iteritems():
			if sw.is_gw and sw_dpid not in self.gateways:
				self.gateways[sw_dpid] = sw
			if not sw.is_gw and sw_dpid in self.gateways:
				del self.gateways[sw_dpid]
