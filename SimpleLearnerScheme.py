# -*- coding: utf-8 -*-
PYTHONIOENCODING="UTF-8"
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
import re
import string
import enchant
import sys
import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout)


missingWordFrequency = -100000000

def getHighestScoringUnforcedSentence(sentenceQueue):
    return sentenceQueue.popitem()[0]


def getHighestScoringLemma(mostFrequentLemmas):
    return mostFrequentLemmas.peekitem()[0] #learnWord will pop it


def getUnlearnedLemmaFromSentence(currentSentence):
    return currentSentence.getOnlyUncoveredLemma()


def learnWord(newWord, wordList, sentenceQueue, wordQueue):
    wordList.append(newWord)
    #It is learned: new sentences become available:
    newWord.coverSentences()
    wordQueue.pop(newWord)
    for sentence in newWord.sentences.values():
        sentenceQueue[sentence] = sentence.getNumberOfUncoveredWords()


def getSentenceScoreByNextUnlockableLemma(learnedSentence, directlyUnlockableLemmas):
    # Teknisk set ikke helt korrekt metode, da den tjekker det bedste par af to ord man kan lære,
    # men ikke tvinger en til at lære de ord lige efter hinanden:
    # så bliver de nogen gange ikke valgt lige efter hinanden, og det er dermed ikke et optimalt par.
    # Man skal være meget præcist for at få det helt korrekt, hvilket jeg ikke gider at være lige nu!

    unlockedLemma = learnedSentence.getOnlyUncoveredLemma()
    maxFrequencyUnlocked = 0

    if True:
        sentences = unlockedLemma.getSentences()
        for sentence in sentences:
            if sentence.getNumberOfUncoveredLemmas() == 2: #Learning unlockedLemma might unlock a new word in this sentence:
                unlockedLemmas = list(sentence.uncoveredLemmas)
                newUnlockedLemma = unlockedLemmas[1] if (unlockedLemmas[0] == unlockedLemma) else unlockedLemmas[0]
                if newUnlockedLemma not in directlyUnlockableLemmas: #Now we know it definetly will unlock a new word!
                    maxFrequencyUnlocked = newUnlockedLemma.getFrequency() if maxFrequencyUnlocked < newUnlockedLemma.getFrequency() else maxFrequencyUnlocked
                else:
                    #Her mangler der at håndretes et case
                    continue

    return -unlockedLemma.getFrequency() - maxFrequencyUnlocked

def getSentenceScoreAsLemmaFrequency(sentence):
    return sentence.getOnlyUncoveredLemma().getFrequency()

def learnLemmaAndHandleSentencesWithLemmaFrequency(newLemma, wordList, sentenceQueue, lemmaQueue, directlyUnlockableLemmas, getSentenceScore):
    wordList.append(newLemma)
    #It is learned: new sentences become available:
    newLemma.coverSentences()
    lemmaQueue.pop(newLemma)
    if newLemma in directlyUnlockableLemmas:
        directlyUnlockableLemmas.remove(newLemma)

    lemmaSentences = newLemma.getSentences()
    #Finds all words that now has become unlockable
    for sentence in lemmaSentences:
        if sentence.getNumberOfUncoveredLemmas() == 1:
            directlyUnlockableLemmas.add(sentence.getOnlyUncoveredLemma())

    #Scores all the sentences, especially those with newly unlockable words
    for sentence in lemmaSentences:
        if sentence.getNumberOfUncoveredLemmas() == 0:
            sentenceQueue[sentence] = missingWordFrequency
        elif sentence.getNumberOfUncoveredLemmas() == 1:
            sentenceScore = getSentenceScore(sentence, directlyUnlockableLemmas)
            sentenceQueue[sentence] = sentenceScore


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


def learnLemmasByOrderOfScore(getSentenceScore):
    # Scheme: Learn words as they become possible to learn, in terms of sentences, in order of score

    # Initialize: Load all texts in Texts folder:
    TextParser.addAllTextsFromDirectoryToDatabase("Texts")

    # Will only contain sentences with fewer than or equal to one missing word, marked in order of the missing words frequency
    sentencesByFrequencyOfLemmas, directlyUnlockableLemmas = getPriorityQueueOfDirectlyLearnableSentencesByLemmaFrequency()
    lemmasByFrequency = getPriorityQueueOfLemmasByFrequency()

    # Find which words one is forced to learn, without being able to isolate it to one sentence:
    forcedToLearn = []
    notForcedToLearn = []
    orderedLearningList = []
    #First we remove all words that are not true "words", for example names, by learning the NotAWordLemma lemma:
    learnLemmaAndHandleSentencesWithLemmaFrequency(TextParser.NotAWordLemma, notForcedToLearn, sentencesByFrequencyOfLemmas, lemmasByFrequency, directlyUnlockableLemmas, getSentenceScore)

    i = 1
    print("Start learning lemmas: " + str(len(lemmasByFrequency)))

    while not hasLearnedAllLemmas(lemmasByFrequency):
        while hasDirectlyLearnableSentence(sentencesByFrequencyOfLemmas):
            currentSentence = getHighestScoringUnforcedSentence(sentencesByFrequencyOfLemmas)
            # No new word in the sentence:
            if currentSentence.getNumberOfUncoveredLemmas() == 0:# or len(currentSentence.words) <= 3:
                continue
            # A new word to learn: lets do it!
            newLemma = currentSentence.getOnlyUncoveredLemma()
            orderedLearningList.append((newLemma, currentSentence))
            learnLemmaAndHandleSentencesWithLemmaFrequency(newLemma, notForcedToLearn, sentencesByFrequencyOfLemmas, lemmasByFrequency, directlyUnlockableLemmas, getSentenceScore)
            if i % 1000 == 0:
                print(i)
            if i < 6000:
                i = i
                #print(str(i) + ", " + newLemma.getRawLemma() + ", " + str(newLemma.getFrequency()) + " -> " + currentSentence.rawSentence)
            i += 1

        if hasLearnedAllLemmas(lemmasByFrequency):  # When all words have been learned in the loop above
            break

        # There are no more free words: time to learn a frequent word:
        newLemma = getHighestScoringLemma(lemmasByFrequency)
        orderedLearningList.append((newLemma, "NONE"))
        learnLemmaAndHandleSentencesWithLemmaFrequency(newLemma, forcedToLearn, sentencesByFrequencyOfLemmas, lemmasByFrequency, directlyUnlockableLemmas, getSentenceScore)
        if i < 6000:
            print(str(i) + ", " + newLemma.getRawLemma() + ", " + str(newLemma.getFrequency()) + " -> " + "NONE")
        i += 1

    return orderedLearningList


def hasLearnedAllLemmas(lemmasByFrequency):
    return len(lemmasByFrequency) == 0


def hasDirectlyLearnableSentence(sentencesByFrequencyOfLemmas):
    can = len(sentencesByFrequencyOfLemmas) != 0 and sentencesByFrequencyOfLemmas.peekitem()[0].getNumberOfUncoveredLemmas() <= 1
    return can


def getPriorityQueueOfLemmasByFrequency():
    mostFrequentLemmas = heapdict()
    for lemma in TextParser.allLemmas.values():
        mostFrequentLemmas[lemma] = -lemma.getFrequency()
    return mostFrequentLemmas

def getPriorityQueueOfDirectlyLearnableSentencesByLemmaFrequency():
    directlyUnlockableLemmas= set()
    sentencesByFrequencyOfLemmas = heapdict()
    TextParser.NotASentence.initializeForAnalysis()
    for sentence in TextParser.allSentences.values():
        sentence.initializeForAnalysis()
        if sentence.getNumberOfUncoveredLemmas() == 0:
            sentencesByFrequencyOfLemmas[sentence] = missingWordFrequency
        elif sentence.getNumberOfUncoveredLemmas() == 1:
            unlockableLemma = sentence.getOnlyUncoveredLemma()
            sentencesByFrequencyOfLemmas[sentence] = -unlockableLemma.getFrequency()
            directlyUnlockableLemmas.add(unlockableLemma)
    return sentencesByFrequencyOfLemmas, directlyUnlockableLemmas

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
    print(u'\u201cRon, what \u2014 ?\u201d\n\n\u201cSCABBERS!')
    test = TextParser.loadProcessedData("everything")
    learningList = learnLemmasByOrderOfScore(getSentenceScoreByNextUnlockableLemma)
    # TextParser.addAllTextsFromDirectoryToDatabase("Texts")
    TextParser.saveProcessedData(TextParser.everything, "everything")

    # texts = test["texts"].values()




    # token = nltk.word_tokenize("stared")
    # taggedToken = nltk.pos_tag(token)
    #
    # tokens = nltk.word_tokenize("Ron stared at him.")
    # taggedTokens = nltk.pos_tag(tokens)

    # lemmatizer = WordNetLemmatizer()

    # pos = TextParser.get_wordnet_pos("stared")
    # kage = lemmatizer.lemmatize("stared", pos)
    #

    sentences = TextParser.allSentences

    print(len(sentences))
    print("done")

#https://www.dictionary.com/browse/walked
#https://cran.r-project.org/web/packages/corpus/vignettes/stemmer.html
#https://github.com/michmech/lemmatization-lists/
#https://www.machinelearningplus.com/nlp/lemmatization-examples-python/
#https://www.nltk.org/book/ch07.html
