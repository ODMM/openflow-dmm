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
from ryu.controller import event
# End import from Ryu files




class EventUEConnected(event.EventBase):
	"""
	This Event is triggered when a UE attaches to the network
	"""
	def __init__(self, ue):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		ue               The UE generating the event
		================ =========================================================
		"""	
		super(EventUEConnected, self).__init__()
		self.ue = ue


class EventUEDisconnected(event.EventBase):
	"""
	This Event is triggered when a UE disconnects from the network
	"""
	def __init__(self, ue):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		ue               The UE generating the event
		================ =========================================================
		"""	
		super(EventUEDisconnected, self).__init__()
		self.ue = ue


class EventUERequest(event.EventRequestBase):
	"""
	This Event is raised to request an UE entry
	"""
	def __init__(self, ue_id = None):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		ue_id            The requested UE id, if None reply with all UEs
		================ =========================================================
		"""	
		super(EventUEDisconnected, self).__init__()
		super(EventUERequest, self).__init__()
		self.dst = 'Mme'
		self.ue_id = ue_id


class EventUEReply(event.EventReplyBase):
	"""
	This Event is raised to reply to an UE request
	"""
	def __init__(self, dst, ue):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		ue            	 The requested UE entry
		================ =========================================================
		"""	
		super(EventUEReply, self).__init__(dst)
		self.ue = ue


class EventUEProfileUpdateRequest(event.EventRequestBase):
	"""
	This Event is raised to request an UE Profile update
	"""
	def __init__(self, ue_id, profile, enabled):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		ue_id          	 The requested UE id
		profile 		 The UE profile to be updated
		enabled			 Enable/Disable the profile
		================ =========================================================
		"""	
		super(EventUEProfileUpdateRequest, self).__init__()
		self.dst = 'Mme'
		self.ue_id = ue_id
		self.profile = profile
		self.enabled = enabled


class EventUEProfileUpdateReply(event.EventReplyBase):
	"""
	This Event is raised to acknowledge an UE Profile update
	"""
	def __init__(self, dst, status):
		"""
		================ =========================================================
		Attribute        Description
		================ =========================================================
		status         	 The status of the UE Profile update
		================ =========================================================
		"""	
		super(EventUEProfileUpdateReply, self).__init__(dst)
		self.status = status
