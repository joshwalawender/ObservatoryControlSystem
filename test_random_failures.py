from ocs.observatory import RollOffRoof
from simulatedobs import build_obs


import pytest
@pytest.mark.parametrize("test_input,expected", [(None, None)]*100)
def test_random_failures(test_input, expected):
    OBs, config = build_obs()
    config['logfile'] = __file__.replace('test_', 'log_test_').replace('.py', '.txt')

    config['roof_config']['open_random_fail_rate'] = 0.02
    config['roof_config']['close_random_fail_rate'] = 0.02
    config['telescope_config']['slew_random_fail_rate'] = 0.02
    config['telescope_config']['park_random_fail_rate'] = 0.02
    config['instrument_config']['configure_random_fail_rate'] = 0.02
    config['detector_config']['expose_random_fail_rate'] = 0.02

    simulatedobs = RollOffRoof(OBs=OBs, **config)
    simulatedobs.wake_up()
    assert simulatedobs.state in ['pau', 'alert']
    assert simulatedobs.error_count <= config['max_allowed_errors']+2


if __name__ == '__main__':
    test_random_failures(0, (True, True))
