import matplotlib
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt


class VehicleStateViewer(object):
    def __init__(self, filenameState):
        self._filenameState = filenameState

        self.dataState = self._readFile(self._filenameState)

    def _readFile(self, filename):
        file = open(filename, "br")
        data = []
        while True:
            try:
                singleData = np.load(file, allow_pickle=True)
                data.append(singleData)
            except:
                break
        file.close()
        return data

    def numSamples(self):
        return len(self.dataState)

    def exportToExcel(self, excelFilename):
        allControls = [(a.flat[0]['timestamp'], a.flat[0]['speed_ms']) for a in self.dataState]
        elenco = []
        for itemControls in allControls:
            v = [itemControls[0], itemControls[1]]
            elenco.append(v)
        df = pd.DataFrame(elenco, columns=['timestamp', 'speed (m/s)'])
        df.to_excel(excelFilename, sheet_name='sheet1', index=False)

    def plotSpeed(self, isLog=False, directory=None):
        allSpeed = [(a.flat[0]['speed_ms']) for a in self.dataState]
        plt.hist(allSpeed, density=False, bins=30, color="#FF70FF", log=isLog)
        plt.ylabel('Num Values')
        plt.xlabel('Speed (m/s)')
        if (directory is not None):
            name = "speed"
            if (isLog):
                name = name + "_log"
            plt.savefig(os.path.join(directory, name + ".png"))
        plt.show()

    def plotSpeedOnTime(self, directory=None):
        start = self.dataState[0].flat[0]['timestamp']
        X = [(a.flat[0]['timestamp'] - start) / 1000 for a in self.dataState]
        Y = [(a.flat[0]['speed_ms']) for a in self.dataState]

        mean = sum(Y) / len(Y)
        print(mean)
        YM = [mean for a in self.dataState]

        fig, ax = plt.subplots()
        ax.plot(X, Y, label="speed (m/s)", alpha=0.6)
        plt.xlabel('Time (sec)')
        plt.ylabel('speed (m/s)')

        ax.plot(X, YM, label="mean speed (m/s)", alpha=0.6,  linestyle=":")
        plt.xlabel('Time (sec)')
        plt.ylabel('speed (m/s)')

        ax.set_title("Data in time")

        ax.legend(loc="lower left", ncol=2)
        pos = ax.get_position()
        ax.set_position([pos.x0, pos.y0+pos.height*0.15, pos.width, pos.height*0.85])
        ax.legend(loc='lower left', bbox_to_anchor=(0, -0.28),ncol=2)

        #ax.set_position([pos.x0, pos.y0, pos.width*0.80, pos.height])
        #ax.legend(loc='center right', bbox_to_anchor=(1.40, 1),ncol=1)

        if (directory is not None):
            name = "speed_on_time"
            fig.savefig(os.path.join(directory, name + ".png"))

        fig.show()


if __name__ == '__main__':
    directories = [
        # "G:/dataset/Town01_001/",
        # "G:/dataset/Town01_002/",
        # "G:/dataset/Town01_003/",
        # "G:/dataset/Town01_004/",
        # "G:/dataset/Town01_005/",
        # "G:/dataset/Town01_006/",
        # "G:/dataset/Town01_007/",
        # "G:/dataset/Town02_001/",
        # "G:/dataset/Town02_004/",
        # "G:/dataset/Town03_001/",
        # "G:/dataset/Town03_002/",
        # "G:/datasetagente/Town01_001/",
        # "G:/datasetagente/Town02_001/"
        "G:/AgentDataset/NoTraffic/Town01_001/",
        "G:/AgentDataset/NoTraffic/Town02_001/",
        "G:/AgentDataset/Traffic/Town01_001/",
        "G:/AgentDataset/Traffic/Town02_001/"
    ]

    for directory in directories:
        vehicleState = VehicleStateViewer(directory + "vehicleState.npy")
        print(directory)
        print(vehicleState.numSamples())

        vehicleState.exportToExcel(directory + "data_vehicle_state.xlsx")
        vehicleState.plotSpeed(isLog=False, directory=directory)
        vehicleState.plotSpeedOnTime(directory=directory)

    print("TERMINATO")
