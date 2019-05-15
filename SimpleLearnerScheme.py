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

def getHighestScoringUnforcedSentence(sentenceQueue):
    return sentenceQueue.popitem()[0]


def getHighestScoringWord(mostFrequentWords):
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


def getSentenceScoreByNextUnlockableWord(learnedSentence, direclyUnlockableWords):
    # Teknisk set ikke helt korrekt metode, da den tjekker det bedste par af to ord man kan lære,
    # men ikke tvinger en til at lære de ord lige efter hinanden:
    # så bliver de nogen gange ikke valgt lige efter hinanden, og det er dermed ikke et optimalt par.
    # Man skal være meget præcist for at få det helt korrekt, hvilket jeg ikke gider at være

    unlockedWord = list(learnedSentence.uncoveredWords)[0]
    maxFrequencyUnlocked = 0

    for sentence in unlockedWord.sentences.values():
        if sentence.getNumberOfUncoveredWords() == 2: #Learning unlockedWord might unlock a new word in this sentence:
            unlockedWords = list(sentence.uncoveredWords)
            newUnlockedWord = unlockedWords[1] if (unlockedWords[0] == unlockedWord) else unlockedWords[0]
            if newUnlockedWord not in direclyUnlockableWords: #Now we know it definetly will unlock a new word!
                maxFrequencyUnlocked = newUnlockedWord.frequency if maxFrequencyUnlocked < newUnlockedWord.frequency else maxFrequencyUnlocked

    return -unlockedWord.frequency - maxFrequencyUnlocked

def getSentenceScoreAsWordFrequency(sentence):
    return -list(sentence.uncoveredWords)[0].frequency

def learnWordAndHandleSentencesWithWordFrequency(newWord, wordList, sentenceQueue, wordQueue, directlyUnlockableWords, getSentenceScore):
    wordList.append(newWord)
    #It is learned: new sentences become available:
    newWord.coverSentences()
    wordQueue.pop(newWord)
    if newWord in directlyUnlockableWords:
        directlyUnlockableWords.remove(newWord)
    #Finds all words that now has become unlockable
    for sentence in newWord.sentences.values():
        if sentence.getNumberOfUncoveredWords() == 1:
            directlyUnlockableWords.add(list(sentence.uncoveredWords)[0])

    #Scores all the sentences, especially those with newly unlockable words
    for sentence in newWord.sentences.values():
        if sentence.getNumberOfUncoveredWords() == 0:
            sentenceQueue[sentence] = missingWordFrequency
        elif sentence.getNumberOfUncoveredWords() == 1:
            sentenceQueue[sentence] = getSentenceScore(sentence, directlyUnlockableWords)


def learnWords(getSentenceScore):
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
            currentSentence = getHighestScoringUnforcedSentence(mostCoveredSentences)
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


def learnWordsByOrderOfScore(getSentenceScore):
    # Scheme: Learn words as they become possible to learn, in terms of sentences, in order of score

    # Initialize: Load all texts in Texts folder:
    TextParser.addAllTextsFromDirectoryToDatabase("Texts")


    # Will only contain sentences with fewer than or equal to one missing word, marked in order of the missing words frequency
    sentencesByFrequencyOfWords, directlyUnlockableWords = GetPriorityQueueOfDirectlyLearnableSentencesByWordFrequency()
    wordsByFrequency = getPriorityQueueOfWordsByFrequency()

    # Find which words one is forced to learn, without being able to isolate it to one sentence:
    forcedToLearn = []
    notForcedToLearn = []
    orderedLearningList = []
    i = 1
    while hasLearnedAllWords(orderedLearningList) == False:
        while hasDirectlyLearnableSentence(sentencesByFrequencyOfWords):
            currentSentence = getHighestScoringUnforcedSentence(sentencesByFrequencyOfWords)
            # No new word in the sentence:
            if currentSentence.getNumberOfUncoveredWords() == 0:# or len(currentSentence.words) <= 3:
                continue
            # A new word to learn: lets do it!
            newWord = getUnlearnedWordFromSentence(currentSentence)
            orderedLearningList.append((newWord, currentSentence))
            learnWordAndHandleSentencesWithWordFrequency(newWord, notForcedToLearn, sentencesByFrequencyOfWords, wordsByFrequency, directlyUnlockableWords, getSentenceScore)
            print(str(i) + ", " + newWord.rawWord + ", " + str(newWord.frequency) + " -> " + currentSentence.rawSentence)
            i += 1
        if hasLearnedAllWords(orderedLearningList):  # When all words have been learned in the loop above
            continue

        # There are no more free words: time to learn a frequent word:
        newWord = getHighestScoringWord(wordsByFrequency)
        orderedLearningList.append((newWord, "NONE"))
        print(str(i) + ", " + newWord.rawWord + ", " + str(newWord.frequency) + " -> " + "NONE")
        learnWordAndHandleSentencesWithWordFrequency(newWord, forcedToLearn, sentencesByFrequencyOfWords, wordsByFrequency, directlyUnlockableWords, getSentenceScore)
        i += 1

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
    directlyUnlockableWords = set()
    sentencesByFrequencyOfWords = heapdict()
    for sentence in TextParser.allSentences.values():
        sentence.initializeForAnalysis()
        if sentence.getNumberOfUncoveredWords() == 0:
            sentencesByFrequencyOfWords[sentence] = missingWordFrequency
        elif sentence.getNumberOfUncoveredWords() == 1:
            sentencesByFrequencyOfWords[sentence] = -list(sentence.uncoveredWords)[0].frequency
            directlyUnlockableWords.add(list(sentence.uncoveredWords)[0])
    return sentencesByFrequencyOfWords, directlyUnlockableWords

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
    #learningList = learnWordsByOrderOfScore(getSentenceScoreAsWordFrequency)
    learningList = learnWordsByOrderOfScore(getSentenceScoreByNextUnlockableWord)
    sentences = TextParser.allSentences
    TextParser.addLemmasToDatabase()

    allLemmas = list(TextParser.allLemmas.values())
    allLemmas.sort(key=lambda x: x.getSumOfFrequencies(), reverse=True)
    print(len(sentences))
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

