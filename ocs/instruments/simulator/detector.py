#!python3
from time import sleep
import random

from ocs.exceptions import *


class DetectorController():
    def __init__(self, config={}):
        self.config = config
        self.name = 'simulator'
        self.exposure_count = 0
        self.exptime = 0


    def set_exptime(self, exptime):
        self.exptime = exptime


    def set_gain(self, gain):
        return


    def set_binning(self, binx, biny):
        return


    def set_window(self):
        return


    def expose(self):
        sleep(self.exptime + self.config.get('exposure_overhead', 0))
        self.exposure_count += 1
        if self.config.get('expose_fail_after', None) is not None:
            if self.exposure_count >= self.config.get('expose_fail_after'):
                raise DetectorFailure
        if self.config.get('expose_random_fail_rate', None) is not None:
            if random.random() <= self.config.get('expose_random_fail_rate'):
                raise DetectorFailure
