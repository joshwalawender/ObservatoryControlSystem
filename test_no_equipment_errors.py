from ocs import load_configuration
from ocs.observatory import RollOffRoof
from simulatedobs import build_OBs
from pathlib import Path


logfile = Path(__file__.replace('test_', 'log_test_').replace('.py', '.txt'))
if logfile.exists(): logfile.unlink()


def test_no_equipment_errors():
    OBs = build_OBs()
    config = load_configuration('simulatedobs')
    config['logfile'] = str(logfile)

    config['waittime'] = 0.005
    config['maxwait'] = 0.010
    config['roof_config'] = {'roof_time_to_open': 0,
                             'roof_time_to_close': 0,
                             'open_fail_after': None,
                             'open_random_fail_rate': 0,
                             'close_fail_after': None,
                             'close_random_fail_rate': 0}
    config['telescope_config'] = {'time_to_slew': 0,
                                  'time_to_park': 0,
                                  'slew_fail_after': None,
                                  'slew_random_fail_rate': 0,
                                  'park_fail_after': None,
                                  'park_random_fail_rate': 0,
                                  }
    config['instrument_config'] = {'time_to_configure': 0,
                                   'configure_fail_after': None,
                                   'configure_random_fail_rate': 0,
                                  }
    config['detector_config'] = {'exposure_overhead': 0,
                                 'expose_fail_after': None,
                                 'expose_random_fail_rate': 0,
                                 'simulate_exposure_time': False,
                                 }

    simulatedobs = RollOffRoof(OBs=OBs, **config)
    simulatedobs.wake_up()
    assert simulatedobs.state == 'pau'
    assert simulatedobs.we_are_done is True
    assert simulatedobs.error_count == 0


if __name__ == '__main__':
    test_no_equipment_errors()
