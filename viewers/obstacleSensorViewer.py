import matplotlib
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt


class ObstacleSensorViewer(object):
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

    def plotDistance(self, isLog=False, directory=None):
        allDistTot = [(a.flat[0]['data'][0]) for a in self.dataState]
        allDist = [x for x in allDistTot if x < 1000]
        print(f"all:{len(allDistTot)} - {len(allDist)}")
        plt.hist(allDist, density=False, bins=100, log=isLog)
        plt.ylabel('Num Values')
        plt.xlabel('obstacle distance (m)')
        if directory is not None:
            name = "obstacle_distance"
            if (isLog):
                name = name + "_log"
            plt.savefig(os.path.join(directory, name + ".png"))
        plt.show()

    def pieDist(self,directory=None):
        allDist = [(a.flat[0]['data'][0]) for a in self.dataState]
        allDefDist = [x for x in allDist if x < 1000]
        print(f"all:{len(allDist)} - {len(allDefDist)}")

        undefPerc = (100.0* (len(allDist) - len(allDefDist))) /len(allDist)
        defPerc = (100.0 * len(allDefDist)) / len(allDist)

        labels = [f"undef [{undefPerc:.3f}]", f"defined [{defPerc:.3f}]"]
        patches, texts = plt.pie([len(allDist) - len(allDefDist), len(allDefDist)], labels=labels,
                                 colors=["#A3C1FF", "#FF3288"])
        plt.legend(patches, labels, loc="best")
        plt.axis('equal')
        plt.tight_layout()

        if directory is not None:
            name = "obstactle_dist_defined_ratio"
            plt.savefig(os.path.join(directory, name + ".png"))

        plt.show()
    def plotRelVel(self, isLog=False, directory=None):
        allControls = [(a.flat[0]['data'][0], a.flat[0]['data'][1]) for a in self.dataState]
        allrelVel = [v for (d, v) in allControls if d < 1000]
        print(f"all:{len(allControls)} - {len(allrelVel)}")
        # labels =["undef","defined"]
        # patches, texts = plt.pie([len(allControls)-len(allrelVel),len(allrelVel)], labels=labels,
        #         colors=["#b0b0b0","#0000FF"])
        # plt.legend(patches, labels, loc="best")
        # plt.axis('equal')
        # plt.tight_layout()
        # plt.show()

        plt.hist(allrelVel, density=False, bins=100, log=isLog)
        plt.ylabel('Num Values')
        plt.xlabel('obstacle rel vel (m/s)')
        if directory is not None:
            name = "obstacle_rel_vel"
            if (isLog):
                name = name + "_log"
            plt.savefig(os.path.join(directory, name + ".png"))
        plt.show()

    def exportToExcel(self, excelFilename):
        allControls = [(a.flat[0]['timestamp'], a.flat[0]['data'][0], a.flat[0]['data'][1]) for a in self.dataState]
        elenco = []
        for itemControls in allControls:
            v = [itemControls[0], itemControls[1], itemControls[2]]
            elenco.append(v)
        df = pd.DataFrame(elenco, columns=['timestamp', 'distance', 'relative_vel'])
        df.to_excel(excelFilename, sheet_name='sheet1', index=False)


if __name__ == '__main__':
    directories = [
        # "G:/datasetagente/Town01_001/",
        # "G:/datasetagente/Town02_001/",
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
        # "G:/dataset/Town03_002/"
        "G:/AgentDataset/NoTraffic/Town01_001/",
        "G:/AgentDataset/NoTraffic/Town02_001/",
        "G:/AgentDataset/Traffic/Town01_001/",
        "G:/AgentDataset/Traffic/Town02_001/"
    ]
    for directory in directories:
        print(directory)
        obstacleSensor = ObstacleSensorViewer(directory + "obstacleSensor.npy")
        print(obstacleSensor.numSamples())

        obstacleSensor.exportToExcel(directory+"data_ObstacleSensor.xlsx")

        obstacleSensor.plotDistance(directory=directory)
        obstacleSensor.pieDist(directory=directory)
        obstacleSensor.plotRelVel(directory=directory)

    print ("TERMINATO")