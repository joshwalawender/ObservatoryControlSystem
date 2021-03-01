#!python3
from time import sleep
import random
from astropy.io import fits

from ocs.exceptions import *


class InstrumentController():
    def __init__(self, logger=None, time_to_configure=0,
                 configure_fail_after=None, configure_random_fail_rate=0):
        self.name = 'simulator'
        self.time_to_configure = time_to_configure
        self.configure_count = 0
        self.configure_fail_after = configure_fail_after
        self.configure_random_fail_rate = configure_random_fail_rate


    def configure(self, instconfig):
        sleep(self.time_to_configure)

        self.configure_count += 1
        if self.configure_fail_after is not None:
            if self.configure_count >= self.configure_fail_after:
                raise InstrumentFailure
        if self.configure_random_fail_rate is not None:
            if random.random() <= self.configure_random_fail_rate:
                raise InstrumentFailure


    def collect_header_metadata(self):
        return fits.Header()
