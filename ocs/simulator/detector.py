#!python3
from time import sleep
import random

from ocs.exceptions import *


class DetectorController():
    def __init__(self, logger=None, exposure_overhead=0,
                 expose_fail_after=None, expose_random_fail_rate=0,
                 simulate_exposure_time=True,):
        self.name = 'simulator'
        self.exposure_count = 0
        self.exptime = 0
        self.exposure_overhead = exposure_overhead
        self.simulate_exposure_time = simulate_exposure_time
        self.expose_fail_after = expose_fail_after
        self.expose_random_fail_rate = expose_random_fail_rate


    def set_exptime(self, exptime):
        self.exptime = exptime


    def set_gain(self, gain):
        return


    def set_binning(self, binx, biny):
        return


    def set_window(self):
        return


    def expose(self, additional_header=None):
        sleeptime = self.exposure_overhead + self.exptime
        if self.simulate_exposure_time is True:
            sleep(sleeptime)
        self.exposure_count += 1
        if self.expose_fail_after is not None:
            if self.exposure_count >= self.expose_fail_after:
                raise DetectorFailure('Exposure count exceeded')
        if self.expose_random_fail_rate is not None:
            if random.random() < self.expose_random_fail_rate:
                raise DetectorFailure('Random failure')
        return None
