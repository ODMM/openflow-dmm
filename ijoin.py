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
# End import from iJOIN solution files

# Start import from Ryu files
from ryu.base import app_manager
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.ofproto import ofproto_v1_3 as ofproto
# End import from Ryu files




class Ijoin(app_manager.RyuApp):
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

	app_manager.require_app('timer.timer', api_style=False)
	app_manager.require_app('packet.packet', api_style=False)
	app_manager.require_app('nmm.nmm', api_style=False)
	app_manager.require_app('teem.teem', api_style=False)
	app_manager.require_app('amm.amm', api_style=False)
	app_manager.require_app('mme.mme', api_style=False)
	app_manager.require_app('ndisc.ndisc', api_style=False)
	app_manager.require_app('accesspoint.accesspoint', api_style=False)
	app_manager.require_app('gateway.gateway', api_style=False)


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
		super(Ijoin, self).__init__(*args, **kwargs)
		self.logger = log.get_logger(self.name)
