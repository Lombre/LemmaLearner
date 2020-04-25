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
import simpleLemmatizer


compoundWordPattern = re.compile(u'.*(-|­|­}).*')
shouldResetSavedText = True

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


def isActualWord(wordSet, onlineDictionary, lemma: str) -> bool:
    #isInDictionary = dictionary.check(lemma)
    isNumber = lemma.isdigit()
    isInWordnet = lemma in wordSet
    isCompound = isCompoundWord(lemma)
    return (not isNumber) and (not isCompound) and (isInWordnet or onlinedictionary.isInOnlineDictionary(lemma, onlineDictionary))
    
def loadText(filename, textDatabase):
    file = io.open(filename, 'rU', encoding='utf-8')    
    rawText = file.read()
    text = Text(rawText, filename, textDatabase, True)
    return text

class TextParser():
    
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.onlineDictionary = onlinedictionary.loadOnlineDictionary()
        simpleLemmatizer.initialize("lemma.en.txt")
        self.wordSet = set(words.words())

        self.NotATextRawTitle = "NotAFile"
        self.NotATextRawText = "NotAWord."
        self.NotALemmaRawLemma = "NotALemma"

        self.allTexts = {}
        self.allSentences = {}
        self.allWords = {}
        self.allLemmas = {}

        self.NotAText = Text(self.NotATextRawText, self.NotATextRawTitle, self, False)
        self.NotASentence = self.NotAText.sentences[0]
        self.NotAWord = self.NotASentence.words[0]
        self.NotAWordLemma = self.NotAWord.getFirstLemma()
        

        #self.allTexts = {self.NotAText.name:self.NotAText}
        #self.allSentences = {self.NotASentence.rawSentence:self.NotASentence}
        #self.allWords = {self.NotAWord.rawWord:self.NotAWord}
        #self.allLemmas = {self.NotAWordLemma.rawLemma:self.NotAWordLemma}

        self.everything = {"texts":self.allTexts, "sentences":self.allSentences, "words":self.allWords, "lemmas":self.allLemmas}

    def initialize(self, shouldPrintToConsole):   
        if shouldPrintToConsole:
            print("Initializing textdabase")
        self.initializeSentences()
        self.initializeWords()
        self.initializeLemmas()
        if shouldPrintToConsole:
            print("Finished initilization")

    def addAllTextsFromDirectoryToDatabase(self, directory, shouldPrintToConsole):
        files = [f for f in glob.glob(directory + "/*.txt")]
        rawTexts = []
        hasNewFile = False
        i = 1
        for file in files:
            fileName = os.path.splitext(os.path.basename(file))[0]
            if not fileName in self.allTexts:
                if shouldPrintToConsole:
                    print("Text " + str(i) + " of " + str(len(files)) +  ": " + fileName)
                    i += 1
                hasNewFile = True
                if not shouldResetSavedText and self.doSavedFileExist(directory + "/" + fileName):
                    text = self.loadSavedText(directory + "/" + fileName)
                    self.addLoadedTextToDatabase(text, True)
                else:
                    text = loadText(file, self)
                    self.saveTextWithPreprocessing(directory + "/" + fileName, text)

                self.synchronizeDatabaseWithText(text)
                #self.synchronizeDatabase() #Makes it n^2, it really should be done on the basis of the text above
                self.resetNothingTerms()

                totalSentencesBeforeRemoval = len(self.allSentences)
                print("Before text sentence count: " + str(len(text.sentences)))
                text.removeUnlearnableSentences(self, True)
                totalSentencesAfterRemoval = len(self.allSentences)
                print("After text sentence count: " + str(len(text.sentences) - (totalSentencesBeforeRemoval - totalSentencesAfterRemoval)))
                print("Total sentence count: " + str(len(self.allSentences)))
                #getBookCharacterset(rawText, shouldPrintToConsole)
                #self.addRawTextToDatabase(text, fileName)
        
        self.synchronizeDatabase() # Not sure this is neccessary.
        #Ugly, needs to be rewritten
        onlinedictionary.saveOnlineDictionary(self.onlineDictionary)
        self.initialize(shouldPrintToConsole)

    def addLoadedTextToDatabase(self, text, shouldRemoveUnlearnableSentences):
        self.allTexts[text.name] = text
        for sentence in text.sentences:
            self.allSentences[sentence.rawSentence] = sentence
            for word in sentence.words:
                self.allWords[word.rawWord] = word
                for lemma in word.lemmas:
                    self.allLemmas[lemma.rawLemma] = lemma
        k = 1

    
    def removeSentenceIfUnlearnable(self, sentence, shouldRemoveUnlearnableSentences):
        if (shouldRemoveUnlearnableSentences and 
            self.isUnlearnableSentence(sentence) and 
            sentence.rawSentence in self.allSentences): #There might be duplicate sentences in texts, with different memory locations, so this is neccessary (trust me)

            #This needs to be here, as creating a sentence is not a pure function.
            self.removeSentenceFromDatabase(sentence)

    def doSavedFileExist(self, fileName):
        return os.path.isfile(fileName + "_preseperated" + ".pkl") 

    def loadSavedText(self, fileName):        
        currentRecursionLimit = sys.getrecursionlimit()
        sys.setrecursionlimit(100000)
        rawPickleData = io.open(fileName +  "_preseperated" + ".pkl", 'rb').read()
        sys.setrecursionlimit(currentRecursionLimit)
        processedData = dill.loads(rawPickleData)
        return processedData

    def saveTextWithPreprocessing(self, fileName, text):
        self.saveProcessedData(text, fileName + "_preseperated")

    def addRawTextToDatabase(self, text, fileName):
        #Simply adds the text to the database: it all its sentences to allSentences,
        #and all its words to allWords, so that it can be used later.
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

    def addWordToDatabase(self, word):
        if not word.rawWord in self.allWords:
            self.allWords[word.rawWord] = word
            self.addWordLemmaToDatabase(word)
            return word
        else:
            self.allWords[word.rawWord].frequency += 1
            return self.allWords[word.rawWord]
       
    def addWordLemmaToDatabase(self, word):
        #It already has an associated lemma, and as such can be skiped:
        if len(word.lemmas) != 0: 
            return

        rawLemmas = self.getRawLemmas(self.lemmatizer, word) 
        #self.printLemmaAddingProgress(allWordValues, i, printEveryNWord, rawLemmas, shouldPrintToConsole, word)
        self.addRawLemmasToDatabaseIfActualLemmas(self.onlineDictionary, rawLemmas, word, self.wordSet)

    def addSentenceToDatabase(self, sentence):
        #Assumes that the same sentence will not be found multiple times.
        #This assumption does not hold.
        self.allSentences[sentence.rawSentence] = sentence        
        for i in range(0,len(sentence.words)):
            #Overrides the word of the sentence with a data-base wide occurence of the word,
            #to eliminate inconsistent/duplicate references to words
            sentence.words[i] = self.allWords[sentence.words[i].rawWord]
            sentence.words[i].sentences[sentence.rawSentence] = sentence

            #adds the sentence to word lemmas:
            for lemma in sentence.words[i].lemmas:
                lemma.sentences.add(sentence)

    def removeSentenceFromDatabase(self, sentence):
        self.allSentences.pop(sentence.rawSentence)
        for word in set(sentence.words):
            word.sentences.pop(sentence.rawSentence)
            for lemma in word.lemmas:
                if lemma.sentences != None and sentence in lemma.sentences:
                    lemma.sentences.remove(sentence)


    def isUnlearnableSentence(self, sentence):
        if (not self.hasCorrectLength(sentence) or not self.hasLemmaWithLowSentenceCount(sentence)):
            return True
        else:
           return False
    
    def hasLemmaWithLowSentenceCount(self, sentence):
        maxSentenceCount = 100
        sentenceLemmas = set([word.getFirstLemma() for word in sentence.words])
        hasLowSentenceCount = False
        for lemma in sentenceLemmas:
            if (len(lemma.sentences) < maxSentenceCount):
                hasLowSentenceCount = True
                break
        if (not hasLowSentenceCount):
            k=1
        return hasLowSentenceCount


    def hasCorrectLength(self, sentence):
        return (5 <= len(sentence.words) and len(sentence.words) <= 12)

    def recognizeNamesInSentences(self):
        for sentence in self.allSentences:
            kage = 1

    def getRawLemmas(self, lemmatizer, word):
        rawLemmas = simpleLemmatizer.lemmatize(word.rawWord)
        possibleRawLemma = lemmatizer.lemmatize(word.rawWord, get_wordnet_pos(word.rawWord))
        #if possibleRawLemma != word.rawWord:
        #    rawLemmas = [possibleRawLemma]
        rawLemmas = [possibleRawLemma]
        return rawLemmas

    def printLemmaAddingProgress(self, allWordValues, i, printEveryNWord, rawLemmas, shouldPrintToConsole, word):
        if (i == 1 or i % printEveryNWord == 0 or i == len(allWordValues)) and shouldPrintToConsole:
            print(str(i) + " of " + str(len(allWordValues)) + ": " + word.rawWord + " -> " + str(rawLemmas))

    def addRawLemmasToDatabaseIfActualLemmas(self, onlineDictionary, rawLemmas, word, wordSet):
        for rawLemma in rawLemmas:
            if isActualWord(wordSet, onlineDictionary, rawLemma):
                if rawLemma in self.allLemmas:
                    # The lemma is already registered,
                    # but the word might be a different conjugation than the ones already added to the lemma:
                    self.allLemmas[rawLemma].addNewWord(word)
                else:
                    self.allLemmas[rawLemma] = Lemma(rawLemma, word)
            else:
                # It is not a real word, and it is added to the token "NotAWordLemma" Lemma,
                # to ensure that all words have an associated lemma.
                self.NotAWordLemma.addNewWord(word)

    def addAllLemmasToDatabase(self, shouldPrintToConsole):
        lemmatizer = WordNetLemmatizer()
        simpleLemmatizer.initialize("lemma.en.txt")

        # Initializing them here,
        # because we don't want to use all that sweet sweet computing power on repeatedly doing this later
        
        #dictionary = enchant.Dict("en_US")
        wordSet = set(words.words())
        allWordValues = set(self.allWords.values())
        allWordValues.remove(self.NotAWord)
        onlineDictionary = onlinedictionary.loadOnlineDictionary()

        i = 0        
        printEveryNWord = 100
        for word in allWordValues:
            i += 1
            if word.lemmas != None: #It already has an associated lemma, and as such can be skiped:
                continue

            rawLemmas = self.getRawLemmas(lemmatizer, word) 
            self.printLemmaAddingProgress(allWordValues, i, printEveryNWord, rawLemmas, shouldPrintToConsole, word)
            self.addRawLemmasToDatabaseIfActualLemmas(onlineDictionary, rawLemmas, word, wordSet)

        onlineDictionary.saveOnlineDictionary()
        print("Found " + str(len(self.allWords)) + " words.")
        print("Found " + str(len(self.allLemmas)) + " lemmas.")

    def initializeLemmas(self):
        lemmas = self.allLemmas.values()
        for lemma in lemmas:
            lemma.setSentences()
            lemma.setTexts()
            lemma.setTimesLearned()

    def initializeSentences(self):
        sentences = self.allSentences.values()
        for sentence in sentences:
            sentence.setWords()

    def initializeWords(self):
        words = self.allWords.values()
        for word in words:
            word.setLemmas()

    def saveProcessedData(self, data, fileName):
        print("Saving " + fileName)
        currentRecursionLimit = sys.getrecursionlimit()
        sys.setrecursionlimit(100000)
        dill.dump(data, open(fileName + '.pkl', 'wb'))
        sys.setrecursionlimit(currentRecursionLimit)
        print("Finished saving " + fileName)

    
    def synchronizeDatabaseWithText(self, text):
        sentences = set(text.sentences)
        self.synchronizeSentencesWithDatabase(sentences)
        words = set()
        lemmas = set()
        for sentence in sentences:
            for word in sentence.words:
                words.add(word)
                lemmas.add(word.getFirstLemma())
        self.synchronizeWordsAndLemmasWithDatabase(words, lemmas)
                


    def synchronizeDatabase(self):
        self.synchronizeDatabaseWithGivenInformation(self.allSentences.values(), 
                                                     self.allWords.values(), 
                                                     self.allLemmas.values())
    
    def synchronizeSentencesWithDatabase(self, sentences):
        for sentence in sentences:
            for i in range(0, len(sentence.words)):
                #Ensuring that the words are the database-wide words:
                sentence.words[i] = self.allWords[sentence.words[i].rawWord]
        
                #Ensuring that the word's associated sentence points to this sentence.
                sentence.words[i].sentences[sentence.rawSentence] = sentence

    def synchronizeWordsAndLemmasWithDatabase(self, words, lemmas):

        #Synchronize words with lemmas:
        
        for lemma in lemmas:
            lemma.conjugatedWords.clear()
        
        for word in words:
            #Replace lemmas with database-wide lemmas:
            textDatabaseLemmas = set()
            for lemma in word.lemmas:
                textDatabaseLemmas.add(self.allLemmas[lemma.rawLemma])
                lemma.conjugatedWords.add(word)
            word.lemmas = textDatabaseLemmas
            
        #Synchronize lemmas with words:
        
        for lemma in lemmas:            
            lemma.setSentences()

    def synchronizeDatabaseWithGivenInformation(self, sentences, words, lemmas):
        
        self.synchronizeSentencesWithDatabase(sentences)
        
        self.synchronizeWordsAndLemmasWithDatabase(words, lemmas)

    def loadProcessedData(self, fileName):
        print("Loading " + fileName)
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

        #lemmas = processedData["lemmas"].values()


        #Synchronize texts and sentences:
               
        #Synchonize sentences and words:
        self.synchronizeDatabase()

        self.resetNothingTerms()
        self.initialize(True)
        
        print("Finished loading " + fileName)
        return processedData
    
    def resetNothingTerms(self):
        #global NotAText, NotASentence, NotAWord, NotAWordLemma

        self.NotAText = self.allTexts[self.NotATextRawTitle]
        self.NotASentence = self.NotAText.sentences[0]
        self.NotASentence.words[0] = self.allWords["notaword"]
        self.NotAWord = self.NotASentence.words[0]
        #Necessary, as the loaded data has a different lemma from the NotAText.
        #Not sure why it is the case.
        notawordlemma = self.allLemmas["notaword"]
        self.NotAWord.lemmas = {notawordlemma}
        self.NotAWordLemma = self.allLemmas["notaword"]
