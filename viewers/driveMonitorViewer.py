import matplotlib
import numpy as np
import math
import os
import pandas as pd
import matplotlib.pyplot as plt


class DriveMonitorViewer:
    def __init__(self, filename):
        self._filename = filename
        self._data = self._readFile(self._filename)

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
        return len(self._data)

    def save(self, filename):
        v = driveMonitorViewer._data[0].flat[0]
        lines = []

        durata = v['duration'] / 60.0
        sec = int(v['duration']) % 60
        lines.append("VEHICLE DYNAMICS --------------------------------------------------")
        lines.append(f"Total driving time:  {math.trunc(durata)} min e {sec} sec")
        lines.append(f"Meters traveled:     {v['meters_traveled']:.1f} mt  -  {(v['meters_traveled'] / 1000):.3f} km")
        lines.append(f"Max speed:           {v['max_speed']:.3f} m/s  -  {(v['max_speed'] * 3.6):.1f} km/h")
        lines.append(f"Mean speed:          {v['mean_speed']:.3f} m/s  -  {(v['mean_speed'] * 3.6):.1f} km/h")
        lines.append(f"Lane invasions:      {len(v['lane_invasions'])}")
        lines.append(f"Repositioning count: {v['repos_count']}")

        lines.append("")
        lines.append("NAVIGATION --------------------------------------------------------")
        lines.append(f"Reached targets:            {v['reached_targets']}")
        lines.append(f"Wrong directions count:     {v['wrong_direction_count']}")
        lines.append(f"Total suggested directions: {v['totalJoinPoints']}")

        lines.append("")
        lines.append("OBSTACLES ---------------------------------------------------------")
        lines.append(f"Number of obstacles:  {len(v['obstacles'])}")
        obstacle_vehicle = [a for a in v['obstacles'] if a[2].startswith('vehicle')]
        lines.append(f"\tNumber of obstacles (vehicle): {len(obstacle_vehicle)}")
        obstacle_static = [a for a in v['obstacles'] if a[2].startswith('static')]
        lines.append(f"\tNumber of obstacles (static): {len(obstacle_static)}")
        obstacle_traffic = [a for a in v['obstacles'] if a[2].startswith('traffic')]
        lines.append(f"\tNumber of obstacles (traffic): {len(obstacle_traffic)}")

        lines.append(f"Number of collisions: {len(v['collisions'])}")
        if (len(v['collisions']) > 0):
            lines.append(f"Collisions:")
            k = 0
            for c in v['collisions']:
                k = k + 1
                lines.append(f"\t{k}) {c[3]}")


        for s in lines:
            print(s)

        with open(filename, 'w') as f:
            for s in lines:
                f.write(s+"\n")
        pass


if __name__ == '__main__':
    directories = [
        # "G:/AgentDataset/Town01_001/",
        # "G:/AgentDataset/Town02_001/"
        "G:/AgentDataset/NoTraffic/Town01_001/",
        "G:/AgentDataset/NoTraffic/Town02_001/",
        "G:/AgentDataset/Traffic/Town01_001/",
        "G:/AgentDataset/Traffic/Town02_001/"
    ]

    for directory in directories:
        print("****************************************************************************")
        driveMonitorViewer = DriveMonitorViewer(directory + "driveMonitor.npy")
        print(directory)
        # print(driveMonitorViewer.numSamples())
        # print(driveMonitorViewer._data[0].flat[0].keys())
        driveMonitorViewer.save(directory + "driveMonitor.txt")
        print("")
