from pathlib import Path
import logging

from odl.block import FocusBlock


class HardwareFailure(Exception): pass
class RoofFailure(HardwareFailure): pass
class TelescopeFailure(HardwareFailure): pass
class InstrumentFailure(HardwareFailure): pass
class DetectorFailure(HardwareFailure): pass
class FocusFailure(HardwareFailure): pass

class SoftwareFailure(Exception): pass
class SchedulingFailure(SoftwareFailure): pass
class AcquisitionFailure(SoftwareFailure): pass


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
log = logging.getLogger('OCS')
log.setLevel(logging.DEBUG)
## Set up console output
LogConsoleHandler = logging.StreamHandler()
LogConsoleHandler.setLevel(logging.DEBUG)
LogFormat = logging.Formatter('%(asctime)s %(levelname)8s: %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')
LogConsoleHandler.setFormatter(LogFormat)
log.addHandler(LogConsoleHandler)
## Set up file output
# LogFileName = None
# LogFileHandler = logging.FileHandler(LogFileName)
# LogFileHandler.setLevel(logging.DEBUG)
# LogFileHandler.setFormatter(LogFormat)
# log.addHandler(LogFileHandler)


##-------------------------------------------------------------------------
## Focus Routines
##-------------------------------------------------------------------------
class FocusFitParabola(FocusBlock):
    '''An observing block describing a focus observation which takes several
    images and measures the FWHM in each, then fits a parabola to find the best
    focus position.
    '''
    def __init__(self, target=None, pattern=None, instconfig=None,
                 detconfig=None, align=None, n_focus_points=7, focus_step=50,
                 blocktype='FocusFitParabola'):
        super().__init__(target=target, pattern=pattern, instconfig=instconfig,
                         detconfig=detconfig, align=align, blocktype=blocktype)
        self.n_focus_points = n_focus_points
        self.focus_step = focus_step
