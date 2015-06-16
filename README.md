# openflow-dmm
OpenfFlow-DMM is a Software-Defined Networking (SDN) implementation of IPv6 Distributed Mobility Management, rfc7333, rfc7429.  OpenFlow-DMM has been developed using Ryu as component-based Software-Defined Networking framework and OpenFlow 1.3 as Southbound API.

OpenFlow-DMM implementation has been tested for Ryu 3.17 and above and it requires OpenFlow 1.3 or above. 

- Install Ryu as expleained here: http://osrg.github.io/ryu/.

- Make sure that the switches managed by the network controller have OpenFlow 1.3. support.

- Configure the IP of network controller on the switches.

- Open the file static.py with a text editor of your choice and edit these variables as you wish:
	
	WLAN_IFACE = 'wlan'
	GW_IFACE = 'gw'

  WLAN_IFACE is the beginning of name of the switch's interface where the users connect to (i.e. wlan0, wlanA1, etc. will match).
  GW_IFACE is the beginning of name of the switch's interface acting as gateway (i.e. gw0, gwA1, etc. will match).

- Make executable the file run.sh: 
	$ chmod +x run.sh

- Run the network controller:
	$ ./run.sh
