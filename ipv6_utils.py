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




import re




def ipv6_prefix_string(nw_prefix, nw_prefix_len):
	"""
	Get an IPv6 network prefix string
	"""
	nwp_bit = list(''.join([bin(int(q, 16))[2:].zfill(16) for q in nw_prefix]))
	nw_addr = nwp_bit[:nw_prefix_len] + ['0']*((16-(nw_prefix_len%16))%16)
	nw_addr = [hex(int(''.join(nw_addr[i:i+4]), 2))[2:] for i in range(0, len(nw_addr), 4)]
	nw_addr = [hex(int(''.join(nw_addr[i:i+4]), 16))[2:] for i in range(0, len(nw_addr), 4)]
									
	return ':'.join(nw_addr) + '::/' + str(nw_prefix_len)
	nw_addr = nwp_bit[:nw_prefix_len] + ['0']*(64-nw_prefix_len)


def ipv6_suffix_from_mac(mac):
	"""
	Get an ipv6 suffix starting from a MAC address
	"""
	suffix = mac[0:9] + 'ff:fe' + mac[8:]
	suffix = suffix.replace(":", "")
	suffix = ':'.join([suffix[i:i+4] for i in range(0, len(suffix), 4)])
	suffix = str(hex(int(suffix[0:2], 16) ^ 2)[2:]) + suffix[2:]

	return suffix
	

def ipv6_global_from_mac(nw_prefix, nw_prefix_len, mac):
	"""
	Get an auto-configure ipv6 global address starting from a network prefix and a MAC address
	"""
	nwp_bit = list(''.join([bin(int(q, 16))[2:].zfill(16) for q in nw_prefix]))
	nw_addr = nwp_bit[:nw_prefix_len] + ['0']*(64-nw_prefix_len)
	nw_addr = [hex(int(''.join(nw_addr[i:i+4]), 2))[2:] for i in range(0, len(nw_addr), 4)]
	nw_addr = [hex(int(''.join(nw_addr[i:i+4]), 16))[2:] for i in range(0, len(nw_addr), 4)]

	return ':'.join(nw_addr) + ':' + ipv6_suffix_from_mac(mac)


def ipv6_local_ucast_from_mac(mac):
	"""
	Get an ipv6 local address starting from a MAC address
	"""
	return 'fe80::' + ipv6_suffix_from_mac(mac)


def ipv6_local_mcast_from_local(ipv6_loc):
	"""
	Get an ipv6 solicited node multicast address starting from a ipv6 local unicast address
	"""
	return 'ff02::1:ff' + ipv6_loc[-7:]


def ipv6_local_mcast_from_mac(mac):
	"""
	Get an ipv6 solicited node multicast address starting from a MAC address
	"""
	ipv6_loc = ipv6_local_ucast_from_mac(mac)
	return 'ff02::1:ff' + ipv6_loc[-7:]


def mac_mcast_from_ipv6_local_mcast(ipv6_loc_mst):
	"""
	Get an ethernet solicited node multicast address starting from a IPv6 local multicast address
	"""
	tmp_str = ipv6_loc_mst[-9:].replace(":", "")
	tmp_str = ':'.join([tmp_str[i:i+2] for i in range(0, len(tmp_str), 2)])
	return '33:33:' + tmp_str


def ipv6_mask_from_cidr(cidr):
	"""
	Get an ipv6 netmask starting from a CIDR.
	Example:
		cidr = 64
		mask = ffff:ffff:ffff:ffff:0:0:0:0
	"""
	mask = ['1']*cidr + ['0']*(128-cidr)
	mask = [hex(int(''.join(mask[i:i+4]), 2))[2:] for i in range(0, len(mask), 4)]
	mask = [''.join(mask[i:i+4]) for i in range(0, len(mask), 4)]
	mask = ':'.join(mask)

	return mask


def ipv6_to_int(string):
	"""
	Convert an ipv6 string into a ipv6 int list
	"""
	ip = string.split(':')
	assert len(ip) == 8

	return [int(x, 16) for x in ip]


def ipv6_fill(string):
	"""
	Fill an ipv6 string.
	Example:
		string: '2001::'
		ipv6: '2001:0:0:0:0:0:0:0'
	"""
	assert (len(re.findall(r'(:)(?=\1)', string))) <= 1

	if string.startswith('::'):
		ipv6 = string[1:].split(':')
	elif string.endswith('::'):
		ipv6 = string[:-1].split(':')
	else:
		ipv6 = string.split(':')

	try:
		i = ipv6.index('')
		ipv6 = ipv6[:i] + ['0']*(8-(len(ipv6)-1)) + ipv6[i+1:]
	except ValueError:
		pass

	return ':'.join(ipv6)
