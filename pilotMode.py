class PilotMode:
    def __init__(self, vehicleActor, gamePadEnabled, wheelEnabled, agentEnabled, startAutopilot=True, isRecording = False):
        self._vehicleActor = vehicleActor
        self._isRecording = isRecording

        self.AUTO_PILOT = 0
        self.MANUAL_KBD_PILOT = 1
        self.MANUAL_GAMEPAD_PILOT = 2
        self.MANUAL_WHEEL_PILOT = 3
        self.AGENT_PILOT = 4

        self._modes = [self.AUTO_PILOT, self.MANUAL_KBD_PILOT]
        if gamePadEnabled:
            self._modes.append(self.MANUAL_GAMEPAD_PILOT)
        if wheelEnabled:
            self._modes.append(self.MANUAL_WHEEL_PILOT)
        if agentEnabled:
            self._modes.append(self.AGENT_PILOT)

        if startAutopilot:
            self._idxMode = 0
        else:
            self._idxMode = 1

    def get_mode(self):
        return self._modes[self._idxMode]

    def set_mode(self, mode):
        self._idxMode = self._modes.index(mode)
        self._vehicleActor.set_autopilot(self.get_mode() == self.AUTO_PILOT)

    def toggleRecording(self):
        self._isRecording = not self._isRecording

    def IsRecording(self):
        return self._isRecording

    def Next(self):
        self._idxMode = (self._idxMode + 1) % len(self._modes)
        self._vehicleActor.set_autopilot(self.get_mode() == self.AUTO_PILOT)
        if self.get_mode() != self.AUTO_PILOT:
            data = self._vehicleActor.get_control()
            data.steer = 0
            data.brake = 0
            data.throttle = 0
            self._vehicleActor.apply_control(data)

    def SetAutoPilotMode(self):
        self._idxMode = 0
        self._vehicleActor.set_autopilot(True)

    def IsAgentMode(self):
        return self.get_mode() == self.AGENT_PILOT

    def IsAutoPilot(self):
        return self.get_mode() == self.AUTO_PILOT

    def IsManualKbdMode(self):
        return self.get_mode() == self.MANUAL_KBD_PILOT

    def GetModeAsString(self):
        mode_names = ["AUTO","KBD","GAMEPAD","WHEEL G29","AGENT"]
        return mode_names[self._modes[self._idxMode]]
