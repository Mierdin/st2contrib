import time

from napalm import get_network_driver

# Stores number of BGP neighbors
bgp_neighbors = 0

# Stores RIB information in-between calls
bgp_rib = {}


while True:

	# Use the appropriate network driver to connect to the device:
	driver = get_network_driver('junos')

	# Connect:
	# device = driver(hostname='172.28.128.10', username='root',
	#                 password='Juniper', optional_args={'port': 22})

	ip_addresses = ["172.28.128.10"]

	devices = [driver(hostname=address, username='root',
	                  password='Juniper', optional_args={'port': 22}) for address in ip_addresses]

	this_bgp_neighbors = 0


	for device in devices:

		# Retrieve full BGP peer info at the VRF level
		with device:
			vrfs = device.get_bgp_neighbors()

		vrfs = {}

		# import pdb; pdb.set_trace()
		for vrf_id, vrf_details in vrfs.items():

			for peer_id, peer_details in vrf_details['peers'].items():

				import pdb; pdb.set_trace()

				# TODO(mierdin): This isn't always the fastest method when
				# peers go down. Try to improve on this.
				if peer_details['is_up']:
					this_bgp_neighbors += 1


	if this_bgp_neighbors > bgp_neighbors:
		print "BGP neighbors went UP to %s" % str(this_bgp_neighbors)
	elif this_bgp_neighbors == bgp_neighbors:
		print "BGP neighbors STAYED at %s" % str(this_bgp_neighbors)
	elif this_bgp_neighbors < bgp_neighbors:
		print "BGP neighbors went DOWN to %s" % str(this_bgp_neighbors)
	

	bgp_neighbors = this_bgp_neighbors

		# with device:
		# 	device.get_bgp_neighbors()
		# 	import pdb; pdb.set_trace()

	time.sleep(2)
