from pathlib import Path
import yaml
from datetime import datetime

from ocs.simulators.weather import Weather
from ocs.simulators.roof import Roof
from ocs.simulators.telescope import Telescope
from ocs.simulators.instrument import Instrument
from ocs.simulators.detector import Detector

safety_file = Path('~/.safe.txt').expanduser()
now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
with open(safety_file, 'a') as FO:
    FO.write(f'{now} safe\n')

from ocs.observatory import RollOffRoof


##-------------------------------------------------------------------------
## Build some test OBs
##-------------------------------------------------------------------------
from ocs.focusing import FocusFitParabola
from ocs.instruments.SVQ100_ZWO import SVQ100_ZWO, CMOSCameraConfig
from odl.block import ObservingBlockList, ScienceBlock, FocusBlock
from odl.target import Target, TargetList
from odl.offset import Stare
from odl.alignment import BlindAlign, MaskAlign

M42 = Target('M42')
M78 = Target('M78')
blindalign = BlindAlign()
stare = Stare()
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
## Read Configuration
##-------------------------------------------------------------------------
root_path = Path(__file__).parent.joinpath('ocs/config')
with open(root_path / 'config.yaml') as FO:
    config = yaml.safe_load(FO)
with open(root_path.parent / 'simulators' / 'simulator_config.yaml') as FO:
    simulator_config = yaml.safe_load(FO)
config['Weather'] = Weather
config['Roof'] = Roof
config['roof_config'] = simulator_config
config['Telescope'] = Telescope
config['telescope_config'] = simulator_config
config['Instrument'] = Instrument
config['instrument_config'] = simulator_config
config['Detector'] = Detector
config['detector_config'] = simulator_config


##-------------------------------------------------------------------------
## Instantiate the Observatory
##-------------------------------------------------------------------------
obs = RollOffRoof(OBs=OBs, **config)
obs.wake_up()
