import pathlib
import os

# Crea un folder all'interno di root folder della forma (NomeMappa_000)

def createFolderForMap(map, rootFolder):
    normalizedmap = map.lower()
    files = list(pathlib.Path(rootFolder).glob(normalizedmap+'_???'))
    if (len(files) == 0):
        theFolder = map+"_001"
    else:
        lastFile = files[-1].name;
        nextIdx =int(lastFile[-3:])+1
        theFolder = map+"_"+"{:03d}".format(nextIdx)

    newDir = os.path.join(rootFolder,theFolder)
    try:
        os.makedirs(newDir)
    except:
        print("Directory already exists")

    return newDir
