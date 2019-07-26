# -*- coding: utf-8 -*-
from Word import Word



class Lemma:

    def __init__(self, rawLemma, conjugatedWord):
        self.rawLemma = rawLemma
        self.conjugatedWords = {conjugatedWord}
        conjugatedWord.lemma = self
        self.sentences = None

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
        return self.sentences
        #return self.sentences

    def getDirectlyUnlockingSentence(self, isSentenceDirectlyUnlockable):
        for sentence in self.sentences:
            if isSentenceDirectlyUnlockable(sentence):
                return sentence
        raise Exception("No sentence can directle unlock the lemma: " + self.rawLemma)

    #Marks the lemma as covered in the sentences it is found in.
    def coverSentences(self):
        sentences = self.getSentences()
        for sentence in sentences:
            sentence.uncoveredLemmas.remove(self)

    def setSentences(self):
        allSentences = set()
        for word in self.conjugatedWords:
            wordSentences = word.sentences.values()
            for sentence in wordSentences:
                allSentences.add(sentence)
        self.sentences = allSentences

    def __getstate__(self):
        self.conjugatedWords = set()
        self.sentences = None
        return  self.__dict__
       
    def __str__(self):
        return self.rawLemma