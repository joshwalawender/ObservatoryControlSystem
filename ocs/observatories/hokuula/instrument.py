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
        self.focuser1 = Focuser(logger=logger, IP=IP, port=port, device_number=0)
        self.focuser2 = Focuser(logger=logger, IP=IP, port=port, device_number=1)


    def configure(self, ic):
        '''Set hardware in a state described by the input InstrumentConfig
        '''
        if ic.filter is not None:
            self.filterwheel.set_position(ic.filter)
        if ic.focuspos1 is not None:
            self.focuser1.move(ic.focuspos1)
        if ic.focuspos2 is not None:
            self.focuser2.move(ic.focuspos2)


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
        # Focuser 1
        h['FOC1NAME'] = (self.focuser1.properties['name'],
                        'Focuser Name')
        h['FOC1DVRV'] = (self.focuser1.properties['driverversion'],
                         'Focuser Driver Version')
        h['FOC1POS'] = (self.focuser1.position(),
                         'Focuser Position')
        h['FOC1TCMP'] = (self.focuser1.tempcomp(),
                         'Focuser Temperature Compensation')
        h['FOC1TEMP'] = (self.focuser1.temperature(),
                        'Focuser Temperature')
        # Focuser 2
        h['FOC2NAME'] = (self.focuser2.properties['name'],
                        'Focuser Name')
        h['FOC2DVRV'] = (self.focuser2.properties['driverversion'],
                         'Focuser Driver Version')
        h['FOC2POS'] = (self.focuser2.position(),
                         'Focuser Position')
        h['FOC2TCMP'] = (self.focuser2.tempcomp(),
                         'Focuser Temperature Compensation')
        h['FOC2TEMP'] = (self.focuser2.temperature(),
                        'Focuser Temperature')
        return h
