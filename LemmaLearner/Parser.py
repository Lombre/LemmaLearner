# -*- coding: utf-8 -*-
from Text import Text
from Sentence import Sentence
from Word import Word
from Lemma import Lemma
import glob
import urllib3
from heapdict import heapdict
import os.path
import time
import io
from nltk.stem.wordnet import WordNetLemmatizer
#import pattern
#from pattern.en import lemma
import nltk
from nltk.corpus import wordnet
from nltk.corpus import words
import re
import string
#import enchant
#import pickle as pickle
import pickle as dill
import sys
import threading
import onlinedictionary


compoundWordPattern = re.compile(u'.*(-|­|­}).*')

def isCompoundWord(word):
    return compoundWordPattern.match(word)

def get_wordnet_pos(word):
    """Map POS tag to first character lemmatize() accepts"""

    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}
    trueTag = tag_dict.get(tag, wordnet.NOUN)
    return trueTag
    
def getBookCharacterset(rawText, shouldPrintToConsole):

    alphabetSet = set()
    for i in range(0, len(rawText)):
        currentChar = rawText[i]
        alphabetSet.add(currentChar)
    alphabetList = list(alphabetSet)
    alphabetList.sort()
    for char in alphabetList:
        if shouldPrintToConsole:
            print(char)
    return alphabetList


def isActualWord(wordSet, onlineDictionary, lemma):
    #isInDictionary = dictionary.check(lemma)
    isInWordnet = lemma in wordSet
    isCompound = isCompoundWord(lemma)
    return not isCompound and (isInWordnet or onlinedictionary.isInOnlineDictionary(lemma, onlineDictionary))
    
def loadText(filename):
    file = io.open(filename, 'rU', encoding='utf-8')
    return file.read()


class TextParser():
    
    def __init__(self):
        self.NotATextRawTitle = "NotAFile"
        self.NotATextRawText = "NotAWord."
        self.NotALemmaRawLemma = "NotALemma"

        self.NotAText = Text(self.NotATextRawText, self.NotATextRawTitle)
        self.NotASentence = self.NotAText.sentences[0]
        self.NotAWord = self.NotASentence.words[0]
        self.NotAWordLemma = Lemma(self.NotALemmaRawLemma, self.NotAWord)


        self.allTexts = {self.NotAText.name:self.NotAText}
        self.allSentences = {self.NotASentence.rawSentence:self.NotASentence}
        self.allWords = {self.NotAWord.rawWord:self.NotAWord}
        self.allLemmas = {self.NotAWordLemma.rawLemma:self.NotAWordLemma}

        self.everything = {"texts":self.allTexts, "sentences":self.allSentences, "words":self.allWords, "lemmas":self.allLemmas}

        

    def initialize(self):    
        self.initializeLemmas()

    def addAllTextsFromDirectoryToDatabase(self, directory, shouldPrintToConsole):
        files = [f for f in glob.glob(directory + "/*.txt")]
        hasNewFile = False
        i = 1
        for file in files:
            fileName = os.path.splitext(os.path.basename(file))[0]
            if not fileName in self.allTexts:
                if shouldPrintToConsole:
                    print("Text " + str(i) + " of " + str(len(files)) +  ": " + fileName)
                    i += 1
                hasNewFile = True
                rawText = loadText(file)
                #getBookCharacterset(rawText, shouldPrintToConsole)
                self.addRawTextToDatabase(rawText, fileName)
        self.addLemmasToDatabase(shouldPrintToConsole)
        self.recognizeNamesInSentences()
        self.initialize()

    def addRawTextToDatabase(self, rawText, fileName):
        #Simply adds the text to the database: it all its sentences to allSentences,
        #and all its words to allWords, so that it can be used later.
        text = Text(rawText, fileName)
        self.allTexts[text.name] = text
        for sentence in text.sentences:
            self.allSentences[sentence.rawSentence] = sentence
            for i in range(0,len(sentence.words)):
                word = sentence.words[i]
                if word.rawWord in self.allWords:
                    self.allWords[word.rawWord].sentences[sentence.rawSentence] = sentence
                    self.allWords[word.rawWord].frequency = self.allWords[word.rawWord].frequency + 1
                    sentence.words[i] = self.allWords[word.rawWord]
                else:
                    self.allWords[word.rawWord] = word

    def recognizeNamesInSentences(self):
        for sentence in self.allSentences:
            kage = 1

    def addLemmasToDatabase(self, shouldPrintToConsole):
        lemmatizer = WordNetLemmatizer()

        # Initializing them here,
        # because we don't want to use all that sweet sweet computing power on repeatedly doing this later
        
        #dictionary = enchant.Dict("en_US")
        wordSet = set(words.words())
        allWordValues = set(self.allWords.values())
        allWordValues.remove(self.NotAWord)
        onlineDictionary = onlinedictionary.loadOnlineDictionary()
        i = 0        
        for word in allWordValues:

            if word.rawWord == "binoculars":
                 k = 1

            i += 1
            if word.lemma != None: #It already has an associated lemma, and as such can be skiped:
                continue

            lemma = lemmatizer.lemmatize(word.rawWord, get_wordnet_pos(word.rawWord))
            if (i == 1 or i % 100 == 0 or i == len(allWordValues)) and shouldPrintToConsole:
                print(str(i) + " of " + str(len(allWordValues)) + ": " + lemma)
            if isActualWord(wordSet, onlineDictionary, lemma):
                if lemma in self.allLemmas:
                    # The lemma is already registered,
                    # but the word might be a different conjugation than the ones already added to the lemma:
                    self.allLemmas[lemma].addNewWord(word)
                else:
                    self.allLemmas[lemma] = Lemma(lemma, word)
            else:
                # It is not a real word, and it is added to the token "NotAWordLemma" Lemma,
                # to ensure that all words have an associated lemma.
                self.NotAWordLemma.addNewWord(word)
        self.saveProcessedData(onlineDictionary, "onlineDictionary")

    def initializeLemmas(self):
        lemmas = self.allLemmas.values()
        for lemma in lemmas:
            lemma.setSentences()

    def saveProcessedData(self, data, fileName):
        currentRecursionLimit = sys.getrecursionlimit()
        sys.setrecursionlimit(100000)
        dill.dump(data, open(fileName + '.pkl', 'wb'))
        sys.setrecursionlimit(currentRecursionLimit)

    def loadProcessedData(self, fileName):
        currentRecursionLimit = sys.getrecursionlimit()
        sys.setrecursionlimit(100000)
        rawPickleData = io.open(fileName + ".pkl", 'rb').read()
        sys.setrecursionlimit(currentRecursionLimit)
        processedData = dill.loads(rawPickleData)

        #global self.allTexts, self.allSentences, self.allWords, self.allLemmas, self.everything
        self.allTexts = processedData["texts"]
        self.allSentences = processedData["sentences"]
        self.allWords = processedData["words"]
        self.allLemmas = processedData["lemmas"]
        self.everything = {"texts": self.allTexts, "sentences": self.allSentences, "words": self.allWords, "lemmas": self.allLemmas}

        #Some data was deleted during pickeling: this is recovered below
        self.sentences = processedData["sentences"].values()
        self.words = processedData["words"].values()
        #lemmas = processedData["lemmas"].values()

        for sentence in self.sentences:
            sentence.recoverWords(self.allWords)
        for word in self.words:
            word.recoverLemma(self.allLemmas)
        #for lemma in lemmas:
        #    lemma.recoverSentences()

        self.resetNothingTerms()

        return processedData
    
    def resetNothingTerms(self):
        #global NotAText, NotASentence, NotAWord, NotAWordLemma
        self.NotAText = self.allTexts[self.NotATextRawTitle]
        self.NotASentence = self.NotAText.sentences[0]
        self.NotAWord = self.NotASentence.words[0]
        self.NotAWordLemma = self.NotAWord.lemma

