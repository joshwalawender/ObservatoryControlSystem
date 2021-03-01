from ocs.observatory import RollOffRoof
from simulatedobs import build_obs


def test_roof_close_failure():
    OBs, config = build_obs()
    config['logfile'] = __file__.replace('test_', 'log_test_').replace('.py', '.txt')
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

    simulatedobs = RollOffRoof(OBs=OBs, **config)
    simulatedobs.wake_up()
    assert simulatedobs.state == 'alert'
    assert simulatedobs.error_count <= config['max_allowed_errors']+2


def test_roof_close_failure_with_other_failures():
    OBs, config = build_obs()
    config['logfile'] = __file__.replace('test_', 'log_test_').replace('.py', '.txt')
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
    config['telescope_config']['slew_fail_after'] = 2

    simulatedobs = RollOffRoof(OBs=OBs, **config)
    simulatedobs.wake_up()
    assert simulatedobs.state == 'alert'
    assert simulatedobs.error_count <= config['max_allowed_errors']+2


if __name__ == '__main__':
    test_roof_close_failure()
    test_roof_close_failure_with_other_failures()
