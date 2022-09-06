import os
class RecordableObject:
    def __init__(self, name, createProperDir):
        self.createProperDir = createProperDir
        self._NAME = name
        self._properDir = None
        pass

    def initRecording(self, baseDir):
        if self.createProperDir:
            self._properDir = os.path.join(baseDir, self._NAME)
            if not os.path.isdir(self._properDir):
                os.makedirs(self._properDir)
        else:
            self._properDir = baseDir
        pass

    def saveDataFrame(self,timestamp):
        pass

    def endRecording(self):
        pass

