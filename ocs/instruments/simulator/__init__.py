from .instrument import InstrumentController
from .detector import DetectorController
from .weather import Weather
from .roof import Roof
from .telescope import Telescope

config = {
          # Roof
          'roof_time_to_open': 5,
          'roof_time_to_close': 1,
          'open_fail_after': None,
          'open_random_fail_rate': 0,
          'close_fail_after': None,
          'close_random_fail_rate': 0,
          # Telescope
          'time_to_slew': 1,
          'time_to_park': 1,
          'slew_fail_after': None,
          'slew_random_fail_rate': 0,
          'park_fail_after': None,
          'park_random_fail_rate': 0,
          # Instrument
          'configure_fail_after': None,
          'configure_random_fail_rate': 0,
          # Detector
          'exposure_overhead': 1,
          'expose_fail_after': None,
          'expose_random_fail_rate': 0,
         }
