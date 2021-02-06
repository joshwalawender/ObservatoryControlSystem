#!python3
from time import sleep


class Telescope():
    def __init__(self, time_to_slew=5, time_to_park=5):
        self.time_to_slew = time_to_slew
        self.time_to_park = time_to_park
        self.parked = True
        self.tracking = False


    def slew(self, target):
        self.parked = False
        self.tracking = True
        sleep(self.time_to_slew)



    def park(self):
        sleep(self.time_to_park)
        self.tracking = False
        self.parked = True

