from ocs.observatory import RollOffRoof
from simulatedobs import build_obs


def test_no_equipment_errors():
    OBs, config = build_obs()
    config['waittime'] = 0
    config['maxwait'] = 0.1
    config['logfile'] = __file__.replace('test_', 'log_test_').replace('.py', '.txt')

    simulatedobs = RollOffRoof(OBs=OBs, **config)
    simulatedobs.wake_up()
    assert simulatedobs.state == 'pau'
    assert simulatedobs.we_are_done is True
    assert simulatedobs.error_count == 0


if __name__ == '__main__':
    test_no_equipment_errors()
