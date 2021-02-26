from odl.detector_config import VisibleDetectorConfig
from odl.instrument_config import InstrumentConfig
from odl.block import FocusBlock

# Use pypaca Camera as detector controller
from pypaca.devices.camera import Camera as DetectorController
from pypaca.devices import focuser, filterwheel

##-------------------------------------------------------------------------
## CMOSCameraConfig
##-------------------------------------------------------------------------
class DetectorConfig(VisibleDetectorConfig):
    '''An object to hold information about CMOS detector configuration.
    '''
    def __init__(self, name=None, exptime=None, nexp=1, readoutmode=0,
                 ampmode=9, dark=False, binning='1x1', window=None, gain=10):
        super().__init__(name=name, instrument='CMOSCamera', detector='', 
                         exptime=exptime, nexp=nexp, readoutmode=readoutmode,
                         ampmode=ampmode, dark=dark, binning=binning,
                         window=window)
        self.gain = gain


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
