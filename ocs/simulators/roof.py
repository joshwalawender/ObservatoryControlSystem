#!python3
from time import sleep
import random

from . import config
from .. import RoofFailure


class Roof():
    def __init__(self):
        self.time_to_open = config.get('roof_time_to_open', 0)
        self.time_to_close = config.get('roof_time_to_close', 0)
        self.is_open = False
        self.open_count = 0
        self.close_count = 0


    def open(self):
        self.is_open = True
        sleep(self.time_to_open)
        self.open_count += 1
        if config.get('open_fail_after', None) is not None:
            if self.open_count >= config.get('open_fail_after'):
                raise RoofFailure
        if config.get('open_random_fail_rate', None) is not None:
            if random.random() <= config.get('open_random_fail_rate'):
                raise RoofFailure


    def close(self):
        self.close_count += 1
        sleep(self.time_to_close)
        if config.get('close_fail_after', None) is not None:
            if self.close_count >= config.get('close_fail_after'):
                raise RoofFailure
        if config.get('close_random_fail_rate', None) is not None:
            if random.random() <= config.get('close_random_fail_rate'):
                raise RoofFailure
        self.is_open = False
