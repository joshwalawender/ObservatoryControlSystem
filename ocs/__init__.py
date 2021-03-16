from pathlib import Path
import importlib
import yaml
import logging
import sys
from astropy.table import Table


##-------------------------------------------------------------------------
## Load Configuration
##-------------------------------------------------------------------------
def load_configuration(obsname):
    root_path = Path(__file__).parent/'observatories'/obsname
    config_file = root_path / f'{obsname}.yaml'
    if config_file.exists() is False:
        print(f'Config file not found: {config_file}')
        sys.exit(0)
    with open(config_file) as FO:
        config = yaml.safe_load(FO)
    config['name'] = obsname

    # Instantiate devices
    devices_path = root_path
    module_base_str = f"ocs.observatories.{config['name']}"
    for component in ['weather', 'roof', 'telescope', 'instrument', 'detector']:
        if component == 'detector':
            module = importlib.import_module(module_base_str)
        else:
            if config[f'{component}_config']['name'] == 'simulator':
                module = importlib.import_module(f"ocs.simulator.{component}")
            else:
                module = importlib.import_module(module_base_str)
        # Create an instance of the device controller
        instancename = component.capitalize()
        if component == 'instrument':
            instancename += 'Controller'
        if component == 'detector':
            config[component] = []
            for det in config['detector_config']:
                instancename = f'{det["name"]}DetectorController'
                det.pop('name')
                config[component].append(getattr(module, instancename))
        else:
            config[component] = getattr(module, instancename)
            config[f'{component}_config'].pop('name')

    # Set defaults
    if 'states_file' not in config.keys():
        config['states_file'] = str(Path(__file__).parent.absolute()/'config'/'states.yaml')
    if 'transitions_file' not in config.keys():
        config['transitions_file'] = str(Path(__file__).parent.absolute()/'config'/'transitions.yaml')
    if 'initial_state' not in config.keys():
        config['initial_state'] = 'sleeping'

    # Read horizon
    if type(config['horizon']) in [float, int]:
        config['horizon'] = Table([{'az': 0, 'h': config['horizon']}])
    else:
        hpath = root_path / config['horizon']
        config['horizon'] = Table.read(hpath, format='ascii.csv')
        config['horizon'].sort('az')

    return config


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
def create_log(loglevel_console='INFO', logfile=None, loglevel_file='DEBUG'):
    if logfile is not None:
        logname = str(Path(logfile).name)
        logname = logname.replace('log_', '').replace('.txt', '')
    else:
        logname = 'RollOffRoof'
    log = logging.getLogger(logname)
    if len(log.handlers) == 0:
        log.setLevel(logging.DEBUG)
        ## Set up console output
        LogConsoleHandler = logging.StreamHandler()
        LogConsoleHandler.setLevel(getattr(logging, f'{loglevel_console.upper()}'))
        LogFormat = logging.Formatter('%(asctime)s %(levelname)7s %(message)s')
        LogConsoleHandler.setFormatter(LogFormat)
        log.addHandler(LogConsoleHandler)
        ## Set up file output
        if logfile is not None:
            LogFileName = Path(logfile)
            LogFileHandler = logging.FileHandler(LogFileName)
            LogFileHandler.setLevel(getattr(logging, f'{loglevel_file.upper()}'))
            LogFileHandler.setFormatter(LogFormat)
            log.addHandler(LogFileHandler)

        log.info(f'Log Started: {logname}')
        if logfile is not None:
            log.info(f'Logging to {LogFileName.absolute()}')
    return log


