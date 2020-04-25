# -*- coding: utf-8 -*-
PYTHONIOENCODING="UTF-8"
import Parser
from Parser import TextParser
import glob
import urllib3
from heapdict import heapdict
import os.path
import time
import io
from nltk.stem.wordnet import WordNetLemmatizer
#import pattern
#from pattern.en import lemma
from Lemma import Lemma
from Sentence import Sentence
import nltk
from nltk.corpus import wordnet
from nltk.corpus import words
import re
import string
#import enchant
import sys
#import codecs
import collections
import simpleLemmatizer
#sys.stdout = codecs.getwriter('utf8')(sys.stdout)

missingWordFrequency = -100000000
minSentenceLength = 5
maxSentenceLength = 12
MAX_TIMES_LEARNED_WORD = 5
WORD_SCORING_MULTIPLIER = 3
SHOULD_LEARN_BASED_ON_LEMMAS = True
TEXTS_LEMMAS_NEEDS_TO_BE_IN = {"Texts\\Test\\HarryPotter.txt"} #{"Texts\\Wheel of Time, The - Robert Jordan & Brandon Sanderson.txt", "Texts\\Dresden Files Omnibus (1-15), The - Jim Butcher.txt"} #If the set is empty, then there are no requirements for the lemmas.
LemmasFromRequiredTexts = set()


class SentenceAndLemmaScores:
    """
        A simple class for storing a lot of lists, sets and priority queues, relating to sentences and lemmas, and their scores.
    """

    def __init__(self, sentenceScores, directlyUnlockableLemmasScore, sentencePairsBySentenceScore, directlyUnlockableLemmas):
        self.sentenceScores = sentenceScores
        self.directlyUnlockableLemmasScore = directlyUnlockableLemmasScore
        self.sentencePairsBySentenceScore = sentencePairsBySentenceScore
        self.directlyUnlockableLemmas = directlyUnlockableLemmas

class LemmaScore:    
    """ 
        A simple class for storing the score of a lemma (in terms of which lemma to learn next).
        In the case that lemmas are learned in pairs, the next sentence containg the other lemma that should be learned,
        is stored in nextSentence 
    """
    def __init__(self, score, nextSentence=None):
        self.score = score
        self.nextSentence = nextSentence

def getHighestScoringLemma(mostFrequentLemmas):
    return mostFrequentLemmas.peekitem()[0] #learnWord will pop it

def getUnlearnedLemmaFromSentence(currentSentence):
    return currentSentence.getOnlyUncoveredLemma()

def getHighestScoringDirectlyLearnableLemma(directlyUnlockableLemmasScore):
    return [directlyUnlockableLemmasScore.popitem()[0]]

def getSentenceScoreByLemmaFrequency(learnedSentence: Sentence) -> LemmaScore:    
    unlockedLemma = learnedSentence.getOnlyUncoveredLemma()
    return LemmaScore(-unlockedLemma.getFrequency(), None)


def getSentenceScoreByConjugationFrequency(learnedSentence: Sentence) -> LemmaScore:
    unlockedLemma = learnedSentence.getOnlyUncoveredLemma()
    totalConjugationFrequency = 0
    for word in set(learnedSentence.words):  
        #if word.timesLearned < MAX_TIMES_LEARNED_WORD and word.getFirstLemma().rawLemma != "NotALemma":
        if SHOULD_LEARN_BASED_ON_LEMMAS:
            timesLearned = word.getFirstLemma().getTimesLearned()
        else:
            timesLearned = word.timesLearned
        if timesLearned < MAX_TIMES_LEARNED_WORD and word.getFirstLemma().rawLemma != "NotALemma":
            learningModefier = (1/WORD_SCORING_MULTIPLIER)**(timesLearned+1)
            learningConstant = 1
            totalConjugationFrequency += learningConstant * learningModefier

    
    return LemmaScore(-unlockedLemma.getFrequency() - totalConjugationFrequency, None)

def getSentenceScoreAsLemmaFrequency(sentence):
    return sentence.getOnlyUncoveredLemma().getFrequency()

def learnLemmaAndHandleSentencesWithLemmaFrequency(newLemma: Lemma, learningList, lemmaQueue, sentenceAndLemmaScores: SentenceAndLemmaScores, getSentenceScore):
    learningList.append(newLemma)

    if newLemma in sentenceAndLemmaScores.directlyUnlockableLemmas:
        sentenceAndLemmaScores.directlyUnlockableLemmas.remove(newLemma)

    #It is learned - new sentences become available and ready for learning:
    newLemma.coverSentences()
    lemmaQueue.pop(newLemma)

    lemmaSentences = newLemma.getSentences()
    #Finds all words that now has become unlockable
    for sentence in lemmaSentences:
        if isSentenceDirectlyUnlockable(sentence):
            sentenceAndLemmaScores.sentenceScores[sentence] = getSentenceScore(sentence).score
            sentenceAndLemmaScores.directlyUnlockableLemmas.add(sentence.getOnlyUncoveredLemma())

def printLearnedLemma(i, newLemma, rawSentence, shouldPrintToConsole):
    if (i < 2000 or i % 100 == 0) and shouldPrintToConsole:
        print(str(i) + ", " + newLemma.getRawLemma() + ", " + str(newLemma.getFrequency()) + " -> " + rawSentence)
    i += 1
    return i

def markConjugationInSentenceAsLearned(sentence, sentenceScores, getSentenceScore):
    for word in set(sentence.words):
        word.hasBeenLearned = True        
        word.incrementTimesLearned()
        if SHOULD_LEARN_BASED_ON_LEMMAS and word.getFirstLemma().getTimesLearned() < MAX_TIMES_LEARNED_WORD:
            # There might be some sentences in the priority queue with a score that depends on the number of times the lemma has been learned.
            # Their score therefore needs to be updated:
            for wordSentence in word.getFirstLemma().getSentences():
                if isSentenceDirectlyUnlockable(wordSentence):                    
                    sentenceScores[wordSentence] = getSentenceScore(wordSentence).score 
        elif not SHOULD_LEARN_BASED_ON_LEMMAS and word.timesLearned < MAX_TIMES_LEARNED_WORD:
            # There might be some sentences in the priority queue with a score that depends on this conjugation.
            # Their score therefore needs to be updated:
            for wordSentence in word.sentences.values():
                if isSentenceDirectlyUnlockable(wordSentence):                    
                    sentenceScores[wordSentence] = getSentenceScore(wordSentence).score 
    #The sentence is added back into the priority quoue by the code above.
    if (sentence in sentenceScores):
        sentenceScores.pop(sentence)
    #sentenceScores.pop(sentence)

def learnListOfSentences(sentenceList, i, lemmasByFrequency, notForcedToLearn, orderedLearningList, sentenceAndLemmaScores: SentenceAndLemmaScores, getSentenceScore, shouldPrintToConsole):
    for sentence in sentenceList:
        if sentence == None:
            continue
        if sentence.associatedLearnableSentence != None:
            #As the sentence will be learned, it is removed as a score dependent sentence.
            sentence.associatedLearnableSentence.scoreDependentSentences.remove(sentence)
            raise Exception("This should not be possible, as lemmas are not learned as pairs.")
                
        newLemma = sentence.getOnlyUncoveredLemma()
        orderedLearningList.append((newLemma, sentence))
        i = printLearnedLemma(i, newLemma, sentence.rawSentence, shouldPrintToConsole)
        markConjugationInSentenceAsLearned(sentence, sentenceAndLemmaScores.sentenceScores, getSentenceScore)
        learnLemmaAndHandleSentencesWithLemmaFrequency(newLemma, notForcedToLearn, lemmasByFrequency, sentenceAndLemmaScores, getSentenceScore)            
    return i

def learnMostFrequentLemma(i, lemmasByFrequency, forcedWordLearningList, orderedLearningList, sentenceAndLemmaScores: SentenceAndLemmaScores, getSentenceScore, shouldPrintToConsole):
    newLemma = getHighestScoringLemma(lemmasByFrequency)
    orderedLearningList.append((newLemma, None))
    learnLemmaAndHandleSentencesWithLemmaFrequency(newLemma, forcedWordLearningList, lemmasByFrequency, sentenceAndLemmaScores, getSentenceScore)            
    i = printLearnedLemma(i, newLemma, "NONE", shouldPrintToConsole)
    return i

def printNumberOfCoveredSentences(shouldPrintToConsole, textDatabase):
    totalNumberOfSentences = len(textDatabase.allSentences)
    numberOfCoveredSentences = 0
    for sentence in textDatabase.allSentences.values():
        if sentence.getNumberOfUncoveredLemmas() == 0:
            numberOfCoveredSentences += 1
    if shouldPrintToConsole:
        print("Number of covered sentences: " + str(numberOfCoveredSentences) + " of " + str(totalNumberOfSentences) + " -> " + str(numberOfCoveredSentences/totalNumberOfSentences))
    k=1

def printAlternativeSentences(count, currentSentence, getSentenceScore, i, sentenceAndLemmaScores, shouldPrintToConsole):
    if ((i < 2000 or i % 100 == 0) and False) and shouldPrintToConsole:
        # An elaborate way to gain the 5 highest scoring sentences
        # One could get it down to log n time by having a search tree for each word,
        # according to each sentence the word is in.
        lemmaToLearn = currentSentence[0].getOnlyUncoveredLemma()
        lemmaSentencesWithScore = heapdict()
        lemmaSentencesWithScore[currentSentence[0]] = getSentenceScore(currentSentence[0]).score
        for sentence in lemmaToLearn.sentences:
            if sentence in sentenceAndLemmaScores.sentenceScores:
                score = sentenceAndLemmaScores.sentenceScores[sentence]
                lemmaSentencesWithScore[sentence] = score
    
        #Now we can quickly sort the sentences:
        sortedSentencesWithScore = []
        while 0 < len(lemmaSentencesWithScore):
            sentenceWithScore = lemmaSentencesWithScore.popitem()
            sortedSentencesWithScore.append(sentenceWithScore)
    
        #And print the best sentences:
        for k in range(0, min(count, len(sortedSentencesWithScore))):
            #print(str(sortedSentencesWithScore[k][1]))
            print("      | " + str(sortedSentencesWithScore[k][1]) + " | " + sortedSentencesWithScore[k][0].rawSentence)

def removeSentencesOfIncorrectLength(textDatabase):
    sentencesOfIncorrectLength = []
    for sentence in textDatabase.allSentences.values():
        if not hasCorrectLength(sentence):
            sentencesOfIncorrectLength.append(sentence)
    for sentence in sentencesOfIncorrectLength:
        textDatabase.removeSentenceFromDatabase(sentence)          

def removeSentencesContainingBannedLemmas(textDatabase):
    #Remove all sentences that involves lemmas that does not fullfill the requirements.
    for lemma in textDatabase.allLemmas.values():
        if not isLemmaInRequiredTexts(lemma, textDatabase):
            sentencesToRemove = set()
            for sentence in lemma.sentences:
                #There might be multiple lemmas in the sentence, and the sentence can't be removed twice.
                if sentence.rawSentence in textDatabase.allSentences: 
                    sentencesToRemove.add(sentence)
            for sentence in sentencesToRemove:
                textDatabase.removeSentenceFromDatabase(sentence)
            lemma.sentences.clear()
            for word in lemma.conjugatedWords:
                word.sentences.clear()

def removeUnlearnableSentences(textDatabase, shouldPrintToConsole):    
    if shouldPrintToConsole:
        print("Initial number of sentences: " + str(len(textDatabase.allSentences)))
    #removeSentencesOfIncorrectLength(textDatabase)
    removeSentencesContainingBannedLemmas(textDatabase)
    #removeSentencesToGivenLimit(textDatabase)
    if shouldPrintToConsole:
        print("Number of sentences after removal: " + str(len(textDatabase.allSentences)))

def removeSentencesToGivenLimit(textDatabase):
    #This will make the sentence-to-lemma and sentence-to-word relationship asymmetric.
    sentenceLimit = 1000
    allSentences = set()
    #Isolating the desired number of sentences, and then removing all sentences, 
    #so the isolated sentences can be added back later.
    for lemma in textDatabase.allLemmas.values(): 
        sentenceLimitSet = set()
        for sentence in lemma.sentences:
            if len(sentenceLimitSet) <= sentenceLimit:
                sentenceLimitSet.add(sentence)
            else:
                break
        lemma.sentences.clear()
        for word in lemma.conjugatedWords:
            word.sentences.clear()
        allSentences = allSentences.union(sentenceLimitSet)

    textDatabase.allSentences.clear()

    #Adding the isolated sentences back to the database, so that it only contains those sentences.
    for sentence in allSentences:
        textDatabase.allSentences[sentence.rawSentence] = sentence
        for word in sentence.words:
            word.sentences[sentence.rawSentence] = sentence
            word.getFirstLemma().sentences.add(sentence)

        



def printInformationAboutLearnedLemmas(orderedLearningList, unforcedWordLearningList, shouldPrintToConsole, textDatabase):    
    if not shouldPrintToConsole:
        return

    print("Learned directly " + str(len(unforcedWordLearningList)) + " of " + str(len(orderedLearningList)) + " lemmas.")

    lemmasLearned = set([lemmaSentencePair[0] for lemmaSentencePair in orderedLearningList])
    wordsWithLearnedLemmas = [word for word in  textDatabase.allWords.values() if (word.getFirstLemma() in lemmasLearned) and word.getFirstLemma() != textDatabase.NotAWordLemma]
    print("Number of conjugations of learned lemmas: " + str(len(wordsWithLearnedLemmas)))
    for i in range(0, 11):
        wordLearnedITimes = set()
        for word in wordsWithLearnedLemmas:
            if word.timesLearned == i:
                wordLearnedITimes.add(word)
        print("Number of words learned " + str(i) + " times: " + str(len(wordLearnedITimes)))
    
    print()
    
    for i in range(0, 11):
        lemmasLearnedITimes = set()
        for lemma in lemmasLearned:
            if lemma.getTimesLearned() == i:
                lemmasLearnedITimes.add(lemma)
        print("Number of lemmas learned " + str(i) + " times: " + str(len(lemmasLearnedITimes)))

def printCurrentStatusInLemmaLearning(i, sentenceAndLemmaScores, shouldPrintToConsole, textDatabase):
    if ((i < 2000 or i % 100 == 0) and False) and shouldPrintToConsole:
        print("Number of directly learnable lemmas: " + str(len(sentenceAndLemmaScores.directlyUnlockableLemmas)))
    if (i % 100 == 0 and False):
        printNumberOfCoveredSentences(shouldPrintToConsole, textDatabase)

def learnDirectlyLearnableSentence(getSentenceScore, i, lemmasByFrequency, orderedLearningList, sentenceAndLemmaScores, shouldPrintToConsole, unforcedWordLearningList):
    currentSentence = getHighestScoringDirectlyLearnableLemma(sentenceAndLemmaScores.sentenceScores)

    # There needs to be a new word in the sentence:
    if not hasNoNewLemmas(currentSentence):
        printAlternativeSentences(5, currentSentence, getSentenceScore, i, sentenceAndLemmaScores, shouldPrintToConsole)
    
        # A new pair of words to learn: lets do it!
        i = learnListOfSentences(currentSentence, i, lemmasByFrequency, unforcedWordLearningList, orderedLearningList, sentenceAndLemmaScores, getSentenceScore, shouldPrintToConsole)
    return i

def printInitialLearningInformation(lemmasByFrequency, sentenceAndLemmaScores, shouldPrintToConsole):
    if shouldPrintToConsole:
        print("Start learning lemmas: " + str(len(lemmasByFrequency)))
        print("Number of directly learnable lemmas: " + str(len(sentenceAndLemmaScores.directlyUnlockableLemmas)))

def learnLemmasByOrderOfScore(maxNumberOfLemmasToLearn, textDatabase, getSentenceScore, shouldPrintToConsole):
    # Scheme: Learn words as they become possible to learn, in terms of sentences, in order of score

    # Initialize everything, including the sentences
    textDatabase.initialize(shouldPrintToConsole)
    
    #Some sentences are unlearnable, in the sense that they for example are to long or short.
    #They are removed to speed up the later processes.
    removeUnlearnableSentences(textDatabase, shouldPrintToConsole)

    # Will only contain sentences with fewer than or equal to one missing word, marked in order of the missing words frequency
    sentenceAndLemmaScores = getPriorityQueueOfDirectlyLearnableSentencesByLemmaScore(textDatabase, getSentenceScore)
    lemmasByFrequency = getPriorityQueueOfLemmasByFrequency(textDatabase)

    # Find which words one is forced to learn, without being able to isolate it to one sentence:
    forcedWordLearningList = []
    unforcedWordLearningList = []
    orderedLearningList = []

    #First we remove all words that are not true "words", for example names, by learning the NotAWordLemma lemma:
    learnLemmaAndHandleSentencesWithLemmaFrequency(textDatabase.NotAWordLemma, unforcedWordLearningList, lemmasByFrequency, sentenceAndLemmaScores, getSentenceScore)

    #For printing to the console. It makes it easier to debug:
    i = 0

    printInitialLearningInformation(lemmasByFrequency, sentenceAndLemmaScores, shouldPrintToConsole)
    
    i = learnInitialSentence(textDatabase, i, lemmasByFrequency, unforcedWordLearningList, orderedLearningList, sentenceAndLemmaScores, getSentenceScore, shouldPrintToConsole)
    
    #TODO Obs. fejl i pointgivningen af sætninger, det ser ud til at den runder ned når den skal vælge imellem dem. Kommatal er derfor ligegyldigt?

    while (not hasLearnedAllLemmas(lemmasByFrequency)) and (i <= maxNumberOfLemmasToLearn or maxNumberOfLemmasToLearn == -1):
        if hasDirectlyLearnableSentence(sentenceAndLemmaScores.sentenceScores):
            i = learnDirectlyLearnableSentence(getSentenceScore, i, lemmasByFrequency, orderedLearningList, sentenceAndLemmaScores, shouldPrintToConsole, unforcedWordLearningList) 
        else: 
            # There are no more "free" words - time to learn a frequent word, without an associated sentence:
            i = learnMostFrequentLemma(i, lemmasByFrequency, forcedWordLearningList, orderedLearningList, sentenceAndLemmaScores, getSentenceScore, shouldPrintToConsole)
        printCurrentStatusInLemmaLearning(i, sentenceAndLemmaScores, shouldPrintToConsole, textDatabase)
                    
    printInformationAboutLearnedLemmas(orderedLearningList, unforcedWordLearningList, shouldPrintToConsole, textDatabase)

    return orderedLearningList

def learnInitialSentence(textDatabase: TextParser, i,  lemmasByFrequency, notForcedToLearn, orderedLearningList, sentenceAndLemmaScores: SentenceAndLemmaScores, getSentenceScore, shouldPrintToConsole):
    """ Finds the sentence that contains the most frequent lemmas, so the learner has a base of learned lemmas to start from. """
    
    maxLenghtSentence = 8 #Maxmium number of words allowed in the sentence.

    #Finding the sentence by a linear scan
    bestSentence = None
    bestSentenceScore = -1
    for sentence in textDatabase.allSentences.values():
        if hasCorrectLength(sentence):
            sentenceScore = 0
            for lemma in sentence.uncoveredLemmas:
                sentenceScore += lemma.getFrequency()
            if bestSentenceScore < sentenceScore:
                bestSentence = sentence
                bestSentenceScore = sentenceScore

    #Learning the lemmas in the sentence
    if bestSentence != None:
        if shouldPrintToConsole:
            print("Learned initial sentence -> " + bestSentence.rawSentence)
        markConjugationInSentenceAsLearned(bestSentence, sentenceAndLemmaScores.sentenceScores, getSentenceScore)
        lemmasToLearn = list(bestSentence.uncoveredLemmas) # Neccessary, as bestSentence.uncoveredLemmas is changed in the for loop below.
        for newLemma in lemmasToLearn:            
            orderedLearningList.append((newLemma, bestSentence))
            learnLemmaAndHandleSentencesWithLemmaFrequency(newLemma, notForcedToLearn, lemmasByFrequency, sentenceAndLemmaScores, getSentenceScore)            
            i = printLearnedLemma(i, newLemma, bestSentence.rawSentence, shouldPrintToConsole)
    return i

def getPriorityQueueOfDirectlyLearnableSentencesByLemmaScore(parser: TextParser, getSentenceScore) -> SentenceAndLemmaScores:
    sentenceScores = heapdict()
    directlyUnlockableLemmas= set()
    directlyUnlockableLemmasScore = None
    sentencePairsBySentenceScore = None #heapdict()
    sentenceAndLemmaScores = SentenceAndLemmaScores(sentenceScores, directlyUnlockableLemmasScore, sentencePairsBySentenceScore, directlyUnlockableLemmas)

    #This will make it so that non-words do not counts towards words in the sentences
    parser.NotASentence.initializeForAnalysis() 

    #First adding all the senteces that are directly learnable to the directly learnable list.
    for sentence in parser.allSentences.values():
        sentence.initializeForAnalysis()
        if isSentenceDirectlyUnlockable(sentence):
            unlockableLemma = sentence.getOnlyUncoveredLemma() 
            sentenceScores[sentence] = getSentenceScore(sentence).score 
            directlyUnlockableLemmas.add(unlockableLemma)

    return sentenceAndLemmaScores

def hasNoNewLemmas(sentencePair):
    return sentencePair[0].getNumberOfUncoveredLemmas() == 0

def getPriorityQueueOfLemmasByFrequency(textDatabase):
    mostFrequentLemmas = heapdict()
    for lemma in textDatabase.allLemmas.values():
        if isLemmaInRequiredTexts(lemma, textDatabase):
            mostFrequentLemmas[lemma] = -lemma.getFrequency()
    return mostFrequentLemmas

def addStemConjugationPair(wordToWordStem, wordStem, wordConjugation):
        if wordToWordStem.has_key(wordConjugation):
            listOfWordStems = wordToWordStem[wordConjugation]
            listOfWordStems.add(wordStem)
        else:
            wordToWordStem[wordConjugation] = {wordStem}

def hasLearnedAllLemmas(lemmasByFrequency):
    return len(lemmasByFrequency) == 0

def hasDirectlyLearnableSentence(unlockableSentences):
    can = len(unlockableSentences) != 0
    return can

def hasCorrectLength(sentence):
    return (minSentenceLength <= len(sentence.words) and len(sentence.words) <= maxSentenceLength)

def isSentenceEmpty(sentence):
    return sentence.getNumberOfUncoveredLemmas() == 0

def isSentenceDirectlyUnlockable(sentence):
    return sentence.getNumberOfUncoveredLemmas() == 1 and hasCorrectLength(sentence) # and onlyContainWordsFromGivenTexts(sentence) #The lenght should also be such that we actually want to learn the sentence

def isSecondaryUnlockable(sentence):
    return sentence.getNumberOfUncoveredLemmas() == 2 and hasCorrectLength(sentence)

def onlyContainWordsFromGivenTexts(sentence: Sentence):
    for word in sentence.words:
        lemma = word.getFirstLemma()
        if not isLemmaInRequiredTexts(lemma):
            return False
    return True

def isLemmaInRequiredTexts(lemma: Lemma, textDatabase): 

    textsToBeIn = [textDatabase.allTexts[textname] for textname in TEXTS_LEMMAS_NEEDS_TO_BE_IN]   
    
    for text in textsToBeIn:
        if (lemma not in text.lemmas):
            return False
    return True

def start():
    shouldResetSaveData = False
    shouldComputeLearningList = True
    loadTestText = True
    shouldPrintToConsole = True
    maxNumberOfLemmasToLearn = 12000
    textDatabase = TextParser()
    
    if shouldResetSaveData:
        if loadTestText:
            textDatabase.addAllTextsFromDirectoryToDatabase("Texts\\Test", shouldPrintToConsole)
            textDatabase.saveProcessedData(textDatabase.everything, "test")
        else:
            textDatabase.addAllTextsFromDirectoryToDatabase("Texts", shouldPrintToConsole)
            textDatabase.saveProcessedData(textDatabase.everything, "everything")
    if shouldComputeLearningList: 
        if loadTestText:
            test = textDatabase.loadProcessedData("test")
        else:            
            textDatabase.loadProcessedData("everything")     
        #printWordsInDatabase(textDatabase)
        learningList = learnLemmasByOrderOfScore(maxNumberOfLemmasToLearn, textDatabase, getSentenceScoreByConjugationFrequency, shouldPrintToConsole)
    print("done")


def testTest():
    simpleLemmatizer.initialize("lemma.en.txt")

def printWordsInDatabase(textDatabase: TextParser):
    rawLemmas = [lemma.rawLemma for lemma in textDatabase.allLemmas.values()]
    rawLemmas.sort()
    for i in range(0, min(len(rawLemmas),6000)):
        print(str(i) + ", " + rawLemmas[i])



#https://www.dictionary.com/browse/walked
#https://cran.r-project.org/web/packages/corpus/vignettes/stemmer.html
#https://github.com/michmech/lemmatization-lists/
#https://www.machinelearningplus.com/nlp/lemmatization-examples-python/
#https://www.nltk.org/book/ch07.html
#https://towardsdatascience.com/state-of-the-art-multilingual-lemmatization-f303e8ff1a8

#En masse corpuser: http://wortschatz.uni-leipzig.de/en/download/
#Engelsk corpus https://www.english-corpora.org/glowbe/

#Lemma database for different languages https://github.com/michmech/lemmatization-lists
