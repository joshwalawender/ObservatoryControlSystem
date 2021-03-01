from ocs.observatory import RollOffRoof
from simulatedobs import build_obs


import pytest
@pytest.mark.parametrize("test_input,expected", [(None, None)]*100)
def test_random_failures(test_input, expected):
    OBs, config = build_obs()
    config['logfile'] = __file__.replace('test_', 'log_test_').replace('.py', '.txt')
    config['waittime'] = 0
    config['maxwait'] = 0.1
    config['weather_config'] = {}
    config['roof_config'] = {'roof_time_to_open': 0,
                             'roof_time_to_close': 0,
                             'open_fail_after': None,
                             'open_random_fail_rate': 0.02,
                             'close_fail_after': None,
                             'close_random_fail_rate': 0.02,                         }
    config['telescope_config'] = {'time_to_slew': 0,
                                  'time_to_park': 0,
                                  'slew_fail_after': None,
                                  'slew_random_fail_rate': 0.02,
                                  'park_fail_after': None,
                                  'park_random_fail_rate': 0.02,
                                  }
    config['instrument_config'] = {'configure_fail_after': None,
                                   'configure_random_fail_rate': 0.02,
                                  }
    config['detector_config'] = {'exposure_overhead': 0,
                                 'expose_fail_after': None,
                                 'expose_random_fail_rate': 0.02,
                                 }

    simulatedobs = RollOffRoof(OBs=OBs, **config)
    simulatedobs.wake_up()
    assert simulatedobs.state in ['pau', 'alert']
    assert simulatedobs.error_count <= config['max_allowed_errors']+1


if __name__ == '__main__':
    test_random_failures(0, (True, True))
