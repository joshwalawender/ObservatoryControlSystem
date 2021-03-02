from pathlib import Path

from ocs import load_configuration
from ocs.observatory import RollOffRoof


def build_OBs():
    #-------------------------------------------------------------------------
    # Build some test OBs
    #-------------------------------------------------------------------------
    from ocs.focusing import FocusFitParabola
    from odl.block import ObservingBlockList, ScienceBlock, FocusBlock
    from odl.target import Target, TargetList
    from odl.offset import Stare
    from odl.alignment import BlindAlign, MaskAlign
    from odl.instrument_config import InstrumentConfig
    from odl.detector_config import CMOSDetectorConfig

    t1 = Target('M31')
    t2 = Target('M78')
    blindalign = BlindAlign()
    stare = Stare(guide=False)
    filter_L = InstrumentConfig()
    filter_R = InstrumentConfig()
    filter_G = InstrumentConfig()
    filter_B = InstrumentConfig()
    science_exp = CMOSDetectorConfig(exptime=20, nexp=2)
    focus_exp = CMOSDetectorConfig(exptime=3, nexp=1)
    OBs = [FocusFitParabola(target=t1, align=blindalign, pattern=stare,
                            instconfig=filter_L, detconfig=focus_exp,
                            n_focus_positions=7, focus_step=50),
           ScienceBlock(target=t1, align=blindalign, pattern=stare,
                        instconfig=filter_L, detconfig=science_exp),
           ScienceBlock(target=t1, align=blindalign, pattern=stare,
                        instconfig=filter_R, detconfig=science_exp),
           ScienceBlock(target=t1, align=blindalign, pattern=stare,
                        instconfig=filter_G, detconfig=science_exp),
           ScienceBlock(target=t1, align=blindalign, pattern=stare,
                        instconfig=filter_B, detconfig=science_exp),
           FocusFitParabola(target=t2, align=blindalign, pattern=stare,
                            instconfig=filter_L, detconfig=focus_exp,
                            n_focus_positions=7, focus_step=50),
           ScienceBlock(target=t2, align=blindalign, pattern=stare,
                        instconfig=filter_L, detconfig=science_exp),
           ScienceBlock(target=t2, align=blindalign, pattern=stare,
                        instconfig=filter_R, detconfig=science_exp),
           ScienceBlock(target=t2, align=blindalign, pattern=stare,
                        instconfig=filter_G, detconfig=science_exp),
           ScienceBlock(target=t2, align=blindalign, pattern=stare,
                        instconfig=filter_B, detconfig=science_exp),
           ]
    OBs = ObservingBlockList(OBs)
    return OBs


if __name__ == '__main__':
    OBs = build_OBs()
    config = load_configuration('simulatedobs')
    testobs = RollOffRoof(OBs=OBs, **config)
    testobs.wake_up()
