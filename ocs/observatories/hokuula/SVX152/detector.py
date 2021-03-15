from astropy.io import fits

##-------------------------------------------------------------------------
## ODL DetectorConfig
##-------------------------------------------------------------------------
from odl.detector_config import CMOSDetectorConfig

class CanonDetectorConfig(CMOSDetectorConfig):
    def __init__(self, instrument='Canon 6D', detector='',
                 exptime=0, nexp=1, readoutmode='fast', gain=1, overhead=20,
                 binning='1x1', window=None, cooler_temp=None):
        super().__init__(instrument=instrument, detector=detector,
                         exptime=exptime, nexp=nexp, readoutmode=readoutmode,
                         gain=gain, overhead=overhead, binning=binning,
                         window=window)
        self.cooler_temp = cooler_temp
