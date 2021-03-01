from ocs.observatory import RollOffRoof
from simulatedobs import build_obs


def test_roof_open_failure():
    OBs, config = build_obs()
    config['logfile'] = __file__.replace('test_', 'log_test_').replace('.py', '.txt')

    config['roof_config']['open_fail_after'] = 0

    simulatedobs = RollOffRoof(OBs=OBs, **config)
    simulatedobs.wake_up()
    assert simulatedobs.state == 'pau'
    assert simulatedobs.error_count <= config['max_allowed_errors']+2


if __name__ == '__main__':
    test_roof_open_failure()
