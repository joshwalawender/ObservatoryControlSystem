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

from transitions.extensions import GraphMachine as Machine
# from transitions import Machine
from transitions import State

from odl.block import ObservingBlockList
from odl.alignment import BlindAlign

from . import (RoofFailure, TelescopeFailure, AcquisitionFailure,
               InstrumentFailure, DetectorFailure)
from .scheduler import Scheduler


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
import logging
root_path = Path(__file__).parent.joinpath('config')
with open(root_path / 'log_config.yaml') as log_config_file:
    log_config = yaml.safe_load(log_config_file)
log = logging.getLogger('RollOffRoof')
log.setLevel(logging.DEBUG)
## Set up console output
LogConsoleHandler = logging.StreamHandler()
LogConsoleHandler.setLevel(getattr(logging, log_config.get('loglevel_console').upper()))
LogFormat = logging.Formatter('%(asctime)s %(levelname)6s %(message)s')
LogConsoleHandler.setFormatter(LogFormat)
log.addHandler(LogConsoleHandler)
## Set up file output
# LogFileName = None
# LogFileHandler = logging.FileHandler(LogFileName)
# LogFileHandler.setLevel(logging.DEBUG)
# LogFileHandler.setFormatter(LogFormat)
# log.addHandler(LogFileHandler)


##-------------------------------------------------------------------------
## Define Roll Off Roof Observatory Model
##-------------------------------------------------------------------------
class RollOffRoof():
    '''Simple observatory with roll off roof.
    '''
    def __init__(self, name='myobservatory',
                 states_file='states.yaml',
                 transitions_file='transitions.yaml',
                 location_file = 'location.yaml',
                 initial_state='sleeping',
                 waittime=2, maxwaits=4, max_allowed_errors=0,
                 Weather=None, weather_config={},
                 Roof=None, roof_config={},
                 Telescope=None, telescope_config={},
                 Instrument=None, instrument_config={},
                 Detector=None, detector_config={},
                 ):
        self.name = name
        # Components
        self.weather = Weather(config=weather_config)
        self.roof = Roof(config=roof_config)
        self.telescope = Telescope(config=telescope_config)
        self.instrument = Instrument(config=instrument_config)
        self.detector = Detector(config=detector_config)
        self.scheduler = Scheduler()
        # Load States File
        states_file = root_path.joinpath(states_file)
        with open(states_file.expanduser().absolute()) as FO:
            self.states = yaml.safe_load(FO)
        # Load Transitions File
        transitions_file = root_path.joinpath(transitions_file)
        with open(transitions_file.expanduser().absolute()) as FO:
            self.transitions = yaml.safe_load(FO)
        # Load Location File
        location_file = root_path.joinpath(location_file)
        with open(location_file.expanduser().absolute()) as FO:
            self.location_info = yaml.safe_load(FO)
        self.location = c.EarthLocation(**self.location_info)
        self.waittime = waittime
        self.maxwaits = maxwaits
        self.max_allowed_errors = max_allowed_errors
        self.machine = Machine(model=self,
                               states=self.states,
                               transitions=self.transitions,
                               initial=initial_state,
                               use_pygraphviz=True,
                               )
        # Initialize Status Values
        self.entered_state_at = datetime.now()
        self.observed = ObservingBlockList([])
        self.failed = ObservingBlockList([])
        self.next_OB = None
        self.current_OB = None
        self.waitcount = 0
        self.we_are_done = False
        self.durations = {}
        self.error_count = 0


    ##-------------------------------------------------------------------------
    ## Utilities
    def log(self, msg, level=logging.INFO):
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


    def log_wakeup(self):
        self.log(f'Waking up observatory: {self.name}')
        # log states
        self.log('States', logging.DEBUG)
        for state in self.states:
            self.log(f'  {state}', logging.DEBUG)
        # log transitions
        self.log('Transitions', logging.DEBUG)
        for transition in self.transitions:
            self.log(f'  {transition}', logging.DEBUG)
        # log location
        self.log('Location Info', logging.DEBUG)
        for key in self.location_info.keys():
            self.log(f'  {key}: {self.location_info.get(key)}', logging.DEBUG)
        self.log(f'Roof parameters:', logging.DEBUG)
        for key in self.roof.config.keys():
            self.log(f'  {key}: {self.roof.config.get(key)}', logging.DEBUG)
        self.log(f'Telescope parameters:', logging.DEBUG)
        for key in self.telescope.config.keys():
            self.log(f'  {key}: {self.telescope.config.get(key)}', logging.DEBUG)
        self.log(f'Instrument parameters:', logging.DEBUG)
        for key in self.instrument.config.keys():
            self.log(f'  {key}: {self.instrument.config.get(key)}', logging.DEBUG)
        self.log(f'Detector parameters:', logging.DEBUG)
        for key in self.detector.config.keys():
            self.log(f'  {key}: {self.detector.config.get(key)}', logging.DEBUG)


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
            self.log(f'Error count for tonight exceeded', level=logging.ERROR)
            self.we_are_done = True

        done_string = {True: '', False: 'not '}[self.we_are_done]
        self.log(f'We are {done_string}shutting down', level=logging.DEBUG)
#         if self.we_are_done is True:
#             self.close()
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
        except RoofFailure:
            self.log('Problem opening roof!', level=logging.ERROR)
            self.error_count += 1
            self.failed_opening()
        else:
            self.select_OB()


    def close_roof(self):
        self.log('Closing the roof')
        try:
            self.roof.close()
        except RoofFailure:
            self.log('Roof failure on closing', logging.ERROR)
            self.critical_failure()
        else:
            if self.we_are_done is True:
                self.log('Shutting down')
                self.shutdown()
            else:
                self.log('Going to wait')
                self.wake_up()


    ##-------------------------------------------------------------------------
    ## Scheduling
    def get_OB(self):
        if self.we_are_done is True:
            self.log('We are done')
            self.close()
        else:
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
    def begin_acquisition(self):
        self.log(f'Executing {self.next_OB.align.name}')
        # Blind Align
        if isinstance(self.next_OB.align, BlindAlign):
            # Slew Telescope
            self.log(f'Slewing to: {self.next_OB.target}')
            try:
                self.telescope.slew(self.next_OB.target)
            except TelescopeFailure:
                self.log('Telescope slew failed', level=logging.ERROR)
                self.error_count += 1
                self.failed_slew()
            else:
                self.log('Slew complete')
                self.current_target = self.next_OB.target
                # End of Acquisition
                self.configure()
        # Other Align methods go here
        else:
            self.log(f"Did not recognize alignment {self.next_OB.align.name}",
                     level=logging.ERROR)
            self.failed.append(self.current_OB)
            self.failed_acquisition()


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
            self.log('Telescope parking failed', level=logging.ERROR)
            self.critical_failure()
        else:
            self.log('Telescope parked')
            self.current_target = None
            self.done_parking()


    ##-------------------------------------------------------------------------
    ## Instrument Controls
    def configure_instrument(self):
        self.log(f'configuring instrument: {self.next_OB.instconfig}')
        try:
            self.instrument.configure(self.next_OB.instconfig)
        except InstrumentFailure:
            self.log('Instrument configuration failed', level=logging.ERROR)
        self.observe()


    def begin_observation(self):
        self.log('starting observation')
        self.current_OB = self.next_OB
        self.next_OB = None
        try:
            self.detector.expose(self.current_OB.detconfig)
        except DetectorFailure:
            self.log('Detector failure', level=logging.ERROR)
            self.error_count += 1
        else:
#             ok = self.check_ok()
            ok = True
            if ok is True:
                self.log('observation complete')
                self.observed.append(self.current_OB)
            else:
                self.log('observation failed')
                self.failed.append(self.current_OB)
        self.select_OB()


    ##-------------------------------------------------------------------------
    ## Other
    def begin_end_of_night_shutdown(self):
        self.we_are_done = True


    def night_summary(self):
        for state in self.durations.keys():
            self.log(f'Spent {self.durations[state]:.1f}s in {state}')
        log.info('Observed:')
        for line in str(self.observed).split('\n'):
            log.info('  |'+line)
        log.info('Failed:')
        for line in str(self.failed).split('\n'):
            log.info('  |'+line)
