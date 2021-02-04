#!python3
from time import sleep


class Telescope():
    def __init__(self, time_to_slew=5, time_to_park=5):
        self.time_to_slew = time_to_slew
        self.time_to_park = time_to_park


    def slew(self, target):
        sleep(self.time_to_slew)
        return True


    def park(self):
        sleep(self.time_to_park)
        return True
