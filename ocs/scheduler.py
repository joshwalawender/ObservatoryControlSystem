

class Scheduler():
    def __init__(self, OBs=['OB1', 'OB2']):
        self.OBs = OBs


    def select(self):
        return self.OBs.pop(0)

