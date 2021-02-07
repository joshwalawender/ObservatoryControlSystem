#!python3
from pathlib import Path
from time import sleep
from datetime import datetime
import random
import numpy as np
import yaml

from astropy import units as u
from astropy import coordinates as c
from astropy.time import Time

# Suppress IERS download failure
from astropy.utils.iers import conf
conf.auto_max_age = None

# from transitions.extensions import GraphMachine as Machine
from transitions import Machine
from transitions import State

from .simulators.weather import Weather
from .simulators.roof import Roof
from .simulators.telescope import Telescope
from .simulators.instrument import Instrument
from .simulators.detector import Detector
from .scheduler import Scheduler


##-------------------------------------------------------------------------
## Load Configuration Data
##-------------------------------------------------------------------------
root_path = Path(__file__).parent.joinpath('config')
with open(root_path / 'config.yaml') as config_file:
    config = yaml.safe_load(config_file)
# Load States File
states_file = root_path / config.get('state_file', 'states.yaml')
with open(states_file.expanduser().absolute()) as states_obj:
    states = yaml.safe_load(states_obj)
# Load Transitions File
transitions_file = root_path / config.get('transitions_file', 'transitions.yaml')
with open(transitions_file.expanduser().absolute()) as transitions_obj:
    transitions = yaml.safe_load(transitions_obj)
# Load Location File
location_file = root_path / config.get('location_file', 'location.yaml')
with open(location_file.expanduser().absolute()) as location_obj:
    location_info = yaml.safe_load(location_obj)


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
import logging
log = logging.getLogger('RollOffRoof')
log.setLevel(logging.DEBUG)
## Set up console output
LogConsoleHandler = logging.StreamHandler()
LogConsoleHandler.setLevel(getattr(logging, config.get('loglevel_console').upper()))
LogFormat = logging.Formatter('%(asctime)s %(levelname)6s %(message)s',
#                               datefmt='%Y-%m-%d %H:%M:%S')
                             )
LogConsoleHandler.setFormatter(LogFormat)
log.addHandler(LogConsoleHandler)


##-------------------------------------------------------------------------
## Define Roll Off Roof Observatory Model
##-------------------------------------------------------------------------
class RollOffRoof():
    '''Simple observatory with roll off roof.
    '''
    def __init__(self, name, states={}, transitions={}, initial=None,
                 waittime=2, maxwaits=4, max_allowed_errors=0,
                 ):
        self.name = name
        self.waittime = waittime
        self.maxwaits = maxwaits
        self.max_allowed_errors = max_allowed_errors
        self.location = c.EarthLocation(**location_info)
        self.machine = Machine(model=self,
                               states=states,
                               transitions=transitions,
                               initial=initial,
#                                use_pygraphviz=True,
                               )
        # Initialize Status Values
        self.entered_state_at = datetime.now()
        self.observed = []
        self.failed = []
        self.next_OB = None
        self.current_OB = None
        self.waitcount = 0
        self.we_are_done = False
        self.durations = {}
        self.error_count = 0
        # Components
        self.weather = Weather()
        self.roof = Roof()
        self.telescope = Telescope()
        self.instrument = Instrument()
        self.detector = Detector()
        self.scheduler = Scheduler()
        # log initial state
        self.log('Starting software')
        # log states
        log.debug('States')
        for state in states:
            log.debug(f'  {state}')
        # log transitions
        log.debug('Transitions')
        for transition in transitions:
            log.debug(f'  {transition}')
        # log location
        log.debug('Location Info')
        for key in location_info.keys():
            log.debug(f'  {key}: {location_info.get(key)}')


    ##-------------------------------------------------------------------------
    ## Utilities
    def log(self, msg, level=logging.INFO):
        open_str = {True: 'Open', False: 'Closed'}[self.roof.is_open]
        log.log(level, f'{self.state:12s}: {msg}')


    def entry_timestamp(self):
        self.log(f'Entering state: {self.state}')
        self.entered_state_at = datetime.now()


    def exit_timestamp(self):
        duration = (datetime.now() - self.entered_state_at).total_seconds()
        self.log(f'Exiting state {self.state} after {duration:.1f}s', level=logging.DEBUG)
        if self.state in self.durations.keys():
            self.durations[self.state] += duration
        else:
            self.durations[self.state] = duration
            

    ##-------------------------------------------------------------------------
    ## Status Checks
    def is_safe(self):
        self.log('Checking safe', level=logging.DEBUG)
        safe = self.weather.is_safe()
        self.log(f'Safe? {safe}', level=logging.DEBUG)
        return safe


    def is_dark(self, obstime=None):
        self.log('Checking dark', level=logging.DEBUG)
        if obstime is None:
            obstime = Time.now()
        sun = c.get_sun(time=obstime)
        altaz = c.AltAz(location=self.location, obstime=obstime,
#                         pressure=, temperature=, relative_humidity=,
                        obswl=0.5*u.micron)
        sun_is_down = sun.transform_to(altaz).alt < 0
        self.log(f'Sun is Down? {sun_is_down}', level=logging.DEBUG)
        sun_is_down = True
        return sun_is_down


    def not_shutting_down(self):
        too_many_errors = self.error_count > self.max_allowed_errors
        if too_many_errors is True:
            self.we_are_done = True

        done_string = {True: '', False: 'not '}[self.we_are_done]
        self.log(f'We are {done_string}shutting down', level=logging.DEBUG)
        return (not self.we_are_done)


    def not_interrupted(self):
        return self.weather.has_been_safe(self.entered_state_at)


    ##-------------------------------------------------------------------------
    ## Timing Controls
    def wait_for(self):
        self.waitcount += 1
        if self.waitcount > self.maxwaits:
            self.log('Wait count exceeded')
            self.begin_end_of_night_shutdown()
            self.close()
        elif self.we_are_done is True:
            self.log('We are done')
            self.begin_end_of_night_shutdown()
            self.close()
        elif self.error_count > self.max_allowed_errors:
            self.log('Too may errors')
            self.begin_end_of_night_shutdown()
            self.close()
        else:
            self.log(f'waiting {self.waittime}s (roof is open? {self.roof.is_open}, waitcount = {self.waitcount})')
            sleep(self.waittime)
            if self.roof.is_open == True:
                self.select_OB()
            else:
                self.open()


    def reset_waitcount(self):
        self.waitcount = 0


    ##-------------------------------------------------------------------------
    ## Roof Controls
    def open_roof(self):
        self.log('Opening the roof')
        try:
            self.roof.open()
        except:
            self.log('Problem opening roof!', level=logging.ERROR)
            self.error_count += 1
            self.failed_opening()
        else:
            self.select_OB()


    def close_roof(self):
        self.log('Closing the roof')
        try:
            self.roof.close()
        except:
            self.critical_failure()
        else:
            print(self.we_are_done)
            if self.we_are_done is True:
                self.shutdown()
            else:
                self.wake_up()


    ##-------------------------------------------------------------------------
    ## Scheduling
    def get_OB(self):
        self.next_OB = self.scheduler.select()
        if self.next_OB is None:
            self.log(f'No more targets')
            self.wait()
        else:
            self.log(f'Got {self.next_OB.target}')
            self.reset_waitcount()
            self.acquire()


    ##-------------------------------------------------------------------------
    ## Telescope Controls
    def slew_telescope(self):
        # Slew Telescope
        self.log(f'Slewing to: {self.next_OB.target}')
        self.telescope.slew(self.next_OB.target)
        self.log('Slew complete')
        self.current_target = self.next_OB.target
        if self.next_OB.acquire is not None:
            # do extra acquire steps
            pass
        self.configure()


    def park_telescope(self):
        # If we are already parking or already shutdown, do nothing
        if self.state == 'parking':
            return
        elif self.state == 'shutdown':
            return

        # Otherwise, park the telescope
        self.log(f'Parking Telescope')
        try:
            self.telescope.park()
        except:
            self.log('Telescope parking failed')
            self.critical_failure()
        else:
            self.log('Telescope parked')
            self.current_target = None
            self.done_parking()


    ##-------------------------------------------------------------------------
    ## Instrument Controls
    def configure_instrument(self):
        self.log(f'configuring instrument: {self.next_OB.instconfig}')
        self.instrument.configure(self.next_OB.instconfig)
        self.observe()


    def begin_observation(self):
        self.log('starting observation')
        self.current_OB = self.next_OB
        self.next_OB = None
        sleep(5)
#         ok = self.check_ok()
#         if ok is True:
#             self.log('observation complete')
#             self.observed.append(self.current_target)
#         else:
#             self.log('observation failed')
#             self.failed.append(self.current_target)
        self.select_OB()


    ##-------------------------------------------------------------------------
    ## Other
    def begin_end_of_night_shutdown(self):
        self.we_are_done = True


    def night_summary(self):
        self.log(f'Observed: {self.observed}')
        self.log(f'Failed: {self.failed}')
        for state in self.durations.keys():
            self.log(f'Spent {self.durations[state]:.1f}s in {state}')


##-------------------------------------------------------------------------
## Instantiate the Observatory
##-------------------------------------------------------------------------
obs = RollOffRoof(name=config.get('name', 'myobservatory'),
                  states=states,
                  transitions=transitions,
                  initial=config.get('initial_state', 'sleeping'),
                  waittime=config.get('waittime', 2),
                  maxwaits=config.get('maxwaits', 4),
                  )

if __name__ == '__main__':
    obs.machine.get_graph().draw('state_diagram.png', prog='dot')
