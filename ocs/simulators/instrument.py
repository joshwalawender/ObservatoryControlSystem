#!python3
from time import sleep


class Instrument():
    def __init__(self, time_to_configure=2):
        self.name = 'simulator'
        self.time_to_configure = time_to_configure


    def configure(self, instconfig):
        sleep(self.time_to_configure)
