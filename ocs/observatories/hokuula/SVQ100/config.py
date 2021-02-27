from astropy.io import fits

##-------------------------------------------------------------------------
## ODL InstrumentConfig
##-------------------------------------------------------------------------
from odl.instrument_config import InstrumentConfig

class SVQ100Config(InstrumentConfig):
    '''InstrumentConfig object for a setup comprised of:
    - ZWO Filter Wheel
    - Optec Focuser
    '''
    def __init__(self, filter='L', focuspos=None):
        super().__init__(name=f'{filter} Filter')
        self.filter = filter
        self.focuspos = focuspos


    def to_header(self):
        h = fits.Header()
        h['ICNAME'] = (self.name, 'Instrument Config Name')
        h['ICPKG'] = (self.package, 'Instrument Config Package Name')
        h['ICINST'] = (self.instrument, 'Instrument Config Instrument Name')
        h['ICFILT'] = (self.filter, 'Instrument Config Filter')
        h['ICFOCPOS'] = (self.focuspos, 'Instrument Config Focus Position')
        return h


##-------------------------------------------------------------------------
## Instrument Controller
##-------------------------------------------------------------------------
from pypaca import Focuser, FilterWheel

class InstrumentController():
    '''
    
    Devices
    -------
    filterwheel : AlpacaDevice
    focuser : AlpacaDevice
    '''
    def __init__(self, logger=None, IP='localhost', port=11111):
        self.logger = logger
        self.filterwheel = FilterWheel(logger=logger, IP=IP, port=port)
        self.focuser = Focuser(logger=logger, IP=IP, port=port)


    def configure(self, ic):
        '''Set hardware in a state described by the input InstrumentConfig
        '''
        if ic.filter is not None:
            self.filterwheel.set_position(ic.filter)
        if ic.focuspos is not None:
            self.focuser.move(ic.focuspos)


    def collect_header_metadata(self):
        h = fits.Header()
        # FilterWheel
        fpos, fname = self.filterwheel.position()
        h['FILTER'] = (fname, 'Filter')
        h['FILTERNO'] = (fpos, 'Filter Wheel Position')
        h['FWNAME'] = (self.filterwheel.properties['name'],
                       'Filter Wheel Name')
        h['FWDRVRSN'] = (self.filterwheel.properties['driverversion'],
                         'Filter Wheel Driver Version')
        # Focus
        h['FOCNAME'] = (self.focuser.properties['name'],
                        'Focuser Name')
        h['FOCDVRSN'] = (self.focuser.properties['driverversion'],
                         'Focuser Driver Version')
        h['FOCUSPOS'] = (self.focuser.position(),
                         'Focuser Position')
        h['FOCTCOMP'] = (self.focuser.tempcomp(),
                         'Focuser Temperature Compensation')
        h['FOCTEMP'] = (self.focuser.temperature(),
                        'Focuser Temperature')
        return h
