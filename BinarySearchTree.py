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
tree.indsaet(10)
tree.indsaet(200)
print(tree.soeg(3, tree.rod).vaerdi)
print(tree.soeg(10, tree.rod).vaerdi)
print(tree.soeg(200, tree.rod).vaerdi)

