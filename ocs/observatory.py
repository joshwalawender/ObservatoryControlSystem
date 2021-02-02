#!python3
from pathlib import Path
from time import sleep
from datetime import datetime
import random
import numpy as np

from transitions import Machine, State, Transition

from .simulators import Weather, Roof, Telescope


# Set up logging; The basic log level will be DEBUG
# import logging
# logging.basicConfig(level=logging.DEBUG)
# logging.getLogger('transitions').setLevel(logging.INFO)

'''A simple observatory sequencer.

This sequencer does not handle safety (e.g. weather) closures.  It assumes that
a safety closure will be sent directly to the roof controller and that it will
close the roof.  This assumes that there are no collision possibilites between
the roof and the telescope.
'''

targets = ['M42', 'M31', 'M104', 'M78', None]

states = [State(name='sleeping',
                on_enter=['entry_timestamp']),
          State(name='opening',
                on_enter=['entry_timestamp', 'open_roof']),
          State(name='ready',
                on_enter=['entry_timestamp', 'pick_target']),
          State(name='acquiring',
                on_enter=['entry_timestamp', 'slew_telescope']),
          State(name='parking',
                on_enter=['entry_timestamp', 'park']),
          State(name='observing',
                on_enter=['entry_timestamp', 'begin_observation'],
                on_exit=['clear_current_target']),
          State(name='closing',
                on_enter=['entry_timestamp', 'close_roof']),
          State(name='shutdown',
                on_enter=['entry_timestamp', 'park', 'end_of_night_shutdown']),
         ]

transitions = [
          {'trigger': 'wake_up',        'source': 'sleeping',  'dest': 'opening', 'conditions': 'is_safe'},
          {'trigger': 'done_opening',   'source': 'opening',   'dest': 'ready'},
          {'trigger': 'acquire',        'source': 'ready',     'dest': 'acquiring', 'conditions': 'is_safe'},
          {'trigger': 'acquisition_complete', 'source': 'acquiring',   'dest': 'observing', 'conditions': 'is_safe'},
          {'trigger': 'done_observing', 'source': 'observing', 'dest': 'ready'},
          {'trigger': 'park_telescope', 'source': '*',         'dest': 'parking'},
          {'trigger': 'done_parking',   'source': 'parking',   'dest': 'sleeping'},
          {'trigger': 'end_of_night',   'source': '*',         'dest': 'shutdown'},
         ]


##-------------------------------------------------------------------------
## Define Roll Off Roof Class
##-------------------------------------------------------------------------
class RollOffRoof():
    def __init__(self, name):
        self.name = name
        self.machine = Machine(model=self, states=states,
                               transitions=transitions, initial='sleeping')

        # Initialize Status Values
        self.safe_parked = True
        self.entered_state_at = datetime.now()
        self.next_target = None
        self.current_target = None
        self.observed = []
        self.failed = []
        # Components
        self.weather = Weather()
        self.roof = Roof()
        self.telescope = Telescope()


    ##-------------------------------------------------------------------------
    ## Utilities
    def print_status(self, msg):
        parked_str = {True: 'Parked', False: 'Unparked'}[self.safe_parked]
        print(f'{self.state:12s} {parked_str:8s} {str(self.current_target):8s}: {msg}')


    def entry_timestamp(self):
        self.entered_state_at = datetime.now()


    def clear_current_target(self):
        self.current_target = None


    ##-------------------------------------------------------------------------
    ## Utilities
    def is_safe(self):
        return self.weather.is_safe()


    def check_ok(self):
        return self.weather.has_been_safe(self.entered_state_at)


    ##-------------------------------------------------------------------------
    ## Roof Controls
    def open_roof(self):
        self.print_status('Opening the roof')
        self.safe_parked = False
        open = self.roof.open()
        if open is True:
            self.done_opening()
        else:
            self.unsafe()


    def close_roof(self):
        self.print_status('Closing the roof')
        closed = self.roof.close()
        if closed is True:
            self.safe_parked = True
            self.print_status('Roof closed')
            self.done_closing()
        else:
            self.print_status('Roof close failed')


    ##-------------------------------------------------------------------------
    ## Scheduler
    def pick_target(self):
        if len(targets) > 0:
            self.print_status('Selecting target ...')
            chosen_index = random.choice([i for i in range(0,len(targets))])
            self.next_target = targets.pop(chosen_index)
            if self.next_target is not None:
                self.print_status(f'Next Target will be {self.next_target}')
                self.slew()
            else:
                self.print_status('No targets available, waiting')
                sleep(5)
                self.pick_target()
        else:
            self.print_status('No more targets available ...')
            self.end_of_night()


    ##-------------------------------------------------------------------------
    ## Telescope Controls
    def acquire(self):
        # Slew Telescope
        self.print_status(f'Slewing to: {self.next_OB.target}')
        self.telescope.slew(self.next_OB.target)
        self.print_status('Slew complete')
        self.current_target = self.next_OB.target
        if self.next_OB.acquire is not None:
            # do extra acquire steps
            pass
        self.acquisition_complete()


    def park(self):
        self.print_status(f'Parking Telescope')
        parked = self.telescope.park()
        if parked is True:
            self.print_status('Telescope parked')
            self.done_parking()
        else:
            self.print_status('Telescope parking failed')

        if self.state == 'parking':
            self.done_parking()
        elif self.state == 'shutdown':
            pass


    ##-------------------------------------------------------------------------
    ## Instrument Controls
    def begin_observation(self):
        self.print_status('starting observation')
        self.current_target = self.next_target
        self.next_target = None
        sleep(5)
        ok = self.check_ok()
        if ok is True:
            self.print_status('observation complete')
            self.observed.append(self.current_target)
        else:
            self.print_status('observation failed')
            self.failed.append(self.current_target)
        self.done_observing()


    ##-------------------------------------------------------------------------
    ## Other
    def end_of_night_shutdown(self):
        print(f'Observed: {self.observed}')
        print(f'Failed: {self.failed}')



##-------------------------------------------------------------------------
## Instantiate the Observatory
##-------------------------------------------------------------------------
hokuula = RollOffRoof(name='hokuula')

