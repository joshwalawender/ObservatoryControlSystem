#!python3
from pathlib import Path
import importlib
from time import sleep
from datetime import datetime
import random
import numpy as np
import yaml
import logging

from astropy import units as u
from astropy.io import fits
from astropy import coordinates as c
from astropy.time import Time
from astropy.table import Table, Row

# Suppress IERS download failure
from astropy.utils.iers import conf
conf.auto_max_age = None

from transitions.extensions import GraphMachine
from transitions import Machine
from transitions import State

from odl.block import ObservingBlockList, ScienceBlock, FocusBlock
from odl.alignment import BlindAlign

from .exceptions import *
from .scheduler import Scheduler
from .focusing import FocusFitParabola, FocusMaxRun


##-------------------------------------------------------------------------
## Read Configuration
##-------------------------------------------------------------------------
def load_configuration(config_file=None):
    root_path = Path(__file__).parent
    if config_file is None:
        config_file = root_path.joinpath('config/config.yaml')
    elif isinstance(config_file, str):
        config_file = Path(config_file)
    if not isinstance(config_file, Path):
        raise Exception(f'Could not read config_file: {config_file}')
    if config_file.exists() is False:
        print('No config file found')
        sys.exit(0)
    with open(config_file) as FO:
        config = yaml.safe_load(FO)
    # Instantiate devices
    devices_path = root_path/'observatories'/config['name']/config['OTA']
    module_base_str = f"ocs.observatories.{config['name']}.{config['OTA']}"
    for component in ['weather', 'roof', 'telescope', 'instrument', 'detector']:
        print(f'Loading {component}: {config[component]}')
        if config[component] == 'simulator':
            module = importlib.import_module(f"ocs.simulator.{component}")
            device_config_file = root_path/"simulator"/f'{component}_config.yaml'
        else:
            module = importlib.import_module(module_base_str)#+f".{component}")
            device_config_file = devices_path/f'{component}_config.yaml'
        # Open the config file
        with open(device_config_file) as FO:
            config[f'{component}_config'] = yaml.safe_load(FO)
        if config[f'{component}_config'] is None:
            config[f'{component}_config'] = {}
        # Create an instance of the device controller
        instancename = component.capitalize()
        if component in ['instrument', 'detector']:
            instancename += 'Controller'
        config[component] = getattr(module, instancename)

    return config


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
def create_log(loglevel_console='INFO', logfile=None, loglevel_file='DEBUG'):
    log = logging.getLogger('RollOffRoof')
    log.setLevel(logging.DEBUG)
    ## Set up console output
    LogConsoleHandler = logging.StreamHandler()
    LogConsoleHandler.setLevel(getattr(logging, f'{loglevel_console.upper()}'))
    LogFormat = logging.Formatter('%(asctime)s %(levelname)7s %(message)s')
    LogConsoleHandler.setFormatter(LogFormat)
    log.addHandler(LogConsoleHandler)
    log.info(f'Log started')
    ## Set up file output
    if logfile is not None:
        LogFileName = Path(logfile)
        LogFileHandler = logging.FileHandler(LogFileName)
        LogFileHandler.setLevel(getattr(logging, f'{loglevel_file.upper()}'))
        LogFileHandler.setFormatter(LogFormat)
        log.addHandler(LogFileHandler)
        log.info(f'Logging to {LogFileName}')
    return log


##-------------------------------------------------------------------------
## Define Roll Off Roof Observatory Model
##-------------------------------------------------------------------------
class RollOffRoof():
    '''Simple observatory with roll off roof.
    '''
    def __init__(self, name='myobservatory', OTA='OTA',
                 states_file='states.yaml',
                 transitions_file='transitions.yaml',
                 location_file = 'location.yaml',
                 initial_state='sleeping',
                 waittime=2, maxwait=10, max_allowed_errors=0,
                 weather=None, weather_config={},
                 roof=None, roof_config={},
                 telescope=None, telescope_config={},
                 instrument=None, instrument_config={},
                 detector=None, detector_config={},
                 datadir='~', lat=0, lon=0, height=0,
                 loglevel_console='INFO', logfile=None, loglevel_file='DEBUG',
                 OBs=[],
                 ):
        self.name = name
        self.datadir = Path(datadir).expanduser().absolute()
        self.logger = create_log(loglevel_console=loglevel_console,
                                 logfile=logfile,
                                 loglevel_file=loglevel_file)
        # Components
        self.weather = weather(logger=self.logger, **weather_config)
        self.roof = roof(logger=self.logger, **roof_config)
        self.telescope = telescope(logger=self.logger, **telescope_config)
        self.instrument = instrument(logger=self.logger, **instrument_config)
        self.detector = detector(logger=self.logger, **detector_config)
        self.scheduler = Scheduler(OBs=OBs)
        # Load States File
        states_file = Path(__file__).parent / 'config' / states_file
        with open(states_file.expanduser().absolute()) as FO:
            self.states = yaml.safe_load(FO)
        # Load Transitions File
        transitions_file = Path(__file__).parent / 'config' / transitions_file
        with open(transitions_file.expanduser().absolute()) as FO:
            self.transitions = yaml.safe_load(FO)
        # Load Location
        self.location = c.EarthLocation(lat=lat, lon=lon, height=height)
        self.waittime = waittime
        self.maxwait = maxwait
        self.wait_duration = 0
        self.max_allowed_errors = max_allowed_errors
        try:
            raise Exception
            self.machine = GraphMachine(model=self,
                                        states=self.states,
                                        transitions=self.transitions,
                                        initial=initial_state,
                                        queued=True,
                                        use_pygraphviz=True,
                                        show_conditions=True,
                                        )
            # Generate state diagram
            self.machine.get_graph().draw('state_diagram.png', prog='dot')
        except:
            self.machine = Machine(model=self,
                                   states=self.states,
                                   transitions=self.transitions,
                                   initial=initial_state,
                                   queued=True,
                                   )
        # Initialize Status Values
        self.startup_at = datetime.now()
        self.entered_state_at = datetime.now()
        self.last_state = str(self.state)
        self.executed = Table(names=('type', 'target', 'pattern', 'instconfig',
                                     'detconfig', 'failed'),
                              dtype=('a20', 'a40', 'a20', 'a40', 'a40', np.bool))
        self.current_OB = None
        self.we_are_done = False
        self.durations = {}
        self.errors = []
        self.error_count = 0
        self.software_errors = []


    ##-------------------------------------------------------------------------
    ## Record Keeping Utilities
    def log(self, msg, level=logging.INFO):
        current_OB = f'{self.current_OB.blocktype} @ {self.current_OB.target}'\
                     if self.current_OB is not None else 'None'
        self.logger.log(level, f'{self.state:15s}|{current_OB:30s}: {msg}')


    def entry_timestamp(self):
        if str(self.state) != str(self.last_state):
            self.log(f'Entering state: {self.state} (from {self.last_state})')
            self.log('Resetting entry time', level=logging.DEBUG)
            self.entered_state_at = datetime.now()
        if str(self.state) == 'acquiring':
            self.wait_duration = 0


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
        self.log(f'  Location:')
        self.log(f'    latitude = {self.location.lat:.6f}')
        self.log(f'    longtiude = {self.location.lon:.6f}')
        self.log(f'    height = {self.location.height:.0f}')


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


    def begin_end_of_night_shutdown(self):
        self.we_are_done = True


    def night_summary(self):
        if self.error_count > 0:
            self.log(f'Encountered {self.error_count} errors',
                     level=logging.WARNING)

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
        self.log(f'\n\n====== Timing ======\n{duration_table}\n')
        self.log(f'\n\n====== Observed ======\n{self.executed}\n')


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
        obstime = Time.now()
#         sun = c.get_sun(time=obstime)
#         altaz = c.AltAz(location=self.location, obstime=obstime,
#                         obswl=0.5*u.micron)
#         sun_is_down = sun.transform_to(altaz).alt < 0
#         self.log(f'Sun is Down? {sun_is_down}', level=logging.DEBUG)
        # Replace this with a simple timer which has sunrise after a set time
        uptime = (datetime.now() - self.startup_at).total_seconds()
        sun_is_down = uptime < self.maxwait*3
        self.log(f'Is it dark? {sun_is_down}', level=logging.DEBUG)
        return sun_is_down


    def done_observing(self):
        too_many_errors = self.error_count > self.max_allowed_errors
        if too_many_errors is True:
            self.log(f'Error count for tonight exceeded', level=logging.ERROR)
            self.begin_end_of_night_shutdown()
        done_string = {True: '', False: 'not '}[self.we_are_done]

        if self.state == 'waiting_closed' and not self.is_dark():
            self.begin_end_of_night_shutdown()

        self.log(f'We are {done_string}shutting down', level=logging.DEBUG)
        return self.we_are_done


    def long_wait(self):
        return (self.wait_duration > self.maxwait)


    def not_done_observing(self):
        done = self.done_observing()
        self.log(f'Done observing? {done}')
        return not done


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
        ready_to_open = self.is_safe() and self.is_dark()\
                        and self.not_done_observing()\
                        and self.current_OB is not None
        return ready_to_open


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
            self.log(f'Got OB: {self.current_OB}')
        except SchedulingFailure as err:
            self.log(f'Scheduling error: {err}', level=logging.ERROR)
            self.software_errors.append(err)


    ##-------------------------------------------------------------------------
    ## On Entry Tasks for States
    def wait(self):
        sleep(0.0006)
        self.wait_duration = (datetime.now() - self.entered_state_at).total_seconds()
        if self.wait_duration > 0.001:
            self.log(f'Waiting {self.waittime} s')
            sleep(self.waittime)
        if self.state == 'waiting_closed':
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

            # Unpark
            if self.telescope.atpark() is True:
                self.log('Unparking telescope')
                self.telescope.unpark()
            # Set tracking
            if self.telescope.tracking() is False:
                self.log('Turning on tracking')
                self.telescope.set_tracking(True)

            # Blind Align
            if isinstance(self.current_OB.align, BlindAlign):
                # Slew Telescope
                self.log(f'Slewing to: {self.current_OB.target}')
                try:
                    self.telescope.slew(self.current_OB.target.coord())
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
        # Otherwise, park the telescope
        self.log(f'Parking Telescope')
        try:
            self.telescope.park()
        except TelescopeFailure as err:
            self.log('Telescope parking failed', level=logging.ERROR)
            self.errors.append(err)
            self.error_count += 1
        else:
            self.log('Telescope parked')
            self.current_target = None


    def configure_instrument(self):
        self.log(f'configuring instrument: {self.current_OB.instconfig}')
        try:
            self.instrument.configure(self.current_OB.instconfig)
        except InstrumentFailure as err:
            self.log('Instrument configuration failed', level=logging.ERROR)
            self.errors.append(err)
            self.error_count += 1
        self.start_observation()


    def begin_focusing(self):
        self.log('starting focusing')
        take_data_failed = True
        analyze_data_failed = True
        if isinstance(self.current_OB, FocusFitParabola):
            self.log(f'Focusing using simple parambola fit')
            failed = False
        elif isinstance(self.current_OB, FocusMaxRun):
            self.log(f'Focusing using FocusMax')
            failed = False
        else:
            self.log(f'Focus strategy {self.current_OB} is unknown',
                     level=logging.ERROR)
            failed = True
        self.record_OB(failed=failed)
        self.focusing_complete()


    def build_fits_filename(self, camera='cam'):
        date_time_string = datetime.utcnow().strftime(f'%Y%m%d_at_%H%M%S')
        fits_filename = f"{camera}_{date_time_string}UT.fits"
        fits_file = self.datadir.joinpath(fits_filename)
        return fits_file


    def begin_observation(self):
        '''For now we assume only one detconfig
        '''
        # Gather header info about OB
        obhdr = self.current_OB.to_header()
        dc = self.current_OB.detconfig[0]
        obhdr += dc.to_header()
        self.log(f'Starting observation: {self.current_OB.pattern}: {dc}')
        # Set detector parameters
        self.detector.set_exptime(dc.exptime)
        if dc.gain is not None:
            self.detector.set_gain(dc.gain)
        if dc.binning is not None:
            binx, biny = dc.binning.split('x')
            self.detector.set_binning(int(binx), int(biny))
        if dc.window is not None:
            self.detector.set_window(dc.window)
        # Start Observing
        dataok = []
        for i,position in enumerate(self.current_OB.pattern):
            self.log(f'  Starting observation at position {i+1} of {len(self.current_OB.pattern)}')
            # Offset to position
            obhdr.set('POSITION', value=i+1, comment='Offset pattern position number')
            # Set guiding for this position
            if position.guide is True:
                raise NotImplementedError('Guiding not implemented')
            else:
                self.log(f'  No guiding at this position')
                # Turn off guiding

            # Take Data
            for j in range(dc.nexp):
                obhdr.set('EXPNO', value=j+1, comment='Exposure number at this position')
                self.log(f'    Starting {dc.exptime:.0f}s exposure ({j+1} of {dc.nexp})')
                hdr = self.telescope.collect_header_metadata()
                hdr += self.instrument.collect_header_metadata()
                hdr += obhdr
                try:
                    hdul = self.detector.expose(additional_header=hdr)
                except DetectorFailure:
                    self.log('Detector failure', level=logging.ERROR)
                    hdul = None
                    self.error_count += 1
                else:
                    dataok.append(True)
                if hdul is not None:
                    fits_file = self.build_fits_filename(camera=f'cam{self.detector.device_number}')
                    self.log(f'    Writing {fits_file.name}')
                    hdul.writeto(fits_file, overwrite=False)
        # return to offset 0, 0
        allok = np.all(dataok)
        self.record_OB(failed=not allok)
        self.observation_complete()

