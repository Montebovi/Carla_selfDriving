import matplotlib
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt


class VehicleStateViewer(object):
    def __init__(self, filenameState):
        self._filenameState = filenameState

        self.dataState  = self._readFile(self._filenameState)


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
            v = [itemControls[0],itemControls[1]]
            elenco.append(v)
        df = pd.DataFrame(elenco, columns=['timestamp', 'speed (m/s)'])
        df.to_excel(excelFilename, sheet_name='sheet1', index=False)

if __name__ == '__main__':
    directory = "H:/_buttare/Town03_012/"
    vehicleState = VehicleStateViewer(directory + "vehicleState.npy")
    print(vehicleState.numSamples())

    vehicleState.exportToExcel("data_vehicle_state.xlsx")