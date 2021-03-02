from pathlib import Path
import importlib
import yaml
import logging


##-------------------------------------------------------------------------
## Read Configuration
##-------------------------------------------------------------------------
def load_configuration(config_file=None):
    root_path = Path(__file__).parent
    if config_file is None:
        config_file = root_path.joinpath('config/config.yaml')
    elif isinstance(config_file, str):
        config_file = Path(config_file)
    if not isinstance(config_file, Path):
        raise Exception(f'Could not read config_file: {config_file}')
    if config_file.exists() is False:
        print('No config file found')
        sys.exit(0)
    with open(config_file) as FO:
        config = yaml.safe_load(FO)

    # Instantiate devices
    devices_path = root_path/'observatories'/config['name']/config['OTA']
    module_base_str = f"ocs.observatories.{config['name']}.{config['OTA']}"
    for component in ['weather', 'roof', 'telescope', 'instrument', 'detector']:
        print(f'Loading {component}: {config[component]}')
        if config[component] == 'simulator':
            module = importlib.import_module(f"ocs.simulator.{component}")
            device_config_file = root_path/"simulator"/f'{component}_config.yaml'
        else:
            module = importlib.import_module(module_base_str)#+f".{component}")
            device_config_file = devices_path/f'{component}_config.yaml'
        # Open the config file
        with open(device_config_file) as FO:
            config[f'{component}_config'] = yaml.safe_load(FO)
        if config[f'{component}_config'] is None:
            config[f'{component}_config'] = {}
        # Create an instance of the device controller
        instancename = component.capitalize()
        if component in ['instrument', 'detector']:
            instancename += 'Controller'
        config[component] = getattr(module, instancename)

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
            log.info(f'Logging to {LogFileName}')
    return log


