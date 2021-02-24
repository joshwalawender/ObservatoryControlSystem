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
from astropy.table import Table, Row

# Suppress IERS download failure
from astropy.utils.iers import conf
conf.auto_max_age = None

from transitions.extensions import GraphMachine as Machine
# from transitions import Machine
from transitions import State

from odl.block import ObservingBlockList, ScienceBlock, FocusBlock
from odl.alignment import BlindAlign

from .exceptions import *
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
LogFormat = logging.Formatter('%(asctime)s %(levelname)7s %(message)s')
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
                 OBs=[],
                 ):
        self.name = name
        # Components
        self.weather = Weather(config=weather_config)
        self.roof = Roof(config=roof_config)
        self.telescope = Telescope(config=telescope_config)
        self.instrument = Instrument(config=instrument_config)
        self.detector = Detector(config=detector_config)
        self.scheduler = Scheduler(OBs=OBs)
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
                               queued=True,
                               use_pygraphviz=True,
                               show_conditions=True,
                               )
        # Initialize Status Values
        self.startup_at = datetime.now()
        self.entered_state_at = datetime.now()
        self.last_state = str(self.state)
        self.executed = Table(names=('type', 'target', 'pattern', 'instconfig',
                                     'detconfig', 'failed'),
                              dtype=('a20', 'a40', 'a20', 'a40', 'a40', np.bool))
        self.current_OB = None
        self.waitcount = 0
        self.we_are_done = False
        self.durations = {}
        self.errors = []
        self.error_count = 0
        self.software_errors = []
        # Generate state diagram
        self.machine.get_graph().draw('state_diagram.png', prog='dot')


    ##-------------------------------------------------------------------------
    ## Record Keeping Utilities
    def log(self, msg, level=logging.INFO):
        current_OB = f'{self.current_OB.blocktype} @ {self.current_OB.target}'\
                     if self.current_OB is not None else 'None'
        log.log(level, f'{self.state:15s}|{current_OB:30s}: {msg}')


    def entry_timestamp(self):
        self.log(f'Entering state: {self.state} (from {self.last_state})')
        self.entered_state_at = datetime.now()


    def exit_timestamp(self):
        self.last_state = str(self.state)
        duration = (datetime.now() - self.entered_state_at).total_seconds()
        self.log(f'Exiting state {self.state} after {duration:.1f}s',
                 level=logging.DEBUG)
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


    def record_OB(self, failed=False):
        row = {'type': self.current_OB.blocktype,
               'target': self.current_OB.target.name,
               'pattern': self.current_OB.pattern.name,
               'instconfig': self.current_OB.instconfig.name,
               'detconfig': ','.join([dc.name for dc in self.current_OB.detconfig]),
               'failed': failed}
        self.executed.add_row(row)
        sorf_string = {False: 'Succeeded', True: 'Failed'}[failed]
        sorf_level = {False: logging.INFO, True: logging.WARNING}[failed]
        self.log(f'OB {sorf_string}', level=sorf_level)
        self.current_OB = None


    def reset_waitcount(self):
        self.waitcount = 0


    def begin_end_of_night_shutdown(self):
        self.we_are_done = True


    def night_summary(self):
        if self.error_count > 0:
            log.warning(f'Encountered {self.error_count} errors')

        total_duration = (datetime.now() - self.startup_at).total_seconds()
        duration_table = Table(names=('State', 'Duration', 'Percent'),
                               dtype=(str, np.float, np.float))
        for state in self.durations.keys():
            row = {'State': state,
                   'Duration': self.durations[state],
                   'Percent': self.durations[state] / total_duration * 100}
            duration_table.add_row(row)
        duration_table['Percent'].format = '.1f'
        duration_table['Percent'].unit = u.percent
        duration_table['Duration'].format = '.0f'
        duration_table['Duration'].unit = u.second
        log.info(f'\n\n====== Timing ======\n{duration_table}\n')
        log.info(f'\n\n====== Observed ======\n{self.executed}\n')


    ##-------------------------------------------------------------------------
    ## Status Checks
    def is_safe(self):
        safe = self.weather.is_safe()
        self.log(f'Weather is Safe? {safe}', level=logging.DEBUG)
        return safe


    def is_unsafe(self):
        safe = self.weather.is_safe()
        self.log(f'Weather is Safe? {safe}', level=logging.DEBUG)
        return not safe



    def is_dark(self):
        self.log('Checking dark', level=logging.DEBUG)
        obstime = Time.now()
        sun = c.get_sun(time=obstime)
        altaz = c.AltAz(location=self.location, obstime=obstime,
#                         pressure=, temperature=, relative_humidity=,
                        obswl=0.5*u.micron)
        sun_is_down = sun.transform_to(altaz).alt < 0
        self.log(f'Sun is Down? {sun_is_down}', level=logging.DEBUG)
        sun_is_down = True
        return sun_is_down


    def done_observing(self):
        too_many_errors = self.error_count > self.max_allowed_errors
        if too_many_errors is True:
            self.log(f'Error count for tonight exceeded', level=logging.ERROR)
            self.begin_end_of_night_shutdown()
        done_string = {True: '', False: 'not '}[self.we_are_done]
        self.log(f'We are {done_string}shutting down', level=logging.DEBUG)
        return self.we_are_done


    def not_done_observing(self):
        return not self.done_observing()


    def no_target(self):
        return self.current_OB is None


    def have_target(self):
        return self.current_OB is not None


    def ready_to_open(self):
        '''Exit waiting closed only if
        
        - weather is safe
        - we have a target to observe
        - it is night
        - we're not shutting down for other reasons
        '''
        return self.is_safe() and self.is_dark() and self.not_done_observing()


    def acquisition_failed(self):
        acq_warnings = [isinstance(w, AcquisitionFailure) for w in self.errors]
        return np.any(acq_warnings)


    def focus_next(self):
        return isinstance(self.current_OB, FocusBlock)


    def focus_failed(self):
        foc_warnings = [isinstance(w, FocusFailure) for w in self.errors]
        return np.any(foc_warnings)


    def roof_err(self):
        roof_errors = [isinstance(w, RoofFailure) for w in self.errors]
        return np.any(roof_errors)


    ##-------------------------------------------------------------------------
    ## Scheduler
    def get_OB(self):
        try:
            self.current_OB = self.scheduler.select()
        except SchedulingFailure as err:
            self.log(f'Scheduling error: {err}', level=logging.ERROR)
            self.software_errors.append(err)


    ##-------------------------------------------------------------------------
    ## On Entry Tasks for States
    def wait(self):
        if self.last_state == self.state:
            sleep(self.waittime)
            self.waitcount += 1
            self.log(f'Incrementing wait count to {self.waitcount}',
                     level=logging.WARNING)
        if self.waitcount > self.maxwaits:
            self.log('Wait count exceeded', level=logging.ERROR)
            self.begin_end_of_night_shutdown()
            self.acquire()
        elif self.state == 'waiting_closed':
            self.get_OB()
            self.done_waiting()
        elif self.state == 'waiting_open':
            if self.current_OB is None:
                self.get_OB()
                self.log(f'Got next OB: {self.current_OB}')
            else:
                self.log(f'Already have next OB: {self.current_OB}')
            self.acquire()


    def open_roof(self):
        self.log('Opening the roof')
        try:
            self.roof.open()
        except RoofFailure as err: 
            self.log('Problem opening roof!', level=logging.ERROR)
            self.errors.append(err)
            self.error_count += 1
            self.begin_end_of_night_shutdown()
        self.done_opening()


    def close_roof(self):
        self.log('Closing the roof')
        try:
            self.roof.close()
        except RoofFailure as err:
            self.log('Roof failure on closing', logging.ERROR)
            self.errors.append(err)
            self.error_count += 1
        self.done_closing()


    def begin_acquisition(self):
        if self.current_OB is not None:
            self.log(f'Executing {self.current_OB.align.name}')
            # Blind Align
            if isinstance(self.current_OB.align, BlindAlign):
                # Slew Telescope
                self.log(f'Slewing to: {self.current_OB.target}')
                try:
                    self.telescope.slew(self.current_OB.target)
                except TelescopeFailure as err:
                    self.log('Telescope slew failed', level=logging.ERROR)
                    self.errors.append(err)
                    self.error_count += 1
                else:
                    self.log('Slew complete')
                    self.current_target = self.current_OB.target
                    # End of Acquisition
            # Other Align methods go here
            else:
                msg = f"Did not recognize alignment {self.current_OB.align.name}"
                self.log(msg, level=logging.ERROR)
                self.errors.append(AcquisitionFailure(msg))
                self.record_OB(failed=True)
        else:
            self.log('No OB to acquire', level=logging.DEBUG)
        self.done_acquiring()


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


    def configure_instrument(self):
        if self.current_OB is not None:
            self.log(f'configuring instrument: {self.current_OB.instconfig}')
            try:
                self.instrument.configure(self.current_OB.instconfig)
            except InstrumentFailure as err:
                self.log('Instrument configuration failed', level=logging.ERROR)
                self.errors.append(err)
                self.error_count += 1
        else:
            self.log('No OB to configure', level=logging.DEBUG)
        self.start_observation()


    def begin_focusing(self):
        self.log('starting focusing')
        take_data_failed = True
        analyze_data_failed = True
        if isinstance(self.current_OB, FocusBlock):
            take_focus_data = getattr(self.current_OB, "take_focus_data", None)
            if callable(take_focus_data) is True:
                self.log(f'Taking focus data for {self.current_OB.blocktype}')
                take_data_failed = not take_focus_data(self.instrument,
                                                       self.detector)
            analyze_focus_data = getattr(self.current_OB, "analyze_focus_data", None)
            if callable(analyze_focus_data) is True:
                self.log(f'Analyzing focus data for {self.current_OB.blocktype}')
                analyze_data_failed = not analyze_focus_data(self.instrument)
        else:
            self.log(f'Focus strategy {self.current_OB} is unknown',
                     level=logging.ERROR)
        self.record_OB(failed=(take_data_failed or analyze_data_failed))
        self.focusing_complete()


    def begin_observation(self):
        if self.current_OB is not None:
            self.log('starting observation')
            # set detector parameters
            # for position in OffsetPattern
            # - offset to position
            # - take data
            # return to offset 0, 0




            try:
                self.detector.expose(self.current_OB.detconfig)
            except DetectorFailure:
                self.log('Detector failure', level=logging.ERROR)
                self.error_count += 1
            else:
    #             ok = self.check_ok()
                ok = True
                self.record_OB(failed=not ok)
        else:
            self.log('No OB to observe', level=logging.DEBUG)
        self.observation_complete()

