#!python3
from time import sleep
import random

from ocs.exceptions import *


class Roof():
    def __init__(self, config={}):
        self.config = config
        self.is_open = False
        self.open_count = 0
        self.close_count = 0


    def open(self):
        self.is_open = True
        sleep(self.config.get('roof_time_to_open', 0))
        self.open_count += 1
        if self.config.get('open_fail_after', None) is not None:
            if self.open_count >= self.config.get('open_fail_after'):
                raise RoofFailure
        if self.config.get('open_random_fail_rate', None) is not None:
            if random.random() <= self.config.get('open_random_fail_rate'):
                raise RoofFailure


    def close(self):
        self.close_count += 1
        sleep(self.config.get('roof_time_to_close', 0))
        if self.config.get('close_fail_after', None) is not None:
            if self.close_count >= self.config.get('close_fail_after'):
                raise RoofFailure
        if self.config.get('close_random_fail_rate', None) is not None:
            if random.random() <= self.config.get('close_random_fail_rate'):
                raise RoofFailure
        self.is_open = False
