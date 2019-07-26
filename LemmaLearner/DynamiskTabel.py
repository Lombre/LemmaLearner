
class DynamiskTabel:

    def __init__(self):
        self.fordoblingsKonstant = 2
        self.længde = 0
        self.indreListeLængde = 0
        self.indreListe = []

    def tilføj(self, element):
        if self.længde == 0:
            self.indreListe = [element]            
            self.indreListeLængde = 1
            self.længde = 1
        else:
            #Tjek om der skal laves en fordobling, og indsæt.
            if self.indreListeLængde == self.længde:
                self.indreListeLængde *= self.fordoblingsKonstant
                nyIndreListe = self.nyTomListe(self.indreListeLængde)
                self.flytElementerTilNyListe(nyIndreListe)
                self.indreListe = nyIndreListe
            self.indreListe[self.længde] = element
            self.længde += 1
    
    def sletSidsteElement(self):
        halveringsKonstant = 4
        self.længde -= 1
        self.indreListe[self.længde] = 'X'
        if self.længde <= self.indreListeLængde/halveringsKonstant:
            self.indreListeLængde = int(self.indreListeLængde/halveringsKonstant)
            nyIndreListe = self.nyTomListe(self.indreListeLængde)
            self.flytElementerTilNyListe(nyIndreListe)
            self.indreListe = nyIndreListe
    
    def flytElementerTilNyListe(self, nyIndreListe):
        for i in range(min(self.længde, self.indreListeLængde)):
            nyIndreListe[i] = self.indreListe[i]
    
    def nyTomListe(self, længde):
        return ['X'] * længde

    def printIndhold(self):
        print(self.indreListe)

def test():
    liste = DynamiskTabel()

    for i in range(1, 10):
        liste.tilføj(str(i))
        liste.printIndhold()
       
    
    print(liste.indreListe[5])
    
    liste.sletSidsteElement()
    liste.printIndhold()
    
    liste.sletSidsteElement()
    liste.printIndhold()
    
    liste.sletSidsteElement()
    liste.printIndhold()
    
    liste.sletSidsteElement()
    liste.printIndhold()
    
    liste.sletSidsteElement()
    liste.printIndhold()
    
    liste.sletSidsteElement()
    liste.printIndhold()
    
    liste.sletSidsteElement()
    liste.printIndhold()
    
    liste.sletSidsteElement()
    liste.printIndhold()
    
    

    
