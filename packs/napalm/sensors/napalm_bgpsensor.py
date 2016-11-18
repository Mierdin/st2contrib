import sys
import os

from napalm import get_network_driver

from st2reactor.sensor.base import PollingSensor


class NapalmBGPSensor(PollingSensor):
    """
    * self.sensor_service
        - provides utilities like
            get_logger() for writing to logs.
            dispatch() for dispatching triggers into the system.
    * self._config
        - contains configuration that was specified as
          config.yaml in the pack.
    * self._poll_interval
        - indicates the interval between two successive poll() calls.
    """

    def setup(self):
        # Setup stuff goes here. For example, you might establish connections
        # to external system once and reuse it. This is called only once by the system.

        # TODO Figure out how to use this and make a config.yaml
        #
        
        # database = database or self.config.get('default')
        # db_config = self.config.get(database, {})
        # params = {
        #     'database': db_config.get('database') or database,
        #     'server': server or db_config.get('server'),
        #     'user': user or db_config.get('user'),
        #     'password': password or db_config.get('password')
        # }

        # Use the appropriate network driver to connect to the device:
        driver = napalm.get_network_driver('junos')

        # Connect:
        device = driver(hostname='10.102.128.168', username='root',
                        password='Juniper', optional_args={'port': 2222})

        # Need to get initial BGP RIB, neighbor table, etc. Put into "self".
        # Then, write some logic within "poll" that checks again, and detects diffs
        # Detects:
        # - Diffs in BGP RIB (need to give a threshold like 100s or 1000s or routes different)
        #   (may want to not only store the previous result, but also the previous 10 or so and do a stddev calc)

        # Stores number of BGP neighbors
        bgp_neighbors = 0

        # Stores RIB information in-between calls
        bgp_rib = {}

    def poll(self):
        # This is where the crux of the sensor work goes.
        # This is called every self._poll_interval.
        # For example, let's assume you want to query ec2 and get
        # health information about your instances:
        #   some_data = aws_client.get('')
        #   payload = self._to_payload(some_data)
        #   # _to_triggers is something you'd write to convert the data format you have
        #   # into a standard python dictionary. This should follow the payload schema
        #   # registered for the trigger.
        #   self.sensor_service.dispatch(trigger, payload)
        #   # You can refer to the trigger as dict
        #   # { "name": ${trigger_name}, "pack": ${trigger_pack} }
        #   # or just simply by reference as string.
        #   # i.e. dispatch(${trigger_pack}.${trigger_name}, payload)
        #   # E.g.: dispatch('examples.foo_sensor', {'k1': 'stuff', 'k2': 'foo'})
        #   # trace_tag is a tag you would like to associate with the dispacthed TriggerInstance
        #   # Typically the trace_tag is unique and a reference to an external event.

        # Use the appropriate network driver to connect to the device:
        driver = get_network_driver('junos')

        ip_addresses = ["172.28.128.10"]

        devices = [driver(hostname=address, username='root',
                          password='Juniper', optional_args={'port': 22})
                   for address in ip_addresses]

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

    def cleanup(self):
        # This is called when the st2 system goes down. You can perform cleanup operations like
        # closing the connections to external system here.
        pass

    def add_trigger(self, trigger):
        # This method is called when trigger is created
        pass

    def update_trigger(self, trigger):
        # This method is called when trigger is updated
        pass

    def remove_trigger(self, trigger):
        # This method is called when trigger is deleted
        pass