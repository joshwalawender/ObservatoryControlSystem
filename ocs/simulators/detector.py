#!python3
from time import sleep
import random

from ..exceptions import *


class Detector():
    def __init__(self, config={}):
        self.config = config
        self.name = 'simulator'
        self.exposure_count = 0


    def expose(self, detconfig):
#         if detconfig is not None:
#             sleep(self.detconfig.exptime)
        sleep(self.config.get('exposure_overhead', 0))
        self.exposure_count += 1
        if self.config.get('expose_fail_after', None) is not None:
            if self.exposure_count >= self.config.get('expose_fail_after'):
                raise DetectorFailure
        if self.config.get('expose_random_fail_rate', None) is not None:
            if random.random() <= self.config.get('expose_random_fail_rate'):
                raise DetectorFailure
