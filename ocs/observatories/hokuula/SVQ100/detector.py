from astropy.io import fits

##-------------------------------------------------------------------------
## ODL DetectorConfig
##-------------------------------------------------------------------------
from odl.detector_config import DetectorConfig as AbstractDetectorConfig

class CMOSDetectorConfig(AbstractDetectorConfig):
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
        self.set_name()


    def set_name(self):
        self.name = f'{self}{self.detector} {self.exptime:.0f}s (gain {self.gain}) x{self.nexp}'


    def to_header(self):
        h = fits.Header()
        h['DCNAME'] = (self.name, 'Detector Config Name')
        h['DCINSTR'] = (self.instrument, 'Detector Config Instrument Name')
        h['DCDET'] = (self.detector, 'Detector Config Detector Name')
        h['DCEXPT'] = (self.exptime, 'Detector Config Exptime (sec)')
        h['DCNEXP'] = (self.nexp, 'Detector Config Number of Exposures')
        h['DCRDMODE'] = (self.readoutmode, 'Detector Config Readout Mode')
        h['DCBIN'] = (self.binning, 'Detector Config Binning')
        h['DCWINDOW'] = (self.window, 'Detector Config Window')
        h['DCGAIN'] = (self.gain, 'Detector Config Gain')
        return h


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
## Detector Controller
##-------------------------------------------------------------------------
from pypaca import Camera as DetectorController

