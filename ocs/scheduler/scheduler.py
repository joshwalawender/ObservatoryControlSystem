from odl.block import ObservingBlockList, ObservingBlock
from odl.target import Target, TargetList
from odl.offset import Stare
from odl.alignment import BlindAlign, MaskAlign


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
OBs = [ObservingBlock(target=M42, align=blindalign, pattern=stare,
                      instconfig=filter_L, detconfig=exp300_x12),
       ObservingBlock(target=M42, align=blindalign, pattern=stare,
                      instconfig=filter_R, detconfig=exp300_x12),
       ObservingBlock(target=M42, align=MaskAlign(), pattern=stare,
                      instconfig=filter_G, detconfig=exp300_x12),
       ObservingBlock(target=M42, align=blindalign, pattern=stare,
                      instconfig=filter_B, detconfig=exp300_x12),
       ObservingBlock(target=M78, align=blindalign, pattern=stare,
                      instconfig=filter_L, detconfig=exp300_x12),
       ObservingBlock(target=M78, align=blindalign, pattern=stare,
                      instconfig=filter_R, detconfig=exp300_x12),
       ObservingBlock(target=M78, align=blindalign, pattern=stare,
                      instconfig=filter_G, detconfig=exp300_x12),
       ObservingBlock(target=M78, align=blindalign, pattern=stare,
                      instconfig=filter_B, detconfig=exp300_x12),
       ]


##-------------------------------------------------------------------------
## Scheduler
##-------------------------------------------------------------------------
class Scheduler():
    def __init__(self, OBs=OBs):
        self.OBs = OBs


    def select(self):
        if len(OBs) > 0:
            OB = self.OBs.pop(0)
        else:
            OB = None
        return OB
