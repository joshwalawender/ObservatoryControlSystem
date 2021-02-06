#!python3
from time import sleep


class Roof():
    def __init__(self, time_to_open=5, time_to_close=5):
        self.time_to_open = time_to_open
        self.time_to_close = time_to_close
        self.is_open = False


    def open(self):
        sleep(self.time_to_open)
        self.is_open = True


    def close(self):
        sleep(self.time_to_close)
        self.is_open = False
