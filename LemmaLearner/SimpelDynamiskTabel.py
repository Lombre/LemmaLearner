class DynamiskTabel:


    def __init__(self):
        self.__fordoblingsKonstant = 2
        self.__længde = 0
        self._indreListeLængde = 0
        self.__indreListe = []

    def tilføj(self, element):
        if self.__længde == 0:
            self.__indreListe = [element]            
            self.__indreListeLængde = 1
            self.__længde = 1
        else:
            #Tjek om der skal laves en fordobling, og indsæt.
            if self.__indreListeLængde == self.__længde:
                self.__indreListeLængde *= self.__fordoblingsKonstant
                nyIndreListe = self.nyTomListe(self.__indreListeLængde)
                self.__flytElementerTilNyListe(nyIndreListe)
                self.__indreListe = nyIndreListe
            self.__indreListe[self.__længde] = element
            self.__længde += 1


    def sletSidsteElement(self):
        kage = 1
    
    def __flytElementerTilNyListe(self, nyIndreListe):
        for i in range(self.__længde):
            nyIndreListe[i] = self.__indreListe[i]
    
    def nyTomListe(self, længde):
        return ['X'] * længde

    def getLength(self):
        return self.__længde

    def printIndhold(self):
        print(self.__indreListe)


def test():
    liste = DynamiskTabel()

    for i in range(1, 10):
        liste.tilføj(str(i))
        liste.printIndhold()