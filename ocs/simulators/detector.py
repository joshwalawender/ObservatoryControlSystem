#!python3
from time import sleep
import random

from . import config
from .. import DetectorFailure


class Detector():
    def __init__(self):
        self.name = 'simulator'
        self.overhead = config.get('exposure_overhead', 0)
        self.exposure_count = 0


    def expose(self, detconfig):
#         if detconfig is not None:
#             sleep(self.detconfig.exptime)
        sleep(self.overhead)
        self.exposure_count += 1
        if config.get('expose_fail_after', None) is not None:
            if self.exposure_count >= config.get('expose_fail_after'):
                raise DetectorFailure
        if config.get('expose_random_fail_rate', None) is not None:
            if random.random() <= config.get('expose_random_fail_rate'):
                raise DetectorFailure
