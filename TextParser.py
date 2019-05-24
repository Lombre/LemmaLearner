# -*- coding: utf-8 -*-
import glob
import urllib2
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
import enchant
import re
import string
import Sentence
from Text import Text
from Sentence import Sentence
from Word import Word
from Lemma import Lemma
#import pickle as pickle
import cPickle as dill
import sys
import threading



NotATextRawTitle = "NotAFile"
NotATextRawText = "NotAWord."
NotALemmaRawLemma = "NotALemma"

NotAText = Text(NotATextRawText, NotATextRawTitle)
NotASentence = NotAText.sentences[0]
NotAWord = NotASentence.words[0]
NotAWordLemma = Lemma(NotALemmaRawLemma, NotAWord)


allTexts = {NotAText.name:NotAText}
allSentences = {NotASentence.rawSentence:NotASentence}
allWords = {NotAWord.rawWord:NotAWord}
allLemmas = {NotAWordLemma.rawLemma:NotAWordLemma}

everything = {"texts": allTexts, "sentences":allSentences, "words":allWords, "lemmas":allLemmas}

compoundWordPattern = re.compile(u'.*(-|­|­}).*')

def addAllTextsFromDirectoryToDatabase(directory):
    files = [f for f in glob.glob(directory + "/*.txt")]
    hasNewFile = False
    for file in files:
        fileName = os.path.splitext(os.path.basename(file))[0]
        if not allTexts.has_key(fileName):
            hasNewFile = True
            rawText = loadText(file)
            getBookCharacterset(rawText)
            addRawTextToDatabase(rawText, fileName)
    if hasNewFile:
        addLemmasToDatabase()

def addRawTextToDatabase(rawText, fileName):
    #Simply adds the text to the database: it all its sentences to allSentences,
    #and all its words to allWords, so that it can be used later.
    text = Text(rawText, fileName)
    allTexts[text.name] = text
    for sentence in text.sentences:
        allSentences[sentence.rawSentence] = sentence
        for i in range(0,len(sentence.words)):
            word = sentence.words[i]
            if allWords.has_key(word.rawWord):
                allWords[word.rawWord].sentences[sentence.rawSentence] = sentence
                allWords[word.rawWord].frequency = allWords[word.rawWord].frequency + 1
                sentence.words[i] = allWords[word.rawWord]
            else:
                allWords[word.rawWord] = word


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


def isInOnlineDictionary(word):
    baseURL = 'https://www.dictionary.com/browse/'
    fullURL = baseURL + word
    filePath = "Websites/" + word + ".txt"
    ERROR_CODE = "ERROR"
    if os.path.isfile(filePath):
        with open(filePath, 'r') as file:
            possibleErrorCode = file.read(len(ERROR_CODE))
            return possibleErrorCode != ERROR_CODE
    else:
        time.sleep(2) # So the website isn't getting spammed
        try:
            response = urllib2.urlopen(baseURL + word)
        except:
            with open(filePath, 'w+') as file:
                file.write(ERROR_CODE)
            return False
        webContent = response.read()
        with open(filePath, 'w+') as file:
            file.write(webContent)
        return True



def isActualWord(dictionary, wordSet, lemma):
    isInWordnet = lemma in wordSet
    isInDictionary = dictionary.check(lemma)
    isCompound = isCompoundWord(lemma)
    return not isCompound and (isInWordnet or isInDictionary or isInOnlineDictionary(lemma))

def addLemmasToDatabase():
    lemmatizer = WordNetLemmatizer()

    # Initializing them here,
    # because we don't want to use all that sweet sweet computing power on repeatedly doing this later
    dictionary = enchant.Dict("en_US")
    wordSet = set(words.words())
    allWordValues = allWords.values()
    i = 0
    for word in allWordValues:
        if word.lemma != None:
            #It already has an associated lemma, and as such can be skiped:
            continue

        lemma = lemmatizer.lemmatize(word.rawWord, get_wordnet_pos(word.rawWord))
        if i % 100 == 0:
            print(str(i) + " of " + str(len(allWords)) + ": " + lemma)
        i += 1
        if isActualWord(dictionary, wordSet, lemma):
            if lemma in allLemmas:
                # The lemma is already registered,
                # but the word might be a different conjugation than the ones already added to the lemma:
                allLemmas[lemma].addNewWord(word)
            else:
                allLemmas[lemma] = Lemma(lemma, word)
        else:
            # It is not a real word, and it is added to the token "NotAWordLemma" Lemma,
            # to ensure that all words have an associated lemma.
            NotAWordLemma.addNewWord(word)


def loadText(filename):
    file = io.open(filename, 'rU', encoding='utf-8')
    return file.read()

def saveProcessedData(data):
    currentRecursionLimit = sys.getrecursionlimit()
    sys.setrecursionlimit(100000)
    dill.dump(data, open('everything.pkl', 'wb'))
    sys.setrecursionlimit(currentRecursionLimit)

def loadProcessedData(fileName):
    currentRecursionLimit = sys.getrecursionlimit()
    sys.setrecursionlimit(100000)
    rawPickleData = io.open(fileName + ".pkl", 'rb').read()
    sys.setrecursionlimit(currentRecursionLimit)
    processedData = dill.loads(str(rawPickleData))

    global allTexts, allSentences, allWords, allLemmas, everything
    allTexts = processedData["texts"]
    allSentences = processedData["sentences"]
    allWords = processedData["words"]
    allLemmas = processedData["lemmas"]
    everything = {"texts": allTexts, "sentences": allSentences, "words": allWords, "lemmas": allLemmas}

    #Some data was deleted during pickeling: this is recovered below
    sentences = processedData["sentences"].values()
    words = processedData["words"].values()

    for sentence in sentences:
        sentence.recoverWords(allWords)
    for word in words:
        word.recoverLemma(allLemmas)

    resetNothingTerms()

    return processedData

def getBookCharacterset(rawText):

    alphabetSet = set()
    for i in range(0, len(rawText)):
        currentChar = rawText[i]
        alphabetSet.add(currentChar)
    alphabetList = list(alphabetSet)
    alphabetList.sort()
    for char in alphabetList:
        print(char)
    return alphabetList

def resetNothingTerms():
    global NotAText, NotASentence, NotAWord, NotAWordLemma
    NotAText = allTexts[NotATextRawTitle]
    NotASentence = NotAText.sentences[0]
    NotAWord = NotASentence.words[0]
    NotAWordLemma = NotAWord.lemma

