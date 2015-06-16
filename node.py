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
# End import from iJOIN solution files

# Start import from Ryu files
from ryu.lib.dpid import dpid_to_str
# End import from Ryu files




class Node(object):
	def __init__(self, hw_addr = None, ipv6_addr = None):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		hw_addr          Node MAC address, String instance.
		ipv6_addr		 Node IPv6 local address, String instance.
		attachment       Attachment/Association instance.
		================ =========================================================
		"""
		self.hw_addr = hw_addr
		self.ipv6_addr = ipv6_addr

		self.attachment = None
		self.attachment_history = []

	
	def set_attachment(self, attachment):
		"""
		Set the current Node's attachment.
		Update attachment history
		"""
		if self.attachment:
			self.attachment.active = False
			self.attachment_history.append(self.attachment)
		self.attachment = attachment


	def get_prev_attachment(self):
		"""
		Get the previous Node's attachment
		"""
		if self.attachment_history:
			return self.attachment_history[-1]
		return None


	def to_dict(self):
		d = {'hw_addr': self.hw_addr,
			'ipv6_addr': self.ipv6_addr,
		}
		if self.attachment:
			d['attachment'] = self.attachment.to_dict()

		return d


class UE(Node):
	def __init__(self, id, hw_addr, ipv6_addr):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		id               UE id, Int instance.
		================ =========================================================
		"""
		super(UE, self).__init__(hw_addr, ipv6_addr)
		self.id = id
		self.profile = Profile(id)

	def to_dict(self):
		d = super(UE, self).to_dict()
		d['id'] = self.id
		d['profile'] = self.profile.to_dict()

		return d


class Profile():
	def __init__(self, id):
		self.id = id

	def to_dict(self):
		d = {}

		return d


class Attachment(object):
	def __init__(self, switch, port):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		active			 Boolean instance. 
						 Tells if the association is active or not.
		switch           Switch instance.
		                 The switch to which the UE is connected.
		port             Port instance.
		================ =========================================================
		"""
		self.active = True
		self.switch = switch
		self.port = port


	def to_dict(self):
		d = {'active': self.active,
			'switch': dpid_to_str(self.switch.switch.dp.id),
			'port': self.port.port_no
		}

		return d
		

class Association(Attachment):
	"""
	The Association attribute for the UE.
	"""
	def __init__(self, switch, port):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		anchors          Anchor dictionary instance.
		================ =========================================================
		"""
		super(Association, self).__init__(switch, port)
		self.anchors = {}


	def to_dict(self):
		d = super(Association, self).to_dict()
		d['anchors'] = {}
		for anch_dpid, anch in self.anchors.iteritems():
			d['anchors'][dpid_to_str(anch_dpid)] = anch.to_dict()

		return d


class Anchor:
	def __init__(self, gw, nw_prefix):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		gw               Switch instance.
		                 The Switch selected as Gateway.
		nw_prefix        tuple instance.
						 IPv6 prefix, each octet is an element of the tuple:
						 ('0','1','2','3','4','5','6','7')
		nw_prefix_len    int instance.
						 CIDR netmask to apply to network_prefix.						 
		router_lft       int instance.
						 The Router Lifetime to be announced.
		valid_lft        int instance.
						 The Valid Lifetime to be announenced for the nw_prefix.
		preferred_lft    int instance.
						 The Preferred Lifetime to be announenced for 
						 the nw_prefix. 
		last_time_adver. The Last Time that the nw_prefix has been announced.
		================ =========================================================
		"""
		self.gw = gw
		self.nw_prefix = nw_prefix
		self.nw_prefix_len = 64
		self.router_lft = 15
		self.valid_lft = 15
		self.preferred_lft = 15
		self.last_time_advertised = 0


	def to_dict(self):
		d = {'gw': dpid_to_str(self.gw.switch.dp.id),
			'nw_prefix': ipv6_utils.ipv6_prefix_string(self.nw_prefix, self.nw_prefix_len),
			'valid_lft': self.valid_lft,
			'preferred_lft': self.preferred_lft
		}

		return d
