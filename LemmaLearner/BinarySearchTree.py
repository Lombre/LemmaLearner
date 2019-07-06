# -*- coding: utf-8 -*-




class Node:
    def __init__(self, foraelder, vaerdi):
        self.foraelder = None
        self.vaerdi = vaerdi
        self.venstre = None
        self.hoejre = None
        

class Tree:

    def __init__(self):
        self.rod = None

    def minPunkt(self, punkt):
        while punkt.venstre != None:
            punkt = punkt.venstre
        return punkt

    def maksPunkt(self, punkt):
        while punkt.hoejre != None:
            punkt = punkt.hoejre
        return punkt
    
    def maks(self, forrigePunkt, nuvaerendePunkt):
        if nuvaerendePunkt == None:
            return forrigePunkt
        else:
            return self.maks(nuvaerendePunkt, nuvaerendePunkt.hoejre)

    def successor(self, punkt, soegeVaerdi):
        #Koden fra CLRS var daarlig, 
        ##så den er her baseret på koden fra algoritmekurset "Algoritmer og datastrukturer" på DTU.
        #Der startes med tree.successor(tree.rod, x), hvor x er søgeværdien.
        if punkt == None: 
            return None
        elif punkt.vaerdi == soegeVaerdi:
            return punkt
        elif punkt.vaerdi < soegeVaerdi:
            #Man skal til hoejre -> vi forsætter søgningen:
            return self.successor(punkt.hoejre, soegeVaerdi)
        else:
            #Nu er vi helt til hoejre, lige før at man bliver nød til at gå til venstre.
            #Vi vil derfor gerne have successoren til elementet i venstre træ.
            venstreSuccessor = self.successor(punkt.venstre, soegeVaerdi)
            if venstreSuccessor != None:
                return venstreSuccessor
            else:
                return punkt

    def soeg(self, soegevaerdi, punkt):
        #Baseret på CLRS
        if punkt == None or punkt.vaerdi == soegevaerdi:
            return punkt
        elif soegevaerdi < punkt.vaerdi:
            return self.soeg(soegevaerdi, punkt.venstre)
        else:
            return self.soeg(soegevaerdi, punkt.hoejre)

    def indsaet(self, indsaetVaerdi):
        #Baseret på CLRS
        nuvaerendePunkt = self.rod
        forrigePunkt = None
        #Essentielt set en søgning:
        while nuvaerendePunkt != None:
            forrigePunkt = nuvaerendePunkt
            if indsaetVaerdi < nuvaerendePunkt.vaerdi:
                nuvaerendePunkt = nuvaerendePunkt.venstre
            else:
                nuvaerendePunkt = nuvaerendePunkt.hoejre
        #Den faktiske indsættelse
        if forrigePunkt == None: #Traet var tomt:
            self.rod = Node(None, indsaetVaerdi)
        elif indsaetVaerdi < forrigePunkt.vaerdi:
            forrigePunkt.venstre = Node(forrigePunkt, indsaetVaerdi)
        else:
            forrigePunkt.hoejre  = Node(forrigePunkt, indsaetVaerdi)

    
    def indsaetRekursiv(self, forrigePunkt, nuvaerendePunkt, indsaetVaerdi):
        #Vi er i en indre knude, 
        #og alt efter dets værdi, skal vi besøge venstre eller højre barn.
        if nuvaerendePunkt != None:  
            if indsaetVaerdi < nuvaerendePunkt.vaerdi:
                self.indsaetRekursiv(nuvaerendePunkt, nuvaerendePunkt.venstre, indsaetVaerdi)
            else:
                self.indsaetRekursiv(nuvaerendePunkt, nuvaerendePunkt.hoejre, indsaetVaerdi)
        else: #Vi har nået stedet hvor nøglen (indsaetVaerdi) skal indsættes.
            if forrigePunkt == None: 
                #Traet var tomt: Vi indsætter værdien som roden for træet
                self.rod = Node(None, indsaetVaerdi)
            elif indsaetVaerdi < forrigePunkt.vaerdi:
                # Nøglen burde have været det venstre barn:
                # Vi indsætter det derfor som det venstre barn
                forrigePunkt.venstre = Node(forrigePunkt, indsaetVaerdi)
            else:
                #Vi indsætter nøglen som det højre barn
                forrigePunkt.hoejre  = Node(forrigePunkt, indsaetVaerdi)


def test():
    tree = Tree()
    result = str(tree.soeg(3, tree.rod))
    print("kage")
    print(result)
    tree.indsaet(100)
    print(str(tree.soeg(100, tree.rod).vaerdi))
    tree.indsaet(3)
    tree.indsaet(200)
    tree.indsaet(10)
    tree.indsaet(120)
    tree.indsaet(50)
    tree.indsaet(1)
    print(str(tree.soeg(3, tree.rod).vaerdi))
    print(str(tree.soeg(10, tree.rod).vaerdi))
    print(str(tree.soeg(200, tree.rod).vaerdi))
    print("Maks vaerdien = " + str(tree.maksPunkt(tree.rod).vaerdi))
    print("Maks vaerdien = " + str(tree.maks(None, tree.rod).vaerdi))
    print("Min vaerdien = "  + str(tree.minPunkt(tree.rod).vaerdi))

    
    print("Successor(1) = "  + str(tree.successor(tree.rod, 1).vaerdi))
    print("Successor(2) = "  + str(tree.successor(tree.rod, 2).vaerdi))
    print("Successor(110) = "  + str(tree.successor(tree.rod, 110).vaerdi))
    print("Successor(130) = "  + str(tree.successor(tree.rod, 139).vaerdi))

