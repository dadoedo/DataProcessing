import threading as th
import time as t


class DataController(th.Thread):
    def __init__(self, threadID, recieverObj, senderObj, deviceName):
        th.Thread.__init__(self)
        self.threadID = threadID
        self.done = False
        self.recieverObj = recieverObj
        self.senderObj = senderObj
        self.sleep_time = 0.3
        self.busy = False
        self.__cmd = None
        self.__newCmd = False
        self.fakeRspTime = 0
        self.paused = True
        self.deviceName = deviceName

    def stop(self):
        self.done = True

    def run(self):
        while not self.done:
            if self.__newCmd:
                self.__newCmd = False
                self.__procCmd()
            if self.busy:
                self.busy = False
            t.sleep(self.sleep_time)

    def getData(self):
        return self.recieverObj.getData()

    def send_cmd(self, cmd):
        if not self.busy:
            self.busy = True
            self.__newCmd = True
            self.__cmd = cmd
            return True
        else:
            raise UserWarning("Unable to handle command")

    def __procCmd(self):
        self.busy = True
        if self.__cmd == 'R':  # Pause
            if self.paused:
                self.paused = False
            else:
                self.paused = True
            self.recieverObj.changePausedState()

        if self.__cmd == 'S':
            self.senderObj.changePausedState()

        if self.__cmd == 'X':
            if not self.senderObj.isPausedState():
                self.senderObj.changePausedState()
            if not self.recieverObj.isPausedState():
                self.recieverObj.changePausedState()
            self.recieverObj.resetData()

    def deleteSenderProducer(self):
        self.recieverObj.__del__()
        self.senderObj.__del__()
