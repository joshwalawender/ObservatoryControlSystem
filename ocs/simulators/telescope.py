#!python3
from time import sleep
import random

from .. import TelescopeFailure


class Telescope():
    def __init__(self, config={}):
        self.config = config
        self.parked = True
        self.tracking = False
        self.slew_count = 0
        self.park_count = 0


    def slew(self, target):
        self.parked = False
        self.tracking = True
        sleep(self.config.get('time_to_slew', 0))
        self.slew_count += 1
        if self.config.get('slew_fail_after', None) is not None:
            if self.slew_count >= self.config.get('slew_fail_after'):
                raise TelescopeFailure
        if self.config.get('slew_random_fail_rate', None) is not None:
            if random.random() <= self.config.get('slew_random_fail_rate'):
                raise TelescopeFailure


    def park(self):
        sleep(self.config.get('time_to_park', 0))
        self.park_count += 1
        if self.config.get('park_fail_after', None) is not None:
            if self.park_count >= self.config.get('park_fail_after'):
                raise TelescopeFailure
        if self.config.get('park_random_fail_rate', None) is not None:
            if random.random() <= self.config.get('park_random_fail_rate'):
                raise TelescopeFailure
        self.tracking = False
        self.parked = True
