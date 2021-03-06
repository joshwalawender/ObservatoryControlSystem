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

    from ocs.observatories.hokuula import InstrumentConfig
    from ocs.observatories.hokuula import ZWODetectorConfig
    from ocs.observatories.hokuula import CanonDetectorConfig

    t1 = Target('M31')
    t2 = Target('M78')
    blindalign = BlindAlign()
    stare = Stare(guide=False)
    filter_L = InstrumentConfig(filter='L')
    filter_R = InstrumentConfig(filter='R')
    filter_G = InstrumentConfig(filter='G')
    filter_B = InstrumentConfig(filter='B')
    SVQ100_exp = ZWODetectorConfig(exptime=10, nexp=2)
    SVX152_exp = CanonDetectorConfig(exptime=7, nexp=3)
    SVQ100_focus_exp = ZWODetectorConfig(exptime=1, nexp=1)
    SVX152_focus_exp = CanonDetectorConfig(exptime=1, nexp=1)

    OBs = [
#            FocusFitParabola(target=t1, align=blindalign, pattern=stare,
#                             instconfig=filter_L,
#                             detconfig=[SVQ100_focus_exp, SVX152_focus_exp],
#                             n_focus_positions=7, focus_step=50),
           ScienceBlock(target=t1, align=blindalign, pattern=stare,
                        instconfig=filter_L,
                        detconfig=[SVQ100_exp, SVX152_exp]),
           ScienceBlock(target=t1, align=blindalign, pattern=stare,
                        instconfig=filter_R,
                        detconfig=[SVQ100_exp, SVX152_exp]),
#            ScienceBlock(target=t1, align=blindalign, pattern=stare,
#                         instconfig=filter_G,
#                         detconfig=[SVQ100_exp, SVX152_exp]),
#            ScienceBlock(target=t1, align=blindalign, pattern=stare,
#                         instconfig=filter_B,
#                         detconfig=[SVQ100_exp, SVX152_exp]),
           ]
    OBs = ObservingBlockList(OBs)
    return OBs


if __name__ == '__main__':
    OBs = build_OBs()
    config = load_configuration('hokuula')
    hokuula = RollOffRoof(OBs=OBs, **config)
    hokuula.wake_up()
