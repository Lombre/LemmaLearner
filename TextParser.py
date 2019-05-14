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

allTexts = {}
allSentences = {}
allWords = {}
allLemmas = {}

def isCompoundWord(word):
    specialChar = u'­'
    pattern = re.compile(u'.*(-|­|­}).*')
    return pattern.match(word)


def shouldIgnore(rawWord):
    return not (1 < len(rawWord) and rawWord[0] != "`" and rawWord[0] != "'") \
           or isCompoundWord(rawWord) #I don't care much for compound words



class Text:
    def __init__(self, rawText):
        self.text = rawText
        rawSentences = nltk.sent_tokenize(rawText)
        self.sentences = []
        for rawSentence in rawSentences:
            sentence = Sentence(self, rawSentence)
            self.sentences.append(sentence)


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


class Word:
    def __init__(self, rawWord, originSentence):
        self.rawWord = rawWord
        self.sentences = {originSentence.rawSentence: originSentence}
        self.frequency = 1
        self.lemma = None

    #Marks the word as covered in the sentences it is found in.
    def coverSentences(self):
        for sentence in self.sentences.values():
            sentence.uncoveredWords.remove(self)

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

def addAllTextsFromDirectoryToDatabase(directory):
    files = [f for f in glob.glob(directory + "/*.txt")]
    for file in files:
        rawText = loadText(file)
        addRawTextToDatabase(rawText)

def addRawTextToDatabase(rawText):
    #Simply adds the text to the database: it all its sentences to allSentences,
    #and all its words to allWords, so that it can be used later.
    text = Text(rawText)
    allTexts[rawText] = text
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
    specialChar = u'­'
    pattern = re.compile(u'.*(-|­|­}).*')
    return pattern.match(word)

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
    # because we don't want to use all that sweet sweet computer power on repeatedly doing this later
    dictionary = enchant.Dict("en_US")
    wordSet = set(words.words())
    allWordValues = allWords.values()
    for word in allWordValues:
        lemma = lemmatizer.lemmatize(word.rawWord, get_wordnet_pos(word.rawWord))
        if isActualWord(dictionary, wordSet, lemma):
            if lemma in allLemmas:
                allLemmas[lemma].addNewWord(word)
            else:
                allLemmas[lemma] = Lemma(lemma, word)


def loadText(filename):
    file = io.open(filename, 'rU', encoding='utf-8')
    return file.read()

