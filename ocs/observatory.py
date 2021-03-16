#!python3
from pathlib import Path
from time import sleep
from datetime import datetime
import random
import numpy as np
import yaml
import logging
from copy import deepcopy
import threading

from astropy import units as u
from astropy.io import fits
from astropy import coordinates as c
from astropy.time import Time, TimeDelta
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
from . import load_configuration, create_log


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
                 detector=None, detector_config=[{}],
                 datadir='~', lat=0, lon=0, height=0,
                 horizon=0,
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
        self.detector = [d(logger=self.logger, **detector_config[i]) for i,d in enumerate(detector)]
        self.scheduler = Scheduler(OBs=OBs)
        
        # Load States File
        with open(Path(states_file).expanduser()) as FO:
            self.states = yaml.safe_load(FO)
        # Load Transitions File
        with open(Path(transitions_file).expanduser()) as FO:
            self.transitions = yaml.safe_load(FO)
        # Load Location
        self.location = c.EarthLocation(lat=lat, lon=lon, height=height)
        self.horizon = horizon
        # Instantiate State Machine
        try:
            self.machine = GraphMachine(model=self,
                                        states=self.states,
                                        transitions=self.transitions,
                                        initial=initial_state,
                                        queued=True,
                                        use_pygraphviz=True,
                                        show_conditions=True,
                                        )
            # Generate state diagram
#             self.machine.get_graph().draw('state_diagram.png', prog='dot')
        except:
            self.machine = Machine(model=self,
                                   states=self.states,
                                   transitions=self.transitions,
                                   initial=initial_state,
                                   queued=True,
                                   )
        # Operational Properties
        self.waittime = waittime
        self.maxwait = maxwait
        self.wait_duration = 0
        self.max_allowed_errors = max_allowed_errors
        
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

        # Configure telescope hardware
        self.log(f'Sending location info to mount')
        self.telescope.set_sitelatitude(lat)
        assert np.isclose(lat, self.telescope.sitelatitude())
        self.telescope.set_sitelongitude(lon)
        assert np.isclose(lon, self.telescope.sitelongitude())
        self.telescope.set_siteelevation(height)
        assert np.isclose(height, self.telescope.siteelevation())
        self.log(f'Sending date and time to mount')
        now = datetime.utcnow()
        self.log(f'Computer time: {now.isoformat()}')
        self.telescope.set_utcdate(f"{now.isoformat()}Z")
        mountnow_str = self.telescope.utcdate()
        self.log(f'Mount time: {mountnow_str}')
        while len(mountnow_str) < 23: mountnow_str += '0'
        mountnow = datetime.fromisoformat(mountnow_str)
        dt = mountnow - now
        assert dt.total_seconds() < 0.25


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


    def get_horizon(self, az):
        '''Return the alt of the horizon for a given az
        '''
        def linterp(x1, y1, x2, y2, x3):
            return y1 + (y2-y1)*(x3-x1)/(x2-x1)

        if len(self.horizon) == 1:
            h = self.horizon['h'][0]
        elif az < self.horizon['az'][0]:
            h = self.horizon['h'][0]
        elif az > self.horizon['az'][-1]:
            h = linterp(self.horizon['az'][-1], self.horizon['h'][-1],
                        self.horizon['az'][0]+360, self.horizon['h'][0],
                        az)
        else:
            low = self.horizon[self.horizon['az'] < az]
            high = self.horizon[self.horizon['az'] >= az]
            h = linterp(low['az'][-1], low['h'][-1],
                        high['az'][0], high['h'][0],
                        az)
        return h


    def below_horizon(self):
        '''Check of the current OB is below the defined horizon or is about to
        set within the duration of the OB.
        '''
        duration = TimeDelta(self.current_OB.estimate_duration(), format='sec')
        altazframe = c.AltAz(obstime=Time.now() + duration,
                             location=self.location,
                             obswl=self.current_OB.instconfig.obswl,
#                              pressure=, temperature=,
#                              relative_humidity=,
                             )
        altaz_coord = self.current_OB.target.coord().transform_to(altazframe)
        self.log(f'OB will end at (alt, az) = ({altaz_coord.alt:.1f}, {altaz_coord.az:.1f})')

        h = self.get_horizon(altaz_coord.az.value)
        self.log(f'Horizon is {h:.1f} at {altaz_coord.az:.1f}')
        below = altaz_coord.alt.value <= h
        if below is True:
            self.log(f'Target is or will set below the horizon', level=logging.ERROR)
        return below


    ##-------------------------------------------------------------------------
    ## Scheduler
    def get_OB(self):
        try:
            self.current_OB = self.scheduler.select()
            self.log(f'Got OB: {self.current_OB}')
        except SchedulingFailure as err:
            self.log(f'Scheduling error: {err}', level=logging.ERROR)
            self.log(f'{err}', level=logging.ERROR)
            self.software_errors.append(err)


    ##-------------------------------------------------------------------------
    ## On Entry Tasks for States
    def cool_detector(self):
        pass


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
            self.log(f'{err}', level=logging.ERROR)
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
            self.log(f'{err}', level=logging.ERROR)
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
                    self.log(f'{err}', level=logging.ERROR)
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
            self.log(f'{err}', level=logging.ERROR)
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
            self.log(f'{err}', level=logging.ERROR)
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


    def begin_observation(self):
        '''
        '''
        self.log(f'Starting observations: {self.current_OB.pattern}')
        obhdr = self.current_OB.to_header()
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

            # Start exposures on all cameras
            threads = []
            headers = [deepcopy(obhdr) for dc in self.current_OB.detconfig]
            for j,dc in enumerate(self.current_OB.detconfig):
                self.log(f'Starting exposure thread {j}')
                threadargs = (headers[j], dc, self.telescope, self.instrument,
                              self.detector[j], self.datadir, self.logger)
                x = threading.Thread(target=start_obseravtion_thread,
                              args=threadargs)
                threads.append(x)
                x.start()
            for index, thread in enumerate(threads):
                thread.join()
                self.log(f"Exposure thread {index} done")

        # return to offset 0, 0
        self.record_OB(failed=False)
        self.observation_complete()


def build_fits_filename(camera='cam', datadir=Path('.')):
    date_time_string = datetime.utcnow().strftime(f'%Y%m%d_at_%H%M%S')
    fits_filename = f"{camera}_{date_time_string}UT.fits"
    fits_file = datadir.joinpath(fits_filename)
    return fits_file


def start_obseravtion_thread(obhdr, dc, telescope, instrument, detector, 
                             datadir, log):
    # Set detector parameters
    log.info(f'{dc.instrument} : Setting detector parameters')
    detector.setup_detector(dc)

    # Take Data
    filesok = []
    obhdr += dc.to_header()
    for j in range(dc.nexp):
        obhdr.set('EXPNO', value=j+1, comment='Exposure number at this position')
        log.info(f'{dc.instrument} : Starting {dc.exptime:.0f}s exposure ({j+1} of {dc.nexp})')
        hdr = telescope.collect_header_metadata()
        hdr += instrument.collect_header_metadata()
        hdr += obhdr
        try:
            hdul = detector.expose(additional_header=hdr)
        except DetectorFailure as err:
            log.error('{dc.instrument} : Detector failure')
            log.error(f'{dc.instrument} : {err}')
            hdul = None
        else:
            ff = build_fits_filename(camera=dc.instrument,
                                     datadir=datadir)
            log.info(f'{dc.instrument} : Writing {ff.name}')
            hdul.writeto(ff, overwrite=False)
            filesok.append(ff.exists())
    return filesok
