# -*- coding: utf-8 -*-
from Word import Word



class Lemma:
    def __init__(self, rawLemma, conjugatedWord):
        self.rawLemma = rawLemma
        self.conjugatedWords = {conjugatedWord}
        conjugatedWord.lemma = self

    def addNewWord(self, word):
        self.conjugatedWords.add(word)
        word.lemma = self

    def getSumOfFrequencies(self):
        sum = 0
        for word in self.conjugatedWords:
            sum += word.frequency
        return sum