##-------------------------------------------------------------------------
## Scheduler
##-------------------------------------------------------------------------
class Scheduler():
    def __init__(self, OBs=[]):
        self.OBs = OBs


    def select(self):
        if len(self.OBs) > 0:
            return self.OBs.pop(0)
        else:
            return None
