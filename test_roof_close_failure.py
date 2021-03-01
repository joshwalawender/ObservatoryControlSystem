from ocs.observatory import RollOffRoof
from simulatedobs import build_obs


def test_roof_close_failure():
    OBs, config = build_obs()
    config['logfile'] = __file__.replace('test_', 'log_test_').replace('.py', '.txt')

    config['roof_config']['close_fail_after'] = 0

    simulatedobs = RollOffRoof(OBs=OBs, **config)
    simulatedobs.wake_up()
    assert simulatedobs.state == 'alert'
    assert simulatedobs.error_count <= config['max_allowed_errors']+2


def test_roof_close_failure_with_other_failures():
    OBs, config = build_obs()
    config['logfile'] = __file__.replace('test_', 'log_test_').replace('.py', '.txt')

    config['roof_config']['close_fail_after'] = 0
    config['telescope_config']['slew_fail_after'] = 2

    simulatedobs = RollOffRoof(OBs=OBs, **config)
    simulatedobs.wake_up()
    assert simulatedobs.state == 'alert'
    assert simulatedobs.error_count <= config['max_allowed_errors']+2


if __name__ == '__main__':
    test_roof_close_failure()
    test_roof_close_failure_with_other_failures()
