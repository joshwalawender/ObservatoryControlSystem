from pathlib import Path
import yaml
from datetime import datetime

from ocs.simulators.weather import Weather
from ocs.simulators.roof import Roof
from ocs.simulators.telescope import Telescope
from ocs.simulators.instrument import Instrument
from ocs.simulators.detector import Detector

safety_file = Path('~/.safe.txt').expanduser()
now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
with open(safety_file, 'a') as FO:
    FO.write(f'{now} safe\n')

from ocs.observatory import RollOffRoof

root_path = Path(__file__).parent.joinpath('ocs/config')
with open(root_path / 'config.yaml') as FO:
    config = yaml.safe_load(FO)
with open(root_path.parent / 'simulators' / 'simulator_config.yaml') as FO:
    simulator_config = yaml.safe_load(FO)
config['Weather'] = Weather
config['Roof'] = Roof
config['roof_config'] = simulator_config
config['Telescope'] = Telescope
config['telescope_config'] = simulator_config
config['Instrument'] = Instrument
config['instrument_config'] = simulator_config
config['Detector'] = Detector
config['detector_config'] = simulator_config

obs = RollOffRoof(**config)
obs.wake_up()
