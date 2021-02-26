#!python3
from time import sleep
import random

from ocs.exceptions import *


class Roof():
    def __init__(self, roof_time_to_open=0, roof_time_to_close=0,
                 open_fail_after=None, close_fail_after=None,
                 open_random_fail_rate=0, close_random_fail_rate=0):
        self.is_open = False
        self.open_count = 0
        self.close_count = 0
        self.roof_time_to_open = roof_time_to_open
        self.roof_time_to_close = roof_time_to_close
        self.open_fail_after = open_fail_after
        self.close_fail_after = close_fail_after
        self.open_random_fail_rate = open_random_fail_rate
        self.close_random_fail_rate = close_random_fail_rate


    def open(self):
        self.is_open = True
        sleep(self.roof_time_to_open)
        self.open_count += 1
        if self.open_fail_after is not None:
            if self.open_count >= self.open_fail_after:
                raise RoofFailure
        if self.open_random_fail_rate is not None:
            if random.random() <= self.open_random_fail_rate:
                raise RoofFailure


    def close(self):
        self.close_count += 1
        sleep(self.roof_time_to_close)
        if self.close_fail_after is not None:
            if self.close_count >= self.close_fail_after:
                raise RoofFailure
        if self.close_random_fail_rate is not None:
            if random.random() <= self.close_random_fail_rate:
                raise RoofFailure
        self.is_open = False
