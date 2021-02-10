from odl.block import ObservingBlockList, ObservingBlock
from odl.target import Target, TargetList
from odl.offset import Stare
from odl.alignment import BlindAlign
from odl.detector_config import VisibleDetectorConfig
from odl.instrument_config import InstrumentConfig


##-------------------------------------------------------------------------
## DomeFlats
##-------------------------------------------------------------------------
domeflats = Target(name='DomeFlats', RA=0, Dec=0)


##-------------------------------------------------------------------------
## KCWIredDetectorConfig
##-------------------------------------------------------------------------
class CMOSCameraConfig(VisibleDetectorConfig):
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
## FilterWheel
##-------------------------------------------------------------------------
class FilterWheel(InstrumentConfig):
    '''An object to hold information about a filter wheel configuration.
    '''
    def __init__(self, filter='L'):
        self.name = f'{filter} Filter'
        self.filter = filter


    def biases(self):
        '''
        '''
        ic_for_bias = deepcopy(self)
        ic_for_bias.name += f' arclamp'
        dc_for_bias = CMOSCameraConfig(exptime=0)
        biases = CalibrationBlock(target=None,
                                  pattern=Stare(repeat=15),
                                  instconfig=ic_for_bias,
                                  detconfig=dc_for_bias,
                                  )
        return biases


    def domeflats(self):
        '''
        '''
        ic_for_domeflats = deepcopy(self)
        ic_for_domeflats.domeflatlamp = True
        lamp_str = {False: 'on', True: 'off'}[off]
        ic_for_domeflats.name += f' domelamp={lamp_str}'
        dc_for_domeflats = CMOSCameraConfig(exptime=100, 
                                            readoutmode='CDS')
        domeflats = CalibrationBlock(target=DomeFlats(),
                                   pattern=Stare(repeat=9),
                                   instconfig=ic_for_domeflats,
                                   detconfig=dc_for_domeflats,
                                   )
        return domeflats


    def cals(self):
        '''
        '''
        cals = ObservingBlockList()
        cals.append(self.biases())
        cals.append(self.domeflats())
        return cals


##-------------------------------------------------------------------------
## Build some test OBs
##-------------------------------------------------------------------------
M42 = Target('M42')
M78 = Target('M78')
blindalign = BlindAlign()
filter_L = FilterWheel(filter='L')
filter_R = FilterWheel(filter='R')
filter_G = FilterWheel(filter='G')
filter_B = FilterWheel(filter='B')
exp300_x12 = CMOSCameraConfig(exptime=300, nexp=12)
OBs = [ObservingBlock(target=M42, align=blindalign,
                      instconfig=filter_L, detconfig=exp300_x12),
       ObservingBlock(target=M42, align=BlindAlign(),
                      instconfig=filter_R, detconfig=exp300_x12),
       ObservingBlock(target=M42, align=BlindAlign(),
                      instconfig=filter_G, detconfig=exp300_x12),
       ObservingBlock(target=M42, align=BlindAlign(),
                      instconfig=filter_B, detconfig=exp300_x12),
       ObservingBlock(target=M78, align=BlindAlign(),
                      instconfig=filter_L, detconfig=exp300_x12),
       ObservingBlock(target=M78, align=BlindAlign(),
                      instconfig=filter_R, detconfig=exp300_x12),
       ObservingBlock(target=M78, align=BlindAlign(),
                      instconfig=filter_G, detconfig=exp300_x12),
       ObservingBlock(target=M78, align=BlindAlign(),
                      instconfig=filter_B, detconfig=exp300_x12),
       ]


class Scheduler():
    def __init__(self, OBs=OBs):
        self.OBs = OBs


    def select(self):
        if len(OBs) > 0:
            OB = self.OBs.pop(0)
        else:
            OB = None
        return OB

