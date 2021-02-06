class OB():
    def __init__(self, target='M1', acquire='blind',
                 instconfig='ic', detconfig='dc'):
        self.target = target
        self.acquire = acquire
        self.instconfig = instconfig
        self.detconfig = detconfig


OBs = [OB(target='M42', acquire='blind', instconfig=None, detconfig='300s'),
#        OB(target='M31', acquire='blind', instconfig=None, detconfig='300s'),
       OB(target='M78', acquire='blind', instconfig=None, detconfig='300s'),
       ]


class Scheduler():
    def __init__(self, OBs=OBs):
        self.OBs = OBs


    def select(self):
        if len(OBs) > 0:
            OB = self.OBs.pop(0)
        else:
            OB = None
        return OB

