# -*- coding: utf-8 -*-
import TextParser
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

missingWordFrequency = -100000000

def getUnforcedSentence(sentenceQueue):
    return sentenceQueue.popitem()[0]


def getMostFrequentUnlearnedWord(mostFrequentWords):
    return mostFrequentWords.peekitem()[0] #learnWord will pop it


def getUnlearnedWordFromSentence(currentSentence):
    if currentSentence.getNumberOfUncoveredWords() != 1:
        raise Exception("Error! There should be exactely one new word in this sentence!")
    return list(currentSentence.uncoveredWords)[0]


def learnWord(newWord, wordList, sentenceQueue, wordQueue):
    wordList.append(newWord)
    #It is learned: new sentences become available:
    newWord.coverSentences()
    wordQueue.pop(newWord)
    for sentence in newWord.sentences.values():
        sentenceQueue[sentence] = sentence.getNumberOfUncoveredWords()


def learnWordAndHandleSentencesWithWordFrequency(newWord, wordList, sentenceQueue, wordQueue):
    wordList.append(newWord)
    #It is learned: new sentences become available:
    if newWord.rawWord == "dragons":
        print()
    newWord.coverSentences()
    wordQueue.pop(newWord)
    for sentence in newWord.sentences.values():
        if sentence.getNumberOfUncoveredWords() == 0:
            sentenceQueue[sentence] = missingWordFrequency
        elif sentence.getNumberOfUncoveredWords() == 1:
            sentenceQueue[sentence] = -list(sentence.uncoveredWords)[0].frequency


def learnWordsAsTheyBecomeAvailable():
    # Scheme: Learn words as they become possible to learn, in terms of sentences.

    # Initialize
    rawText = TextParser.loadText("HarryPotter.txt")
    TextParser.addRawTextToDatabase(rawText)
    mostCoveredSentences = heapdict()

    for sentence in TextParser.allSentences.values():
        sentence.initializeForAnalysis()
        mostCoveredSentences[sentence] = sentence.getNumberOfUncoveredWords()

    # We don't want all the empty sentences
    while mostCoveredSentences.peekitem()[1] == 0:
        mostCoveredSentences.popitem()
    firstSentence = mostCoveredSentences.peekitem()
    print ("")

    mostFrequentWords = heapdict()
    for word in TextParser.allWords.values():
        mostFrequentWords[word] = -word.frequency

    # Find which words one is forced to learn, without being able to isolate it to one sentence:
    forcedToLearn = []
    notForcedToLearn = []
    orderedLearningList = []

    while len(mostCoveredSentences) != 0:
        mostUncoveredNumber = mostCoveredSentences.peekitem()[1]
        while len(mostCoveredSentences) != 0 and mostCoveredSentences.peekitem()[1] <= 1:
            currentSentence = getUnforcedSentence(mostCoveredSentences)
            # No new word in the sentence:
            if currentSentence.getNumberOfUncoveredWords() == 0:
                continue
            #A new word to learn: lets do it!
            newWord = getUnlearnedWordFromSentence(currentSentence)
            orderedLearningList.append(newWord.rawWord + ": " + newWord.frequency)
            learnWord(newWord, notForcedToLearn, mostCoveredSentences, mostFrequentWords)

        if len(mostFrequentWords) == 0: #I have no idea why this case can occur
            continue
        #There are no more free words: time to learn an frequent word:
        newWord = getMostFrequentUnlearnedWord(mostFrequentWords)
        orderedLearningList.append(newWord.rawWord + ": " + newWord.frequency)
        learnWord(newWord, forcedToLearn, mostCoveredSentences, mostFrequentWords)
    return orderedLearningList


def learnFrequentAvailableWords():
    # Scheme: Learn words as they become possible to learn, in terms of sentences, in their order of frequency.

    # Initialize: Load all texts in Texts folder:
    TextParser.addAllTextsFromDirectoryToDatabase("Texts")

    # Will only contain sentences with fewer than or equal to one missing word, marked in order of the missings words frequency
    sentencesByFrequencyOfWords = GetPriorityQueueOfDirectlyLearnableSentencesByWordFrequency()
    wordsByFrequency = getPriorityQueueOfWordsByFrequency()

    # Find which words one is forced to learn, without being able to isolate it to one sentence:
    forcedToLearn = []
    notForcedToLearn = []
    orderedLearningList = []

    while hasLearnedAllWords(orderedLearningList) == False:
        while hasDirectlyLearnableSentence(sentencesByFrequencyOfWords):
            currentSentence = getUnforcedSentence(sentencesByFrequencyOfWords)
            # No new word in the sentence:
            if currentSentence.getNumberOfUncoveredWords() == 0:
                continue
            # A new word to learn: lets do it!
            newWord = getUnlearnedWordFromSentence(currentSentence)
            orderedLearningList.append((newWord, currentSentence))
            learnWordAndHandleSentencesWithWordFrequency(newWord, notForcedToLearn, sentencesByFrequencyOfWords, wordsByFrequency)

        if hasLearnedAllWords(orderedLearningList):  # I have no idea why this case can occur
            continue

        # There are no more free words: time to learn a frequent word:
        newWord = getMostFrequentUnlearnedWord(wordsByFrequency)

        orderedLearningList.append((newWord, currentSentence))
        learnWordAndHandleSentencesWithWordFrequency(newWord, forcedToLearn, sentencesByFrequencyOfWords, wordsByFrequency)

    return orderedLearningList


def hasLearnedAllWords(orderedLearningList):
    return len(orderedLearningList) == len(TextParser.allWords)


def hasDirectlyLearnableSentence(sentencesByFrequencyOfWords):
    can = len(sentencesByFrequencyOfWords) != 0 and sentencesByFrequencyOfWords.peekitem()[0].getNumberOfUncoveredWords() <= 1
    return can


def getPriorityQueueOfWordsByFrequency():
    mostFrequentWords = heapdict()
    for word in TextParser.allWords.values():
        mostFrequentWords[word] = -word.frequency
    return mostFrequentWords

def GetPriorityQueueOfDirectlyLearnableSentencesByWordFrequency():
    sentencesByFrequencyOfWords = heapdict()
    for sentence in TextParser.allSentences.values():
        sentence.initializeForAnalysis()
        if sentence.getNumberOfUncoveredWords() == 0:
            sentencesByFrequencyOfWords[sentence] = missingWordFrequency
        elif sentence.getNumberOfUncoveredWords() == 1:
            sentencesByFrequencyOfWords[sentence] = -list(sentence.uncoveredWords)[0].frequency
    return sentencesByFrequencyOfWords

def downloadWebsites(learningList):

    baseURL = 'https://www.dictionary.com/browse/'

    for i in range(0, min(len(learningList), 700)):
        print(i)
        word = learningList[i]
        fullURL = baseURL + word[0]
        filePath = "Websites/" + word[0] + ".txt"
        if os.path.isfile(filePath):
            l = 1
        else:
            try:
                response = urllib2.urlopen(baseURL + word[0])
            except:
                print("Error on: " + word[0])
                with open(filePath, 'w+') as file:
                    file.write("ERROR")
                continue
            webContent = response.read()
            with open(filePath, 'w+') as file:
                file.write(webContent)
            time.sleep(12)

def addStemConjugationPair(wordToWordStem, wordStem, wordConjugation):
        if wordToWordStem.has_key(wordConjugation):
            listOfWordStems = wordToWordStem[wordConjugation]
            listOfWordStems.add(wordStem)
        else:
            wordToWordStem[wordConjugation] = {wordStem}



def wordStemmingUsingLemmaConjugationPairs(learningList):

    lemmaFile = "lemmatization-en.txt"
    file = io.open(lemmaFile, 'rU', encoding='utf-8')
    lemmaText = file.read()
    lemmaTextLines = lemmaText.splitlines()
    wordToWordStem = {}
    for lemma in lemmaTextLines:
        dividedLemma = lemma.split("\t")
        wordStem = dividedLemma[0]
        wordConjugation = dividedLemma[1]
        addStemConjugationPair(wordToWordStem, wordStem, wordConjugation)
        addStemConjugationPair(wordToWordStem, wordStem, wordStem)
    print("Loaded lemmas")

    allWordStems = set()
    uncontainedWords = []
    for wordSentencePair in learningList:
        word = wordSentencePair[0]
        if (wordToWordStem.has_key(word)):
            wordStems = wordToWordStem[word]
            k = 1
            for wordStem in wordStems:
                allWordStems.add(wordStem)
        else:
            uncontainedWords.append(word)
    for i in range(0, min(len(uncontainedWords), 8000)):
        print (str(i) + ": " + uncontainedWords[i])

if __name__ == '__main__':
    learningList = learnFrequentAvailableWords()
    TextParser.addLemmasToDatabase()
    allLemmas = list(TextParser.allLemmas.values())
    allLemmas.sort(key=lambda x: x.getSumOfFrequencies(), reverse=True)

    print("done")

#https://www.dictionary.com/browse/walked
#https://cran.r-project.org/web/packages/corpus/vignettes/stemmer.html
#https://github.com/michmech/lemmatization-lists/
#https://www.machinelearningplus.com/nlp/lemmatization-examples-python/

# #Start learning the n most common words.
# n = 300
# mostFrequentWords = heapdict()
# for word in TextParser.allWords.values():
#     mostFrequentWords[word] = -word.frequency
#
# for i in range(0, n):
#     currentWord = mostFrequentWords.popitem()
#     currentWord.coverSentences()
#     for sentence in currentWord.sentences.values():
#         mostCoveredSentences[sentence] = sentence.getNumberUncoveredWords()

