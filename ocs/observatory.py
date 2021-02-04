#!python3
from pathlib import Path
from time import sleep
from datetime import datetime
import random
import numpy as np
import yaml

from astropy import coordinates as c

from transitions.extensions import GraphMachine as Machine
from transitions import State

from .simulators.weather import Weather
from .simulators.roof import Roof
from .simulators.telescope import Telescope
from .simulators.instrument import Instrument
from .simulators.detector import Detector
from .scheduler import Scheduler

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

with open(Path(__file__).parent.joinpath('states.yaml')) as states_file:
    states = yaml.safe_load(states_file)
with open(Path(__file__).parent.joinpath('transitions.yaml')) as transitions_file:
    transitions = yaml.safe_load(transitions_file)
with open(Path(__file__).parent.joinpath('location.yaml')) as location_file:
    location_info = yaml.safe_load(location_file)


##-------------------------------------------------------------------------
## Define Roll Off Roof Model
##-------------------------------------------------------------------------
class RollOffRoof():
    def __init__(self, name):
        self.name = name
        self.location = c.EarthLocation.from_geocentric(**location_info)
        self.machine = Machine(model=self,
                               states=states,
                               transitions=transitions,
                               initial='sleeping',
                               use_pygraphviz=True,
                               )
        # Initialize Status Values
        self.entered_state_at = datetime.now()
        self.observed = []
        self.failed = []
        # Components
        self.weather = Weather()
        self.roof = Roof()
        self.telescope = Telescope()
        self.instrument = Instrument()
        self.detector = Detector()
        self.scheduler = Scheduler()


    ##-------------------------------------------------------------------------
    ## Utilities
    def print_status(self, msg):
        parked_str = {True: 'Parked', False: 'Unparked'}[self.safe_parked]
        print(f'{self.state:12s} {parked_str:8s} {str(self.current_target):8s}: {msg}')


    def entry_timestamp(self):
        self.entered_state_at = datetime.now()


    ##-------------------------------------------------------------------------
    ## Status Checks
    def is_safe(self):
        return self.weather.is_safe()


    def not_interrupted(self):
        return self.weather.has_been_safe(self.entered_state_at)


    def is_dark(self):
        


    ##-------------------------------------------------------------------------
    ## Overall Controls
    def wait_for(self, waittime=30):
        # Actions on entering new state
        sleep(waittime)
        # Trigger next state
        self.open()


    ##-------------------------------------------------------------------------
    ## Roof Controls
    def open_roof(self):
        self.print_status('Opening the roof')
        try:
            self.roof.open()
        except:
            self.failed_opening()
        self.select_OB()


    def close_roof(self):
        self.print_status('Closing the roof')
        try:
            self.roof.close()
        except:
            self.critical_failure()


    ##-------------------------------------------------------------------------
    ## Scheduling


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

if __name__ == '__main__':
    hokuula.machine.get_graph().draw('state_diagram.png', prog='dot')
