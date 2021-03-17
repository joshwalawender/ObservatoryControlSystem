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
    def __init__(self, filter='L', focusposSVQ=None, focusposSVX=None):
        super().__init__(instrument='SVQ100_SVX152')
        self.name = f'ZWO {filter} Filter'
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
        self.focusposSVQ = focusposSVQ
        self.focusposSVX = focusposSVX
        if focusposSVQ is not None:
            self.name += ' (focuspos1={focusposSVQ:.0f})'
        if focusposSVX is not None:
            self.name += ' (focuspos2={focusposSVX:.0f})'


    def to_dict(self):
        output = super().to_dict()
        output['filter'] = self.filter
        output['focusposSVQ'] = self.focusposSVQ
        output['focusposSVX'] = self.focusposSVX
        return output


    def to_header(self):
        h = fits.Header()
        h['ICNAME'] = (self.name, 'Instrument Config Name')
        h['ICINST'] = (self.instrument, 'Instrument Config Instrument Name')
        h['ICFILT'] = (self.filter, 'Instrument Config Filter')
        h['ICFOCSVQ'] = (self.focusposSVQ, 'Instrument Config Focus Position SVQ')
        h['ICFOCSVX'] = (self.focusposSVX, 'Instrument Config Focus Position SVX')
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
        self.focuserSVQ = Focuser(logger=logger, IP=IP, port=port, device_number=0)
        self.focuserSVX = Focuser(logger=logger, IP=IP, port=port, device_number=1)


    def configure(self, ic):
        '''Set hardware in a state described by the input InstrumentConfig
        '''
        if ic.filter is not None:
            self.filterwheel.set_position(ic.filter)
        if ic.focusposSVQ is not None:
            self.focuserSVQ.move(ic.focusposSVQ)
        if ic.focusposSVX is not None:
            self.focuserSVX.move(ic.focusposSVX)


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
        h['FOC1NAME'] = (self.focuserSVQ.properties['name'],
                        'Focuser Name')
        h['FOC1DVRV'] = (self.focuserSVQ.properties['driverversion'],
                         'Focuser Driver Version')
        h['FOC1POS'] = (self.focuserSVQ.position(),
                         'Focuser Position')
        h['FOC1TCMP'] = (self.focuserSVQ.tempcomp(),
                         'Focuser Temperature Compensation')
        h['FOC1TEMP'] = (self.focuserSVQ.temperature(),
                        'Focuser Temperature')
        # Focuser 2
        h['FOC2NAME'] = (self.focuserSVX.properties['name'],
                        'Focuser Name')
        h['FOC2DVRV'] = (self.focuserSVX.properties['driverversion'],
                         'Focuser Driver Version')
        h['FOC2POS'] = (self.focuserSVX.position(),
                         'Focuser Position')
        h['FOC2TCMP'] = (self.focuserSVX.tempcomp(),
                         'Focuser Temperature Compensation')
        h['FOC2TEMP'] = (self.focuserSVX.temperature(),
                        'Focuser Temperature')
        return h
