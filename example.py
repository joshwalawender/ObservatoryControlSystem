from pathlib import Path
from datetime import datetime

safety_file = Path('~/.safe.txt').expanduser()
now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
with open(safety_file, 'a') as FO:
    FO.write(f'{now} safe\n')

from ocs.observatory import obs

# obs.machine.get_graph().draw('state_diagram.png', prog='dot')

obs.wake_up()
