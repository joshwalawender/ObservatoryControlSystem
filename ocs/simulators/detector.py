#!python3
from time import sleep


class Detector():
    def __init__(self, overhead=3):
        self.name = 'simulator'
        self.overhead = overhead


    def expose(self, detconfig):
        if detconfig is not None:
            sleep(self.detconfig.exptime)
        sleep(self.overhead)
        return True
