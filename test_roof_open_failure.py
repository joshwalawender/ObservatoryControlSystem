from ocs import load_configuration
from ocs.observatory import RollOffRoof
from simulatedobs import build_OBs
from pathlib import Path


logfile = Path(__file__.replace('test_', 'log_test_').replace('.py', '.txt'))
if logfile.exists(): logfile.unlink()


def test_roof_open_failure():
    OBs = build_OBs()
    config = load_configuration('simulatedobs')
    config['logfile'] = str(logfile)
    config['roof_config'] = {'roof_time_to_open': 0,
                             'roof_time_to_close': 0,
                             'open_fail_after': 0,
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
    assert simulatedobs.state == 'alert'
    assert simulatedobs.error_count <= config['max_allowed_errors']+2


if __name__ == '__main__':
    test_roof_open_failure()
