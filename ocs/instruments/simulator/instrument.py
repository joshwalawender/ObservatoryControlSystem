#!python3
from time import sleep

from ocs.exceptions import *


class InstrumentController():
    def __init__(self, config={}):
        self.config = config
        self.name = 'simulator'
        self.time_to_configure = self.config.get('time_to_configure', 0)


    def configure(self, instconfig):
        sleep(self.time_to_configure)
