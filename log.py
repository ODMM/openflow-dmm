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
from static import LOG_FILE
from static import DEBUG_FILE
# End import from iJOIN solution files

# Start import from Python files
import logging.config
# End import from Python files


COLORS = {	'Amm': '0;31m',
			'AccessPoint': '0;32m',
			'Gateway': '0;34m',
			'Mme': '0;36m',
			'Ndisc': '0;37m',
			'Nmm': '0;91m',
			'Packet': '0;92m',
			'Teem': '0;93m',
		}


def get_logger(name):
	# create logger with 'spam_application'
	logger = logging.getLogger(name)
	logger.setLevel(logging.DEBUG)
	# create file handler which logs even debug messages
	fh = logging.FileHandler(LOG_FILE, mode='a')
	fh.setLevel(logging.INFO)
	# create file handler which logs even debug messages
	dh = logging.FileHandler(DEBUG_FILE, mode='a')
	dh.setLevel(logging.DEBUG)
	# create console handler with a higher log level
	ch = logging.StreamHandler()
	ch.setLevel(logging.INFO)
	# create a formatter and add it to the handlers
	if name in COLORS:
		color = COLORS[name]
	else:
		color = '0m'
	fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [\033[' + color + '%(name)s\033[0m]: %(message)s')
	dh_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(name)s]: %(message)s')
	ch_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [\033[' + color + '%(name)s\033[0m]: %(message)s')
	# add the formatter to the handlers
	fh.setFormatter(fh_formatter)
	dh.setFormatter(dh_formatter)
	ch.setFormatter(ch_formatter)
	# add the handlers to the logger
	logger.addHandler(fh)
	logger.addHandler(dh)
	logger.addHandler(ch)
	# set the parent to 0 to avoid double output
	logger.parent = 0
	
	return logger
