#!python3
from time import sleep
import random

from ocs.exceptions import *


class Telescope():
    def __init__(self, logger=None, time_to_slew=0, time_to_park=0,
                 slew_fail_after=None, park_fail_after=None,
                 slew_random_fail_rate=0, park_random_fail_rate=0):
        self.parked = True
        self.tracking = False
        self.slew_count = 0
        self.park_count = 0
        self.time_to_slew = time_to_slew
        self.time_to_park = time_to_park
        self.slew_fail_after = slew_fail_after
        self.park_fail_after = park_fail_after
        self.slew_random_fail_rate = slew_random_fail_rate
        self.park_random_fail_rate = park_random_fail_rate


    def slew(self, target):
        self.parked = False
        self.tracking = True
        sleep(self.time_to_slew)
        self.slew_count += 1
        if self.slew_fail_after is not None:
            if self.slew_count >= self.slew_fail_after:
                raise TelescopeFailure
        if self.slew_random_fail_rate is not None:
            if random.random() <= self.slew_random_fail_rate:
                raise TelescopeFailure


    def park(self):
        sleep(self.time_to_park)
        self.park_count += 1
        if self.park_fail_after is not None:
            if self.park_count >= self.park_fail_after:
                raise TelescopeFailure
        if self.park_random_fail_rate is not None:
            if random.random() <= self.park_random_fail_rate:
                raise TelescopeFailure
        self.tracking = False
        self.parked = True