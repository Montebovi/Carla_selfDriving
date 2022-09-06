

class TownChooser:
    def __init__(self):
        self.maps = ['Town01', 'Town02', 'Town03', 'Town04', 'Town05', 'Town06', 'Town07']

    def selectTown(self):
        print('Elenco delle mappe disponibili: ')

        idxMap = 0

        for map in self.maps:
            idxMap += 1
            print(f'\t({idxMap}) {map}')
        try:
            # choosenMapIdx = 1
            choosenMapIdx = int(input('Digitare il numero della mappa: '))
            choosenMap = self.maps[choosenMapIdx - 1]
        except:
            return None

        return choosenMap



