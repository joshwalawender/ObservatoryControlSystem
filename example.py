from pathlib import Path
import yaml
from datetime import datetime
import importlib

safety_file = Path('~/.safe.txt').expanduser()
now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
with open(safety_file, 'a') as FO:
    FO.write(f'{now} safe\n')


#-------------------------------------------------------------------------
# Build some test OBs
#-------------------------------------------------------------------------
from ocs.focusing import FocusFitParabola
from odl.block import ObservingBlockList, ScienceBlock, FocusBlock
from odl.target import Target, TargetList
from odl.offset import Stare
from odl.alignment import BlindAlign, MaskAlign

instr_module = importlib.import_module(f"ocs.instruments.SVQ100_ZWO")
detector_module = importlib.import_module(f"ocs.instruments.SVQ100_ZWO")
inst_config = getattr(instr_module, f"InstrumentConfig")
detector_config = getattr(detector_module, f"DetectorConfig")

M42 = Target('M42')
M78 = Target('M78')
blindalign = BlindAlign()
stare = Stare()
filter_L = inst_config(filter='L')
filter_R = inst_config(filter='R')
filter_G = inst_config(filter='G')
filter_B = inst_config(filter='B')
exp300_x12 = detector_config(exptime=300, nexp=12)
exp10 = detector_config(exptime=10, nexp=1)
OBs = [FocusFitParabola(target=M42, align=blindalign, pattern=stare,
                        instconfig=filter_L, detconfig=exp10,
                        n_focus_positions=7, focus_step=50),
       ScienceBlock(target=M42, align=blindalign, pattern=stare,
                    instconfig=filter_L, detconfig=exp300_x12),
       ScienceBlock(target=M42, align=blindalign, pattern=stare,
                    instconfig=filter_R, detconfig=exp300_x12),
#        ScienceBlock(target=M42, align=blindalign, pattern=stare,
#                     instconfig=filter_G, detconfig=exp300_x12),
#        ScienceBlock(target=M42, align=blindalign, pattern=stare,
#                     instconfig=filter_B, detconfig=exp300_x12),
#        FocusFitParabola(target=M78, align=blindalign, pattern=stare,
#                         instconfig=filter_L, detconfig=exp10,
#                         n_focus_positions=7, focus_step=50),
#        ScienceBlock(target=M78, align=blindalign, pattern=stare,
#                     instconfig=filter_L, detconfig=exp300_x12),
#        ScienceBlock(target=M78, align=blindalign, pattern=stare,
#                     instconfig=filter_R, detconfig=exp300_x12),
#        ScienceBlock(target=M78, align=blindalign, pattern=stare,
#                     instconfig=filter_G, detconfig=exp300_x12),
#        ScienceBlock(target=M78, align=blindalign, pattern=stare,
#                     instconfig=filter_B, detconfig=exp300_x12),
       ]
OBs = ObservingBlockList(OBs)


##-------------------------------------------------------------------------
## Instantiate the Observatory
##-------------------------------------------------------------------------
from ocs.observatory import RollOffRoof, load_configuration
config = load_configuration()
obs = RollOffRoof(OBs=OBs, **config)
obs.wake_up()
