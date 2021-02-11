#!python3
from time import sleep
import random

from . import config
from .. import TelescopeFailure


class Telescope():
    def __init__(self, time_to_slew=5, time_to_park=5):
        self.time_to_slew = config.get('time_to_slew', 0)
        self.time_to_park = config.get('time_to_park', 0)
        self.parked = True
        self.tracking = False
        self.slew_count = 0
        self.park_count = 0


    def slew(self, target):
        self.parked = False
        self.tracking = True
        sleep(self.time_to_slew)
        self.slew_count += 1
        if config.get('slew_fail_after', None) is not None:
            if self.slew_count >= config.get('slew_fail_after'):
                raise TelescopeFailure
        if config.get('slew_random_fail_rate', None) is not None:
            if random.random() <= config.get('slew_random_fail_rate'):
                raise TelescopeFailure


    def park(self):
        sleep(self.time_to_park)
        self.park_count += 1
        if config.get('park_fail_after', None) is not None:
            if self.park_count >= config.get('park_fail_after'):
                raise TelescopeFailure
        if config.get('park_random_fail_rate', None) is not None:
            if random.random() <= config.get('park_random_fail_rate'):
                raise TelescopeFailure
        self.tracking = False
        self.parked = True
