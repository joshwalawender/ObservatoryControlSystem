from ocs.observatory import RollOffRoof
from simulatedobs import build_obs
from pathlib import Path


logfile = Path(__file__.replace('test_', 'log_test_').replace('.py', '.txt'))
if logfile.exists(): logfile.unlink()


def test_no_equipment_errors():
    OBs, config = build_obs()
    config['logfile'] = str(logfile)

    simulatedobs = RollOffRoof(OBs=OBs, **config)
    simulatedobs.wake_up()
    assert simulatedobs.state == 'pau'
    assert simulatedobs.we_are_done is True
    assert simulatedobs.error_count == 0


if __name__ == '__main__':
    test_no_equipment_errors()
