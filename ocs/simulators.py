#!python3
from pathlib import Path
import re
from time import sleep
from datetime import datetime
import random
import numpy as np


class Weather():
    def __init__(self):
        self.safety_file = Path('~/.safe.txt').expanduser()


    def _evaluate_safety_line(self, line):
        timestamp = datetime.strptime(line[:19], '%Y-%m-%dT%H:%M:%S')
        if re.search('unsafe', line.lower()) is not None:
            safe = False
        elif re.search('\ssafe', line.lower()) is not None:
            safe = True
        else:
            safe = False
        return timestamp, safe


    def is_safe(self, age_limit=600):
        with open(self.safety_file) as safety_file:
            lines = safety_file.readlines()
        timestamp, safe = self._evaluate_safety_line(lines[-1])
        now = datetime.now()
        age = (now - timestamp).total_seconds()
        if abs(age) > age_limit:
            safe = False
        return safe


    def has_been_safe(self, entered_state_at):
        with open(self.safety_file) as safety_file:
            lines = safety_file.readlines()
        i = -1
        line_ts, safe = self._evaluate_safety_line(lines[-1])
        values = [safe]
        while line_ts > entered_state_at:
            i -= 1
            line_ts, safe = self._evaluate_safety_line(lines[i])
            values.append(safe)
        ok = np.all(np.array(values))
        return ok


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
