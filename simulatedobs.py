from pathlib import Path
from datetime import datetime

from ocs.observatory import RollOffRoof, load_configuration


def build_obs():
    # Set weather safety
    safety_file = Path('~/.safe.txt').expanduser()
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    with open(safety_file, 'a') as FO:
        FO.write(f'{now} safe\n')

    #-------------------------------------------------------------------------
    # Build some test OBs
    #-------------------------------------------------------------------------
    from ocs.focusing import FocusFitParabola
    from odl.block import ObservingBlockList, ScienceBlock, FocusBlock
    from odl.target import Target, TargetList
    from odl.offset import Stare
    from odl.alignment import BlindAlign, MaskAlign

    from ocs.observatories.hokuula.SVQ100 import SVQ100Config, CMOSDetectorConfig

    t1 = Target('M31')
    t2 = Target('M78')
    blindalign = BlindAlign()
    stare = Stare(guide=False)
    filter_L = SVQ100Config(filter='L')
    filter_R = SVQ100Config(filter='R')
    filter_G = SVQ100Config(filter='G')
    filter_B = SVQ100Config(filter='B')
    science_exp = CMOSDetectorConfig(exptime=20, nexp=2)
    focus_exp = CMOSDetectorConfig(exptime=3, nexp=1)
    OBs = [FocusFitParabola(target=t1, align=blindalign, pattern=stare,
                            instconfig=filter_L, detconfig=focus_exp,
                            n_focus_positions=7, focus_step=50),
           ScienceBlock(target=t1, align=blindalign, pattern=stare,
                        instconfig=filter_L, detconfig=science_exp),
           ScienceBlock(target=t1, align=blindalign, pattern=stare,
                        instconfig=filter_R, detconfig=science_exp),
           ScienceBlock(target=t1, align=blindalign, pattern=stare,
                        instconfig=filter_G, detconfig=science_exp),
           ScienceBlock(target=t1, align=blindalign, pattern=stare,
                        instconfig=filter_B, detconfig=science_exp),
           FocusFitParabola(target=t2, align=blindalign, pattern=stare,
                            instconfig=filter_L, detconfig=focus_exp,
                            n_focus_positions=7, focus_step=50),
           ScienceBlock(target=t2, align=blindalign, pattern=stare,
                        instconfig=filter_L, detconfig=science_exp),
           ScienceBlock(target=t2, align=blindalign, pattern=stare,
                        instconfig=filter_R, detconfig=science_exp),
           ScienceBlock(target=t2, align=blindalign, pattern=stare,
                        instconfig=filter_G, detconfig=science_exp),
           ScienceBlock(target=t2, align=blindalign, pattern=stare,
                        instconfig=filter_B, detconfig=science_exp),
           ]
    OBs = ObservingBlockList(OBs)
    config = load_configuration()

    config['waittime'] = 0.005
    config['maxwait'] = 0.010
    config['weather_config'] = {}
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


    return OBs, config


if __name__ == '__main__':
    OBs, config = build_obs()
    obs = RollOffRoof(OBs=OBs, **config)
    obs.wake_up()
