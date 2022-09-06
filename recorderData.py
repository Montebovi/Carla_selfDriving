class RecorderData:
    def __init__(self, baseDirectory, numFrameToSkip=5, enabled=True):
        self._enabled = enabled
        self.baseDirectory = baseDirectory
        self.recordableObjects = []
        self._numFrameToSkip = numFrameToSkip

    def EnableRecording(self, enabled):
        self._enabled = enabled

    def subscribeRecordableObject(self, obj):
        obj.initRecording(self.baseDirectory)
        self.recordableObjects.append(obj)

    def recordFrame(self, timestamp):
        if self._numFrameToSkip > 0:
            self._numFrameToSkip -= 1
        elif (self._enabled):
            for obj in self.recordableObjects:
                obj.saveDataFrame(timestamp)

    def dispose(self):
        for obj in self.recordableObjects:
            obj.endRecording()
        self.recordableObjects = None
