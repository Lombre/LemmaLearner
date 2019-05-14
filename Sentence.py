# -*- coding: utf-8 -*-
from Word import Word
import nltk
import re
import string

def isCompoundWord(word):
    specialChar = u'­'
    pattern = re.compile(u'.*(-|­|­}).*')
    return pattern.match(word)

def shouldIgnore(rawWord):
    return not (1 < len(rawWord) and rawWord[0] != "`" and rawWord[0] != "'") \
           or isCompoundWord(rawWord) #I don't care much for compound words

class Sentence:
    def __init__(self, originText, rawSentence):
        self.text = originText
        self.rawSentence = rawSentence
        rawWords = nltk.word_tokenize(rawSentence)
        self.words = []
        self.uncoveredWords = set()#All the words found in the sentence, that haven't been learned yet. Must be initialized
        for rawWord in rawWords:
            #Ignores word if 1 => length, as it is probably just something like a comma or \":
            if not shouldIgnore(rawWord):
                word = re.sub('[' + string.punctuation + ']', '', rawWord)
                if 0 < len(word):
                    self.words.append(Word(word.lower(), self))

    def initializeForAnalysis(self):
        for word in self.words:
            self.uncoveredWords.add(word)

    def getNumberOfUncoveredWords(self):
        return len(self.uncoveredWords)

