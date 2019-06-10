# -*- coding: utf-8 -*-




class Node:
    def __init__(self, foraelder, vaerdi):
        self.foraelder = None
        self.vaerdi = vaerdi
        self.venstre = None
        self.hoejre = None

        #Baseret på CLRS

        #naestePunkt = None
        #if self.vaerdi <= soegevaerdi:
        #    naestePunkt = self.venstre
        #else:
        #    naestePunkt = self.hoejre
        #if

               


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

    def successor(self, punkt, soegeVaerdi):
        #Baseret på algoritme fra kurset "Algoritmer og datastrukturer" på DTU
        if punkt == None:
            return None
        elif punkt.vaerdi == soegeVaerdi:
            return punkt
        elif punkt.vaerdi < soegevaerdi:
            #Man skal til hoejre -> vi forsætter søgningen:
            return successor(punkt.hoejre, soegeVaerdi)
        else:
            #Nu er vi helt til hoejre, lige før at man bliver nød til at gå til venstre.
            #Vi vil derfor gerne have successoren til elementet i venstre træ.
            venstreSuccessor = successor(punkt.vestre, soegeVaerdi)
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
        while nuvaerendePunkt != None:
            forrigePunkt = nuvaerendePunkt
            if indsaetVaerdi < nuvaerendePunkt.vaerdi:
                nuvaerendePunkt = nuvaerendePunkt.venstre
            else:
                nuvaerendePunkt = nuvaerendePunkt.hoejre
        if forrigePunkt == None: #Traet var tomt:
            self.rod = Node(None, indsaetVaerdi)
        elif indsaetVaerdi < forrigePunkt.vaerdi:
            forrigePunkt.venstre = Node(forrigePunkt, indsaetVaerdi)
        else:
            forrigePunkt.hoejre  = Node(forrigePunkt, indsaetVaerdi)

tree = Tree()
print(tree.soeg(3, tree.rod))
tree.indsaet(100)
print(tree.soeg(100, tree.rod).vaerdi)
tree.indsaet(3)
tree.indsaet(200)
tree.indsaet(10)
print(tree.soeg(3, tree.rod).vaerdi)
print(tree.soeg(10, tree.rod).vaerdi)
print(tree.soeg(200, tree.rod).vaerdi)
print("Maks vaerdien = " + str(tree.maksPunkt(tree.rod).vaerdi))
print("Min vaerdien = "  + str(tree.minPunkt(tree.rod).vaerdi))
