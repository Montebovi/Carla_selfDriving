import matplotlib
import random
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import colors


class VehicleDataViewer(object):
    def __init__(self, filenameControls):
        self.filenameControls = filenameControls

        self.dataControls = self._readFile(self.filenameControls)

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

    def numSamplesControls(self):
        return len(self.dataControls)

    def reduceZerosSteer(self, percZeros):
        y_vehicleData = [a.flat[0]['data'] for a in dataVehicle.dataControls]

        #MAXZEROSTEER = 0.003
        MAXZEROSTEER = 0.01
        listIdxZeros = []
        total = len(y_vehicleData)
        listSteer = [s[0] for s in y_vehicleData]
        listBrake = [s[2] for s in y_vehicleData]
        numZeros = len(
            [s for s in range(0, len(listSteer)) if (abs(listSteer[s]) <= MAXZEROSTEER and listBrake[s] < 0.2)])
        print(numZeros)
        # numZeros = len([s for s in listSteer if abs(s) <= MAXZEROSTEER])
        attualPercentOfZeros = (1.0 * numZeros) / total
        if attualPercentOfZeros <= percZeros:
            return y_vehicleData

        toRemove = int((1.0 * numZeros - percZeros * total) / (1 - percZeros))

        for idx in range(0, total):
            steer = y_vehicleData[idx][0]
            brake = y_vehicleData[idx][2]
            if abs(steer) <= MAXZEROSTEER and brake < 0.2:
                listIdxZeros.append(idx)
        random.shuffle(listIdxZeros)
        listIdxZeros = listIdxZeros[0:toRemove]

        listIdxZeros.sort(reverse=True)
        for idx in range(0, toRemove):
            idxToRemove = listIdxZeros[idx]
            y_vehicleData = np.delete(y_vehicleData, idxToRemove, axis=0)

        return y_vehicleData

    def plotSteer(self, customData=None, isLog=False, directory=None):
        if customData is not None:
            allSteer = [(a[0]) for a in customData]
        else:
            allSteer = [(a.flat[0]['data'][0]) for a in dataVehicle.dataControls]
        print(len(allSteer))
        plt.hist(allSteer, density=False, bins=100, log=isLog)
        plt.ylabel('Num Values')
        if customData is not None:
            plt.xlabel('Steer (reduced)')
            name = "steer_reduced"
        else:
            name = "steer"
            plt.xlabel('Steer')
        if (directory is not None):
            if (isLog):
                name = name + "_log"
            plt.savefig(os.path.join(directory, name + ".png"))
        plt.show()

    def plotThrottle(self, customData=None, isLog=False, directory=None):
        if customData is not None:
            allSteer = [(a[1]) for a in customData]
        else:
            allSteer = [(a.flat[0]['data'][1]) for a in dataVehicle.dataControls]
        print(len(allSteer))
        plt.hist(allSteer, density=False, bins=30, color="orange", log=isLog)
        plt.ylabel('Num Values')
        if customData is not None:
            name = "throttle_reduced"
            plt.xlabel('Throttle (reduced)')
        else:
            name = "throttle"
            plt.xlabel('Throttle')
        if (directory is not None):
            if (isLog):
                name = name + "_log"
            plt.savefig(os.path.join(directory, name + ".png"))
        plt.show()

    def plotBrake(self, customData=None, isLog=False, directory=None):
        if customData is not None:
            allBrake = [(a[2]) for a in customData]
        else:
            allBrake = [(a.flat[0]['data'][2]) for a in dataVehicle.dataControls]
        # print(len(allBrake))
        plt.hist(allBrake, density=False, bins=30, color="green", log=isLog)
        plt.ylabel('Num Values')
        if customData is not None:
            name = "brake_reduced"
            plt.xlabel('Brake (reduced)')
        else:
            name = "brake"
            plt.xlabel('Brake')
        if (directory is not None):
            if (isLog):
                name = name + "_log"
            plt.savefig(os.path.join(directory, name + ".png"))
        plt.show()

    def plotBrakeThrottle(self, isLog=False, directory=None):
        colors = ['orange', 'green']
        allThrottleBrake = [[a.flat[0]['data'][1], a.flat[0]['data'][2]] for a in dataVehicle.dataControls]
        # print(len(allThrottleBrake))
        plt.grid(axis='y', color='gray', linestyle=':')
        plt.hist(np.array(allThrottleBrake), histtype='bar', density=False, bins=20, color=colors,
                 label=["throttle", "brake"], log=isLog)
        plt.ylabel('Num Values')
        # plt.xlabel('')
        plt.legend(prop={'size': 10}, ncol=2)
        if (directory is not None):
            name = "brake_and_throttle"
            if (isLog):
                name = name + "_log"
            plt.savefig(os.path.join(directory, name + ".png"))

        plt.show()

    def histo2d_brake_throttle(self, directory=None):
        allThrottle = [(a.flat[0]['data'][1]) for a in dataVehicle.dataControls]
        allBrake = [(a.flat[0]['data'][2]) for a in dataVehicle.dataControls]

        heatmap, xedges, yedges = np.histogram2d(allThrottle, allBrake, bins=20)
        extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
        # plt.clf()
        # cmap = colors.ListedColormap(['white', 'red'])

        cmap = colors.LinearSegmentedColormap.from_list('custom red', ['#ffffff', '#E00000'], N=256)
        plt.imshow(heatmap.T, cmap=cmap, extent=extent, origin='lower')
        plt.xlabel('Throttle')
        plt.ylabel('Brake')

        plt.subplots_adjust(bottom=0.1, right=0.8, top=0.9)
        cax = plt.axes([0.85, 0.1, 0.075, 0.8])
        plt.colorbar(cax=cax)

        if (directory is not None):
            name = "brake_vs_throttle"
            plt.savefig(os.path.join(directory, name + ".png"))

        plt.show()

    def plotDataOnTime(self, directory=None):
        start = dataVehicle.dataControls[0].flat[0]['timestamp']
        X = [(a.flat[0]['timestamp'] - start) / 1000 for a in dataVehicle.dataControls]
        Y = [(a.flat[0]['data'][0]) for a in dataVehicle.dataControls]
        Y_throttle = [(a.flat[0]['data'][1]) for a in dataVehicle.dataControls]
        Y_brake = [(a.flat[0]['data'][2]) for a in dataVehicle.dataControls]
        fig, ax = plt.subplots()
        ax.plot(X, Y, label="steer", alpha=0.6)
        plt.xlabel('Time (sec)')
        plt.ylabel('values')

        ax.set_title("Data in time")
        ax.plot(X, Y_throttle, label="throttle", linestyle=":", alpha=0.8)
        ax.plot(X, Y_brake, label="brake", linestyle=":", alpha=0.8)

        ax.legend(loc="lower left", ncol=3)
        if directory is not None:
            fig.savefig(os.path.join(directory, "dati_su_tempo.png"))
        fig.show()

    def exportToExcel(self, excelFilename):
        start = dataVehicle.dataControls[0]
        allControls = [(a.flat[0]['timestamp'], a.flat[0]['data']) for a in dataVehicle.dataControls]
        elenco = []
        for itemControls in allControls:
            v = [itemControls[0], itemControls[1][0], itemControls[1][1], itemControls[1][2]]
            elenco.append(v)
        df = pd.DataFrame(elenco, columns=['timestamp', 'steer', 'throttle', 'brake'])
        df.to_excel(excelFilename, sheet_name='sheet1', index=False)


if __name__ == '__main__':
    # directory = "H:/_buttare/Town01_001/"
    directories = [
        # "G:/AgentDataset/NoTraffic/Town01_001/",
        # "G:/AgentDataset/NoTraffic/Town02_001/",
        # "G:/AgentDataset/Traffic/Town01_001/",
        # "G:/AgentDataset/Traffic/Town02_001/"
        "G:/dataset/Town01_001_soglia_steer_diversa/",
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
    ]
    for directory in directories:
        # directory = "G:/dataset/Town01_005/"
        dataVehicle = VehicleDataViewer(directory + "vehicleData.npy")

        FPS = 20
        numSamples = dataVehicle.numSamplesControls()
        duration = (1.0 * numSamples) / FPS
        print(f"Num of samples: {numSamples} - sec: {duration:.1f}")

        #datiRidotti = dataVehicle.reduceZerosSteer(0.25)
        datiRidotti = dataVehicle.reduceZerosSteer(0.10)
        print(f"Num of samples (reduced): {len(datiRidotti)}")

        with open(directory + 'readme.txt', 'w') as f:
            f.write(f"Num of samples: {numSamples} - FPS: {FPS} - sec: {duration:.1f}")

        dataVehicle.exportToExcel(directory + "data_vehicle_ctrls.xlsx")

        dataVehicle.plotSteer(isLog=False, directory=directory)
        dataVehicle.plotSteer(isLog=True, directory=directory)

        dataVehicle.plotSteer(customData=datiRidotti, isLog=False, directory=directory)  # ridotto
        dataVehicle.plotSteer(customData=datiRidotti, isLog=True, directory=directory)  # ridotto

        dataVehicle.plotDataOnTime(directory=directory)

        dataVehicle.plotBrake(isLog=True, directory=directory)
        dataVehicle.plotBrake(isLog=False, directory=directory)
        dataVehicle.plotBrake(customData=datiRidotti, isLog=True, directory=directory)
        dataVehicle.plotBrake(customData=datiRidotti, isLog=False, directory=directory)

        dataVehicle.plotThrottle(isLog=False, directory=directory)
        dataVehicle.plotThrottle(customData=datiRidotti, isLog=False, directory=directory)

        dataVehicle.plotBrakeThrottle(isLog=True, directory=directory)
        dataVehicle.plotBrakeThrottle(isLog=False, directory=directory)
        dataVehicle.histo2d_brake_throttle(directory=directory)

    print("TERMINATO")
