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


    def getFrequency(self):
        sum = 0
        for word in self.conjugatedWords:
            sum += word.frequency
        return sum

    def getRawLemma(self):
        return self.rawLemma

    def getSentences(self):
        allSentences = set()
        for word in self.conjugatedWords:
            wordSentences = word.sentences.values()
            for sentence in wordSentences:
                allSentences.add(sentence)
        return allSentences


    #Marks the lemma as covered in the sentences it is found in.
    def coverSentences(self):
        sentences = self.getSentences()
        for sentence in sentences:
            sentence.uncoveredLemmas.remove(self)