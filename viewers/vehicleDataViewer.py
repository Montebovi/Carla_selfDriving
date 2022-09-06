import matplotlib
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt



class VehicleDataViewer(object):
    def __init__(self, filenameControls):
        self.filenameControls = filenameControls

        self.dataControls  =self._readFile(self.filenameControls)


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

    def plotSteer(self):
        allSteer = [(a.flat[0]['data'][0]) for a in dataVehicle.dataControls]
        print(len(allSteer))
        plt.hist(allSteer, density=False, bins=30)
        plt.ylabel('Value')
        plt.xlabel('Steer')
        plt.show()

    def exportToExcel(self, excelFilename):
        allControls = [(a.flat[0]['timestamp'], a.flat[0]['data']) for a in dataVehicle.dataControls]
        elenco = []
        for itemControls in allControls:
            v = [itemControls[0],itemControls[1][0],itemControls[1][1],itemControls[1][2]]
            elenco.append(v)
        df = pd.DataFrame(elenco, columns=['timestamp', 'steer','throttle','brake'])
        df.to_excel(excelFilename, sheet_name='sheet1', index=False)



if __name__ == '__main__':
    directory = "H:/_buttare/Town01_001/"
    dataVehicle = VehicleDataViewer(directory + "vehicleData.npy")
    print(dataVehicle.numSamplesControls())
    dataVehicle.exportToExcel("data_vehicle_ctrls.xlsx")
    dataVehicle.plotSteer()