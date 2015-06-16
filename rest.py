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
from amm.event import EventUEAnchorsUpdate

from mme.event import EventUERequest
from mme.event import EventUEConnected
from mme.event import EventUEDisconnected
from mme.event import EventUEProfileUpdateRequest

from teem.event import EventRoutingUpdate

from ndisc.event import EventNeighRequest
from ndisc.event import EventNodeReachable
from ndisc.event import EventNodeUnreachable

from nmm.event import EventSwitchRequest
from nmm.event import EventLinkRequest
from nmm.event import EventTopologyUpdate
from nmm.event import EventSwitchEnter
from nmm.event import EventSwitchUpdate
from nmm.event import EventSwitchLeave
from nmm.event import EventLinkAdd
from nmm.event import EventLinkDelete

from static import ETH_PATTERN
# End import from iJOIN solution files

# Start import from Ryu files
import json
from webob import Response

from socket import error as SocketError
from ryu.contrib.tinyrpc.exc import InvalidReplyError

from ryu.app.wsgi import ControllerBase
from ryu.app.wsgi import WSGIApplication
from ryu.app.wsgi import websocket
from ryu.app.wsgi import route
from ryu.app.wsgi import WebSocketRPCServer
from ryu.app.wsgi import rpc_public

from ryu.base import app_manager

from ryu.lib import dpid as dpid_lib
from ryu.topology.api import get_switch, get_link

from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER
# End import from Ryu files



class iJOINRestAPI(app_manager.RyuApp):
	_CONTEXTS = {
		'wsgi': WSGIApplication
	}


	def __init__(self, *args, **kwargs):
		super(iJOINRestAPI, self).__init__(*args, **kwargs)
		wsgi = kwargs['wsgi']
		wsgi.register(iJOINController, {'ijoin_api_app': self})
		self._ws_manager = wsgi.websocketmanager


	@set_ev_cls(EventNodeReachable, MAIN_DISPATCHER)
	def _handler_node_reachable(self, ev):
		msg = ev.node.to_dict()
		self._rpc_broadcall('node_reachable', msg)


	@set_ev_cls(EventNodeUnreachable, MAIN_DISPATCHER)
	def _handler_node_unreachable(self, ev):
		msg = ev.node.to_dict()
		self._rpc_broadcall('node_unreachable', msg)


	@set_ev_cls(EventUEConnected, MAIN_DISPATCHER)
	def _handler_ue_connected(self, ev):
		msg = ev.ue.to_dict()
		self._rpc_broadcall('ue_connected', msg)


	@set_ev_cls(EventUEAnchorsUpdate, MAIN_DISPATCHER)
	def _handler_ue_anchors_update(self, ev):
		msg = ev.ue.to_dict()
		self._rpc_broadcall('ue_anchors', msg)


	@set_ev_cls(EventUEDisconnected, MAIN_DISPATCHER)
	def _handler_ue_disconnected(self, ev):
		prev_att = ev.ue.get_prev_attachment()
		ev.ue.set_attachment(prev_att)
		msg = ev.ue.to_dict()
		self._rpc_broadcall('ue_disconnected', msg)


	@set_ev_cls(EventRoutingUpdate, MAIN_DISPATCHER)
	def _handler_topology_update(self, ev):
		"""
		Handler for EventRoutingUpdate.
		Update the network topology stored locally.
		"""
		msg = ''
		self._rpc_broadcall('routing_update')


	@set_ev_cls(EventTopologyUpdate, MAIN_DISPATCHER)
	def _handler_topology_update(self, ev):
		"""
		Handler for EventTopologyUpdate.
		Update the network topology stored locally.
		"""
		msg = ''
		self._rpc_broadcall('topology_update')


	@set_ev_cls(EventSwitchEnter, MAIN_DISPATCHER)
	def _handler_switch_enter(self, ev):
		msg = ev.switch.to_dict()
		self._rpc_broadcall('switch_enter', msg)


	@set_ev_cls(EventSwitchUpdate, MAIN_DISPATCHER)
	def _handler_switch_update(self, ev):
		msg = ev.switch.to_dict()
		self._rpc_broadcall('switch_update', msg)


	@set_ev_cls(EventSwitchLeave, MAIN_DISPATCHER)
	def _handler_switch_leave(self, ev):
		msg = ev.switch.to_dict()
		self._rpc_broadcall('switch_leave', msg)


	@set_ev_cls(EventLinkAdd, MAIN_DISPATCHER)
	def _handler_link_add(self, ev):
		msg = ev.link.to_dict()
		self._rpc_broadcall('link_add', msg)


	@set_ev_cls(EventLinkDelete, MAIN_DISPATCHER)
	def _handler_link_delete(self, ev):
		msg = ev.link.to_dict()
		self._rpc_broadcall('link_del', msg)


	def _rpc_broadcall(self, func_name, msg = {}):
		d = {}
		d['jsonrpc'] = '2.0'
		d['id'] = 1
		d['method'] = func_name
		d['params'] = msg

		self._ws_manager.broadcast(json.dumps(d))




class iJOINController(ControllerBase):
	def __init__(self, req, link, data, **config):
		super(iJOINController, self).__init__(req, link, data, **config)
		self.app = data['ijoin_api_app']


	@websocket('topology', '/topology/ws')
	def _handler_topology_websocket(self, ws):
		rpc_server = WebSocketRPCServer(ws, self.app)
		rpc_server.serve_forever()


	@route('topology', '/topology/ue', methods=['GET'])
	def _handler_list_ues(self, req, **kwargs):
		ues = self._get_ue(None)
		body = json.dumps([ue.to_dict() for ue in ues])
		return Response(content_type = 'application/json', body = body)


	@route('topology', '/topology/ue/{id}/profile/{profile}/enable',
			methods=['POST'], requirements={'id': ETH_PATTERN, 'profile': r'\w+'})
	def _handler_enable_ue_profile(self, req, **kwargs):
		if 'id' not in kwargs or 'profile' not in kwargs:
			return Response(status = 400)

		ueid = kwargs['id']
		profile = kwargs['profile']
		status = self._update_ue_profile(ueid, profile, True)
		if not status:
			self.app.logger.info("MADONNA TROIA")
			return Response(status = 400)

		body = json.dumps('')
		return Response(content_type = 'application/json', body = body)


	@route('topology', '/topology/ue/{id}/profile/{profile}/disable',
			methods=['POST'], requirements={'id': ETH_PATTERN, 'profile': r'\w+'})
	def _handler_disable_ue_profile(self, req, **kwargs):
		if 'id' not in kwargs or 'profile' not in kwargs:
			return Response(status = 400)

		ueid = kwargs['id']
		profile = kwargs['profile']
		status = self._update_ue_profile(ueid, profile, False)
		if not status:
			return Response(status = 400)

		body = json.dumps('')
		return Response(content_type = 'application/json', body = body)


	@route('topology', '/topology/switch', methods=['GET'])
	def _handler_list_switches(self, req, **kwargs):
		switches = self._get_switch(None)
		body = json.dumps([switch.to_dict() for switch in switches])
		return Response(content_type = 'application/json', body = body)


	@route('topology', '/topology/switch/{dpid}',
			methods=['GET'], requirements={'dpid': dpid_lib.DPID_PATTERN})
	def _handler_get_switch(self, req, **kwargs):
		if 'dpid' not in kwargs:
			return Response(status=400)
		
		dpid = dpid_lib.str_to_dpid(kwargs['dpid'])
		switches = self._get_switch(dpid)
		body = json.dumps([switch.to_dict() for switch in switches])
		return Response(content_type = 'application/json', body = body)


	@route('topology', '/topology/neigh', methods=['GET'])
	def _handler_list_neighs(self, req, **kwargs):
		neighs = self._get_neigh(None)
		body = json.dumps([neigh.to_dict() for neigh in neighs])
		return Response(content_type = 'application/json', body = body)


	@route('topology', '/topology/neigh/{dpid}',
			methods=['GET'], requirements={'dpid': dpid_lib.DPID_PATTERN})
	def _handler_get_switch_neigh(self, req, **kwargs):
		if 'dpid' not in kwargs:
			return Response(status=400)

		dpid = dpid_lib.str_to_dpid(kwargs['dpid'])
		neighs = self._get_neigh(dpid)
		body = json.dumps([neigh.to_dict() for neigh in neighs])
		return Response(content_type = 'application/json', body = body)


	@route('topology', '/topology/link', methods=['GET'])
	def _handler_list_links(self, req, **kwargs):
		links = self._get_link(None)
		body = json.dumps([link.to_dict() for link in links])
		return Response(content_type = 'application/json', body = body)


	@route('topology', '/topology/link/{dpid}',
			methods=['GET'], requirements={'dpid': dpid_lib.DPID_PATTERN})
	def _handler_get_links(self, req, **kwargs):
		if 'dpid' not in kwargs:
			return Response(status=400)

		dpid = dpid_lib.str_to_dpid(kwargs['dpid'])
		links = self._get_link(dpid)
		body = json.dumps([link.to_dict() for link in links])
		return Response(content_type = 'application/json', body = body)


	def _update_ue_profile(self, ueid, profile, enabled):
		rep = self.app.send_request(EventUEProfileUpdateRequest(ueid, profile, enabled))
		return rep.status


	def _get_ue(self, ue_id):
		rep = self.app.send_request(EventUERequest(ue_id))
		return rep.ue


	def _get_switch(self, dpid):
		rep = self.app.send_request(EventSwitchRequest(dpid))
		return rep.switch


	def _get_link(self, dpid):
		rep = self.app.send_request(EventLinkRequest(dpid))
		return rep.link


	def _get_neigh(self, dpid):
		rep = self.app.send_request(EventNeighRequest(dpid))
		return rep.neigh
