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


class EventTimer1sec(event.EventBase):
	"""
	This event is automatically triggered every 1 second.
	"""
	def __init__(self):
		super(EventTimer1sec, self).__init__()


class EventTimer5sec(event.EventBase):
	"""
	This event is automatically triggered every 5 second.
	"""
	def __init__(self):
		super(EventTimer5sec, self).__init__()
