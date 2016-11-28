from datetime import datetime

from napalm import get_network_driver

from st2reactor.sensor.base import PollingSensor

BGP_PEER_INCREASE = 'napalm.BgpPeerIncrease'
BGP_PEER_DECREASE = 'napalm.BgpPeerDecrease'


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

    def __init__(self, sensor_service, config=None, poll_interval=5):
        super(NapalmBGPSensor, self).__init__(sensor_service=sensor_service,
                                              config=config,
                                              poll_interval=poll_interval)
        self._logger = self.sensor_service.get_logger(
            name=self.__class__.__name__
        )

        # self._poll_interval = 30

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

        # Need to get initial BGP RIB, neighbor table, etc. Put into "self".
        # Then, write some logic within "poll" that checks again, and detects diffs
        # Detects:
        # - Diffs in BGP RIB (need to give a threshold like 100s or 1000s or routes different)
        #   (may want to not only store the previous result, but also the previous 10 or so and do a stddev calc)

        # Stores number of BGP neighbors
        # self.bgp_neighbors = 0

        # Stores RIB information in-between calls
        # self.bgp_rib = {}

        # Dictionary for tracking per-device known state
        # Top-level keys are the management IPs sent to NAPALM, and
        # information on each is contained below that
        self.device_state = {}

        napalm_config = self._config

        # Assign sane defaults for configuration
        default_opts = {
            "opt1": "val1"
        }
        for opt_name, opt_val in default_opts.items():

            try:

                # key exists but is set to nothing
                if not napalm_config[opt_name]:
                    napalm_config[opt_name] == default_opts

            except KeyError:

                # key doesn't exist
                napalm_config[opt_name] == default_opts

        # Assign options to instance
        self._devices = napalm_config['devices']

        # Generate dictionary of device objects per configuration
        # IP Address(key): Device Object(value)
        #
        # TODO(mierdin): Yes I know this looks terrible, I will fix it
        self.devices = {
            str(device['host']): get_network_driver(device['driver'])(
                hostname=str(device['host']),
                username=device['username'],
                password=device['password'],
                optional_args={
                    'port': str(device['port'])
                })
            for device in self._devices
        }

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

        for hostname, device_obj in self.devices.items():

            try:
                last_bgp_peers = self.device_state[hostname]["last_bgp_peers"]
            except KeyError:

                # Get current BGP peers (instead of setting to 0 and
                # triggering every time sensor starts initially)
                try:
                    self.device_state[hostname] = {
                        "last_bgp_peers": self.get_number_of_peers(device_obj)
                    }
                    continue
                # Any connection-related exception raised here is
                # driver-specific, so we have to catch "Exception"
                except Exception as e:
                    self._logger.debug("Caught exception on connect: %s" % e)
                    continue

            try:
                this_bgp_peers = self.get_number_of_peers(device_obj)
            # Any connection-related exception raised here is
            # driver-specific, so we have to catch "Exception"
            except Exception as e:
                self._logger.debug("Caught exception on get peers: %s" % e)
                continue

            if this_bgp_peers > last_bgp_peers:
                self._logger.info(
                    "Peer count went UP to %s" % str(this_bgp_peers)
                )
                self._bgp_peer_trigger(BGP_PEER_INCREASE, hostname,
                                       last_bgp_peers, this_bgp_peers)

            elif this_bgp_peers < last_bgp_peers:
                self._logger.info(
                    "BGP neighbors went DOWN to %s" % str(this_bgp_peers)
                )

                self._bgp_peer_trigger(BGP_PEER_DECREASE, hostname,
                                       last_bgp_peers, this_bgp_peers)

            elif this_bgp_peers == last_bgp_peers:
                self._logger.info(
                    "BGP neighbors STAYED at %s" % str(this_bgp_peers)
                )

            # Save this state for the next poll
            self.device_state[hostname]["last_bgp_peers"] = this_bgp_peers

    def cleanup(self):
        # This is called when the st2 system goes down. You can perform
        # cleanup operations like closing the connections to external
        # system here.
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

    def get_number_of_peers(self, device_obj):

        vrfs = {}

        # Retrieve full BGP peer info at the VRF level
        try:
            with device_obj:
                vrfs = device_obj.get_bgp_neighbors()
        except Exception:  # TODO(mierdin): convert to ConnectionException
            raise

        this_bgp_peers = 0

        for vrf_id, vrf_details in vrfs.items():

            for peer_id, peer_details in vrf_details['peers'].items():

                # TODO(mierdin): This isn't always the fastest method when
                # peers go down. Try to improve on this.
                if peer_details['is_up']:
                    this_bgp_peers += 1

        return this_bgp_peers

    def _bgp_peer_trigger(self, trigger, hostname, oldpeers, newpeers):
        trigger = 'napalm.BgpPeerDecrease'
        payload = {
            'device': hostname,
            'oldpeers': int(oldpeers),
            'newpeers': int(newpeers),
            'timestamp': str(datetime.now()),
        }
        self._logger.debug("DISPATCHING TRIGGER %s" % trigger)
        self._sensor_service.dispatch(trigger=trigger, payload=payload)
