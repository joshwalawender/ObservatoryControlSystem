from astropy.io import fits
from astropy import units as u


##-------------------------------------------------------------------------
## ODL InstrumentConfig
##-------------------------------------------------------------------------
from odl.instrument_config import InstrumentConfig as GenericInstrumentConfig

class InstrumentConfig(GenericInstrumentConfig):
    '''InstrumentConfig object for a setup comprised of:
    - ZWO Filter Wheel
    - Optec Focuser with 2 focusers attached
    '''
    def __init__(self, filter='L', focuspos1=None, focuspos2=None):
        super().__init__(name=f'{filter} Filter')
        filter_wavelengths = {'L': 550*u.nm, # 396-705
                              'R': 530*u.nm, # 592-690
                              'G': 530*u.nm, # 492-572
                              'B': 450*u.nm, # 397-506
                              'Ha': 656.3*u.nm,
                              'Empty': 600*u.nm, 
                              'Grating': 0.5*u.micron,
                              'Dark': 0.5*u.micron}
        if filter in filter_wavelengths.keys():
            self.obswl = filter_wavelengths[filter]
        self.filter = filter
        self.focuspos1 = focuspos1
        self.focuspos2 = focuspos2


    def to_header(self):
        h = fits.Header()
        h['ICNAME'] = (self.name, 'Instrument Config Name')
        h['ICPKG'] = (self.package, 'Instrument Config Package Name')
        h['ICINST'] = (self.instrument, 'Instrument Config Instrument Name')
        h['ICFILT'] = (self.filter, 'Instrument Config Filter')
        h['ICFOC1'] = (self.focuspos1, 'Instrument Config Focus Position 1')
        h['ICFOC2'] = (self.focuspos2, 'Instrument Config Focus Position 2')
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
        if ic.focuspos1 is not None:
            self.focuser.move(ic.focuspos1)
        if ic.focuspos2 is not None:
            self.focuser.move(ic.focuspos2)


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
