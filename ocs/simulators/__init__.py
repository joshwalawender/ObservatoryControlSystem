from pathlib import Path
import yaml

root_path = Path(__file__).parent
with open(root_path / 'simulator_config.yaml') as config_file:
    config = yaml.safe_load(config_file)

