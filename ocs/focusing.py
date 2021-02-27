from odl.block import FocusBlock


##-------------------------------------------------------------------------
## Focus Routines
##-------------------------------------------------------------------------
class FocusFitParabola(FocusBlock):
    '''An observing block describing a focus observation which takes several
    images and measures the FWHM in each, then fits a parabola to find the best
    focus position.
    '''
    def __init__(self, target=None, pattern=None, instconfig=None,
                 detconfig=None, align=None, blocktype='FocusFitParabola',
                 n_focus_positions=7, focus_step=50, images_per_position=1,
                 refocus_if_near_edge=True,
                 ):
        super().__init__(target=target, pattern=pattern, instconfig=instconfig,
                         detconfig=detconfig, align=align, blocktype=blocktype)
        self.n_focus_positions = n_focus_positions
        self.focus_step = focus_step
        self.images_per_position = images_per_position
        self.refocus_if_near_edge = refocus_if_near_edge


class FocusMaxRun(FocusBlock):
    '''Trigger a FocusMax run.
    '''
    def __init__(self, target=None, pattern=None, instconfig=None,
                 detconfig=None, align=None, blocktype='FocusMaxRun',
                 ):
        super().__init__(target=target, pattern=pattern, instconfig=instconfig,
                         detconfig=detconfig, align=align, blocktype=blocktype)
