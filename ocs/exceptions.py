class HardwareFailure(Exception): pass
class RoofFailure(HardwareFailure): pass
class TelescopeFailure(HardwareFailure): pass
class InstrumentFailure(HardwareFailure): pass
class DetectorFailure(HardwareFailure): pass
class FocuserFailure(HardwareFailure): pass

class SoftwareFailure(Exception): pass
class SchedulingFailure(SoftwareFailure): pass
class AcquisitionFailure(SoftwareFailure): pass
class FocusRunFailure(SoftwareFailure): pass
