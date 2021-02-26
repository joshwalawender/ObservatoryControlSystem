from odl.detector_config import DetectorConfig as AbstractDetectorConfig
from odl.instrument_config import InstrumentConfig
from odl.block import FocusBlock

# Use pypaca Camera as detector controller
from pypaca.devices.camera import Camera as DetectorController
from pypaca.devices import focuser, filterwheel

##-------------------------------------------------------------------------
## CMOSDetectorConfig
##-------------------------------------------------------------------------
class DetectorConfig(AbstractDetectorConfig):
    '''An object to hold information about a visible light detector
    configuration.  This is an abstract class which we expect to be subclassed
    to a particular instrument/detector.

    Attributes
    ----------
    readoutmode : str
        Either 'fast' or 'slow'

    gain : int
        The gain value.

    binning : str
        The binning, parsed as (nrows)x(ncolumns)

    window : str
        The window, parsed as x1:x2,y1:y2
    '''
    def __init__(self, name=None, instrument='CMOSCamera', detector='',
                 exptime=0, nexp=1, readoutmode='fast', gain=111,
                 binning='1x1', window=None):
        super().__init__(name=name, instrument=instrument, detector=detector,
                         exptime=exptime, nexp=nexp, readoutmode=readoutmode)
        self.binning = binning
        self.window = window
        self.gain = gain
        if name is None:
            self.set_name()
        else:
            self.name = name


    def set_name(self):
        self.name = f'{self.instrument}{self.detector} {self.exptime:.0f}s (gain {self.gain}) x{self.nexp}'


    def to_dict(self):
        output = super().to_dict()
        output['gain'] = self.gain
        output['binning'] = self.binning
        output['window'] = self.window
        return output


    def erase_time(self):
        return 0


    def readout_time(self):
        return 0


    def other_overhead(self):
        return 0


    def estimate_clock_time(self):
        total_time = self.erase_time()\
                   + self.exptime\
                   + self.readout_time()\
                   + self.other_overhead()
        return total_time*self.nexp


    def match_time(self, target):
        overhead_per_exp = self.other_overhead()\
                         + self.readout_time()\
                         + self.erase_time()
        self.exptime = target/self.nexp - overhead_per_exp
        self.set_name()


##-------------------------------------------------------------------------
## SVQ100_ZWO InstrumentConfig
##-------------------------------------------------------------------------
class InstrumentConfig(InstrumentConfig):
    '''InstrumentConfig object for a setup comprised of:
    - ZWO Filter Wheel
    - Optec Focuser
    '''
    def __init__(self, filter='L', focuspos=None):
        self.name = f'{filter} Filter'
        self.filter = filter
        self.focuspos = focuspos


##-------------------------------------------------------------------------
## SVQ100_ZWO Instrument Controller
##-------------------------------------------------------------------------
class InstrumentController():
    def __init__(self):
        self.filterwheel = filterwheel.FilterWheel()
        self.focuser = focuser.Focuser()
        config_file = Path(__file__).parent
        print(config_file)


    def configure(self, ic):
        '''Set hardware in a state described by the input InstrumentConfig
        '''
        pass
