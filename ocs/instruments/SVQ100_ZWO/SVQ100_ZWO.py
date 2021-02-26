from odl.detector_config import VisibleDetectorConfig
from odl.instrument_config import InstrumentConfig
from odl.block import FocusBlock

import pypaca


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


    def biases(self):
        '''
        '''
        ic_for_bias = deepcopy(self)
        ic_for_bias.name += f' bias'
        dc_for_bias = CMOSCameraConfig(exptime=0)
        biases = CalibrationBlock(target=None,
                                  pattern=Stare(repeat=15),
                                  instconfig=ic_for_bias,
                                  detconfig=dc_for_bias,
                                  )
        return biases


    def cals(self):
        '''
        '''
        cals = ObservingBlockList()
        cals.append(self.biases())
#         cals.append(self.domeflats())
        return cals


##-------------------------------------------------------------------------
## SVQ100_ZWO Instrument Controller
##-------------------------------------------------------------------------
class SVQ100_ZWOController():
    def __init__(self):
        self.filterwheel = pypaca.filterwheel.FilterWheel()


class SVQ100_ZWODetectorController():
    def __init__(self):
        pass

