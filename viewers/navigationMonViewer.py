import matplotlib
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt


class NavigationMonViewer(object):
    def __init__(self, filenameData):
        self._filenameData = filenameData

        self._dataNav  = self._readFile(self._filenameData)


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
        return len(self._dataNav)

    def exportToExcel(self, excelFilename):
        allControls = [(a.flat[0]['timestamp'], a.flat[0]['dir'][0], a.flat[0]['dir'][1], a.flat[0]['dir'][2],a.flat[0]['dirDist']) for a in self._dataNav]
        elenco = []
        for itemControls in allControls:
            v = [itemControls[0],itemControls[1],itemControls[2],itemControls[3],itemControls[4]]
            elenco.append(v)
        df = pd.DataFrame(elenco, columns=['timestamp', 'sx','diritto',"dx","dist-dir"])
        df.to_excel(excelFilename, sheet_name='sheet1', index=False)


if __name__ == '__main__':
    directory = "H:/_buttare/Town03_012/"
    navData  = NavigationMonViewer(directory + "navigationData.npy")
    print(navData.numSamples())

    navData.exportToExcel("data_navigator.xlsx")