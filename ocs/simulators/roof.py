#!python3
from time import sleep


class Roof():
    def __init__(self, time_to_open=5, time_to_close=5):
        self.time_to_open = time_to_open
        self.time_to_close = time_to_close


    def open(self):
        sleep(self.time_to_open)
        return True


    def close(self):
        sleep(self.time_to_close)
        return True
