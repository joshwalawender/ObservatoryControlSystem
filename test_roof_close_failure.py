from pathlib import Path
import yaml
from datetime import datetime
import importlib
from copy import deepcopy

from ocs.observatory import RollOffRoof, load_configuration


safety_file = Path('~/.safe.txt').expanduser()
now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
with open(safety_file, 'a') as FO:
    FO.write(f'{now} safe\n')


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
config = load_configuration()
config['waittime'] = 0
config['maxwait'] = 0.1
config['weather_config'] = {}
config['roof_config'] = {'roof_time_to_open': 0,
                         'roof_time_to_close': 0,
                         'open_fail_after': None,
                         'open_random_fail_rate': 0,
                         'close_fail_after': 0,
                         'close_random_fail_rate': 0,                         }
config['telescope_config'] = {'time_to_slew': 0,
                              'time_to_park': 0,
                              'slew_fail_after': None,
                              'slew_random_fail_rate': 0,
                              'park_fail_after': None,
                              'park_random_fail_rate': 0,
                              }
config['instrument_config'] = {'configure_fail_after': None,
                               'configure_random_fail_rate': 0,
                              }
config['detector_config'] = {'exposure_overhead': 0,
                             'expose_fail_after': None,
                             'expose_random_fail_rate': 0,
                             }


##-------------------------------------------------------------------------
## Tests
##-------------------------------------------------------------------------
def test_roof_close_failure():
    obs = RollOffRoof(OBs=deepcopy(OBs), **config)
    obs.wake_up()
    assert obs.state == 'alert'
    assert obs.error_count <= config['max_allowed_errors']+1


def test_roof_close_failure_with_other_failures():
    config['telescope_config']['slew_fail_after'] = 2
    obs = RollOffRoof(OBs=deepcopy(OBs), **config)
    obs.wake_up()
    assert obs.state == 'alert'
    assert obs.error_count <= config['max_allowed_errors']+2


if __name__ == '__main__':
    test_roof_close_failure()
    test_roof_close_failure_with_other_failures()
