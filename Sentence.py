# -*- coding: utf-8 -*-
from Word import Word
import nltk
import re
import string

compoundWordPattern = re.compile(u'.*(-|­|­}).*')
extraPunctuation = u"…"

def isCompoundWord(word):
    return compoundWordPattern.match(word)

def shouldIgnore(rawWord):
    return not (1 < len(rawWord) and rawWord[0] != "`" and rawWord[0] != "'") \
           or isCompoundWord(rawWord) #I don't care much for compound words

class Sentence:
    def __init__(self, originText, rawSentence):
        self.text = originText
        self.rawSentence = rawSentence
        rawWords = nltk.word_tokenize(rawSentence)
        self.words = []
        self.uncoveredWords = set() #All the words found in the sentence, that haven't been learned yet. Must be initialized
        self.uncoveredLemmas = set() #Same as above, but with lemmas.
        for rawWord in rawWords:
            #Ignores word if 1 => length, as it is probably just something like a comma or \":
            if not shouldIgnore(rawWord):
                word = re.sub('[' + string.punctuation + extraPunctuation + ']', '', rawWord)
                if 0 < len(word):
                    self.words.append(Word(word.lower(), self))
        self.associatedLearnableSentence = None
        self.scoreDependentSentences = set()

    def initializeForAnalysis(self):
        #Reseting:
        self.uncoveredWords = set()
        self.uncoveredLemmas = set()
        #Initializing
        for word in self.words:
            self.uncoveredWords.add(word)
            self.uncoveredLemmas.add(word.lemma)

    def rescoreScoreDependentSentences(getSentenceScore):
        return None

    def getNumberOfUncoveredWords(self):
        return len(self.uncoveredWords)

    def getNumberOfUncoveredLemmas(self):
        return len(self.uncoveredLemmas)

    def getOnlyUncoveredLemma(self):
        if self.getNumberOfUncoveredLemmas() != 1:
            raise Exception("There are " + str(self.getNumberOfUncoveredLemmas()) + " uncovered lemmas, not 1.")
        elif list(self.uncoveredLemmas)[0] == None:
            raise Exception("A word does not contain a lemma")
        else:
            #Faster than: list(self.uncoveredLemmas)[0]
            for uncoveredLemma in self.uncoveredLemmas:
                return uncoveredLemma

    def recoverWords(self, allWords):
        for i in range(0, len(self.words)):
            #Ensuring that the words in the sentence, points to those in the complete list of words
            #if not allWords.has_key(self.words[i].rawWord):
            #    raise Exception("The word: " + self.words[i].rawWord + " do not exist in allWords, though it exists in a sentence.")
            #self.words[i] = allWords[self.words[i].rawWord]

            #Ensuring that the word's associated sentence points to this sentence.
            self.words[i].sentences[self.rawSentence] = self