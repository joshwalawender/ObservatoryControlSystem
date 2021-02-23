from odl.block import ObservingBlockList, ScienceBlock, FocusBlock
from odl.target import Target, TargetList
from odl.offset import Stare
from odl.alignment import BlindAlign, MaskAlign

from ..focusing import FocusFitParabola
from ..exceptions import *


##-------------------------------------------------------------------------
## Build some test OBs
##-------------------------------------------------------------------------
M42 = Target('M42')
M78 = Target('M78')
blindalign = BlindAlign()
stare = Stare()
from .SVQ100_ZWO import SVQ100_ZWO, CMOSCameraConfig
filter_L = SVQ100_ZWO(filter='L')
filter_R = SVQ100_ZWO(filter='R')
filter_G = SVQ100_ZWO(filter='G')
filter_B = SVQ100_ZWO(filter='B')
exp300_x12 = CMOSCameraConfig(exptime=300, nexp=12)
exp10 = CMOSCameraConfig(exptime=10, nexp=1)
OBs = [FocusFitParabola(target=M42, align=blindalign, pattern=stare,
                        instconfig=filter_L, detconfig=exp10,
                        n_focus_positions=7, focus_step=50),
       ScienceBlock(target=M42, align=blindalign, pattern=stare,
                    instconfig=filter_L, detconfig=exp300_x12),
       ScienceBlock(target=M42, align=blindalign, pattern=stare,
                    instconfig=filter_R, detconfig=exp300_x12),
       ScienceBlock(target=M42, align=blindalign, pattern=stare,
                    instconfig=filter_G, detconfig=exp300_x12),
       ScienceBlock(target=M42, align=blindalign, pattern=stare,
                    instconfig=filter_B, detconfig=exp300_x12),
       FocusFitParabola(target=M78, align=blindalign, pattern=stare,
                        instconfig=filter_L, detconfig=exp10,
                        n_focus_positions=7, focus_step=50),
       ScienceBlock(target=M78, align=blindalign, pattern=stare,
                    instconfig=filter_L, detconfig=exp300_x12),
       ScienceBlock(target=M78, align=blindalign, pattern=stare,
                    instconfig=filter_R, detconfig=exp300_x12),
       ScienceBlock(target=M78, align=blindalign, pattern=stare,
                    instconfig=filter_G, detconfig=exp300_x12),
       ScienceBlock(target=M78, align=blindalign, pattern=stare,
                    instconfig=filter_B, detconfig=exp300_x12),
       ]
OBs = ObservingBlockList(OBs)

##-------------------------------------------------------------------------
## Scheduler
##-------------------------------------------------------------------------
class Scheduler():
    def __init__(self, OBs=OBs):
        self.OBs = OBs


    def select(self):
        if len(OBs) > 0:
            return self.OBs.pop(0)
        else:
            return None
#             raise SchedulingFailure('No OBs available')
