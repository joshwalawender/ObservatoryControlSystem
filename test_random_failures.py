from ocs.observatory import RollOffRoof
from simulatedobs import build_obs
from pathlib import Path
from copy import deepcopy


logfile = Path(__file__.replace('test_', 'log_test_').replace('.py', '.txt'))
if logfile.exists(): logfile.unlink()

OBs, config = build_obs()
config['logfile'] = str(logfile)
config['roof_config']['open_random_fail_rate'] = 0.02
config['roof_config']['close_random_fail_rate'] = 0.02
config['telescope_config']['slew_random_fail_rate'] = 0.02
config['telescope_config']['park_random_fail_rate'] = 0.02
config['instrument_config']['configure_random_fail_rate'] = 0.02
config['detector_config']['expose_random_fail_rate'] = 0.02


import pytest
@pytest.mark.parametrize("OBs,config,expected", [(OBs, config, None)]*25)
def test_random_failures(OBs, config, expected):
    simulatedobs = RollOffRoof(OBs=deepcopy(OBs), **config)
    simulatedobs.wake_up()
    assert simulatedobs.state in ['pau', 'alert']
    assert simulatedobs.error_count <= config['max_allowed_errors']+2


if __name__ == '__main__':
    test_random_failures(0, (True, True))
