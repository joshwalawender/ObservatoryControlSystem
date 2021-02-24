from odl.detector_config import VisibleDetectorConfig
from odl.instrument_config import InstrumentConfig
from odl.offset import Stare


##-------------------------------------------------------------------------
## CMOSCameraConfig
##-------------------------------------------------------------------------
class DSLRCameraConfig(VisibleDetectorConfig):
    '''An object to hold information about DSLR detector configuration.
    '''
    def __init__(self, name=None, exptime=None, nexp=1, readoutmode=0,
                 ampmode=9, dark=False, binning='1x1', window=None, gain=10):
        super().__init__(name=name, instrument='DSLRCamera', detector='', 
                         exptime=exptime, nexp=nexp, readoutmode=readoutmode,
                         ampmode=ampmode, dark=dark, binning=binning,
                         window=window)
        self.gain = gain


##-------------------------------------------------------------------------
## SVQ100_DSLR
##-------------------------------------------------------------------------
class SVQ100_DSLR(InstrumentConfig):
    '''An object to hold information about a filter wheel configuration.
    '''
    def __init__(self):
        self.name = f'DSLR'


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
