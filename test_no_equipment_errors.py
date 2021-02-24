from pathlib import Path
import yaml
from datetime import datetime

safety_file = Path('~/.safe.txt').expanduser()
now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
with open(safety_file, 'a') as FO:
    FO.write(f'{now} safe\n')

from ocs.observatory import RollOffRoof
from ocs.simulators.weather import Weather
from ocs.simulators.roof import Roof
from ocs.simulators.telescope import Telescope
from ocs.simulators.instrument import Instrument
from ocs.simulators.detector import Detector

## Set up file output for log
import logging
log = logging.getLogger('RollOffRoof')
log.setLevel(logging.DEBUG)
LogFileName = __file__.replace('test_', 'log_test_').replace('.py', '.txt')
LogFileHandler = logging.FileHandler(LogFileName)
LogFileHandler.setLevel(logging.DEBUG)
LogFormat = logging.Formatter('%(asctime)s %(levelname)6s %(message)s')
LogFileHandler.setFormatter(LogFormat)
log.addHandler(LogFileHandler)
log.info('\n\n******** Beginning Tests ********\n')


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
with open(root_path / 'config.yaml') as config_file:
    config = yaml.safe_load(config_file)
simulator_config = {'roof_time_to_open': 0,
                    'roof_time_to_close': 0,
                    'time_to_slew': 0,
                    'time_to_park': 0,
                    'exposure_overhead': 0,
                    'open_fail_after': None,
                    'open_random_fail_rate': 0,
                    'close_fail_after': None,
                    'close_random_fail_rate': 0,
                    'slew_fail_after': None,
                    'slew_random_fail_rate': 0,
                    'park_fail_after': None,
                    'park_random_fail_rate': 0,
                    'configure_fail_after': None,
                    'configure_random_fail_rate': 0,
                    'expose_fail_after': None,
                    'expose_random_fail_rate': 0}
config['waittime'] = 0
config['Weather'] = Weather
config['Roof'] = Roof
config['Telescope'] = Telescope
config['Instrument'] = Instrument
config['Detector'] = Detector
config['roof_config'] = simulator_config
config['telescope_config'] = simulator_config
config['instrument_config'] = simulator_config
config['detector_config'] = simulator_config




def test_no_equipment_errors():
    obs = RollOffRoof(OBs=OBs, **config)
    obs.wake_up()
    assert obs.state == 'pau'
    assert obs.we_are_done is True
    assert obs.error_count == 0


if __name__ == '__main__':
    test_no_equipment_errors()
