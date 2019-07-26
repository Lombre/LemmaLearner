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
#sys.stdout = codecs.getwriter('utf8')(sys.stdout)

missingWordFrequency = -100000000
minSentenceLength = 5
maxSentenceLength = 15

class SentenceAndLemmaScores:
    """
        A simple class for storing a lot of lists, sets and priority queues, relating to sentences and lemmas, and their scores.
    """

    def __init__(self, directlyUnlockableLemmasScore, sentencePairsBySentenceScore, directlyUnlockableLemmas):
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

def getHighestScoringUnforcedSentencePair(sentencePairsBySentenceScore, highestScoringDirectlyLearnableSentencePair, highestScoringDirectlyLearnableSentencePairScore):
    highestScoreSentencePairScore = sentencePairsBySentenceScore.peekitem()[1]
    if highestScoreSentencePairScore < highestScoringDirectlyLearnableSentencePairScore:
        sentenceFromPair = sentencePairsBySentenceScore.popitem()[0]
        return (sentenceFromPair, sentenceFromPair.associatedLearnableSentence)
    else:
        return highestScoringDirectlyLearnableSentencePair

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

def getHighestScoringDirectlyLearnablePair(directlyUnlockableLemmasScore):
    if len(directlyUnlockableLemmasScore) == 0:
        return ((None, None), -missingWordFrequency)
    else:
        highestScoringLemma = directlyUnlockableLemmasScore.popitem()[0]
        if len(directlyUnlockableLemmasScore) == 0:
            directlyUnlockableLemmasScore[highestScoringLemma] = -highestScoringLemma.getFrequency()
            return ((highestScoringLemma.getDirectlyUnlockingSentence(isSentenceDirectlyUnlockable), None), -highestScoringLemma.getFrequency())
        else:
            nextHighestScoringLemma = directlyUnlockableLemmasScore.popitem()[0]
            #We don't want to actually delete the sentences from the priority queue, so we place them back after use:
            directlyUnlockableLemmasScore[nextHighestScoringLemma] = -nextHighestScoringLemma.getFrequency()
            directlyUnlockableLemmasScore[highestScoringLemma] = -highestScoringLemma.getFrequency()
            return ( (highestScoringLemma.getDirectlyUnlockingSentence(isSentenceDirectlyUnlockable), nextHighestScoringLemma.getDirectlyUnlockingSentence(isSentenceDirectlyUnlockable)) , 
                    -highestScoringLemma.getFrequency() + -nextHighestScoringLemma.getFrequency())

def getSentenceScoreByNextUnlockableLemma(learnedSentence: Sentence, directlyUnlockableLemmas) -> LemmaScore:

    unlockedLemma = learnedSentence.getOnlyUncoveredLemma()
    maxFrequencyUnlocked = 0
    maxFrequencySentence = None

    sentences = unlockedLemma.getSentences()
    for sentence in sentences:
        if isSecondaryUnlockable(sentence): #Learning unlockedLemma might unlock a new word in this sentence:     

            unlockedLemmas = list(sentence.uncoveredLemmas) #Contains two lemmas: unlockedLemma and a new lemma.
            newUnlockedLemma = unlockedLemmas[1] if (unlockedLemmas[0] == unlockedLemma) else unlockedLemmas[0]

            if newUnlockedLemma not in directlyUnlockableLemmas: #Now we know it is definetly a lemma that hasn't been learned before
                if maxFrequencyUnlocked <  newUnlockedLemma.getFrequency():
                    maxFrequencyUnlocked = newUnlockedLemma.getFrequency()
                    maxFrequencySentence = sentence
            else:
                #TODO Her mangler der at håndretes et case
                continue

    return LemmaScore(-unlockedLemma.getFrequency() - maxFrequencyUnlocked, maxFrequencySentence)

def getSentenceScoreAsLemmaFrequency(sentence):
    return sentence.getOnlyUncoveredLemma().getFrequency()

def learnLemmaAndHandleSentencesWithLemmaFrequency(newLemma: Lemma, learningList, lemmaQueue, sentenceAndLemmaScores: SentenceAndLemmaScores, getSentenceScore):
    learningList.append(newLemma)
    #It is learned - new sentences become available and ready for learning:
    newLemma.coverSentences()
    lemmaQueue.pop(newLemma)
    if newLemma in sentenceAndLemmaScores.directlyUnlockableLemmas:
        sentenceAndLemmaScores.directlyUnlockableLemmas.remove(newLemma)
        sentenceAndLemmaScores.directlyUnlockableLemmasScore.pop(newLemma)

    lemmaSentences = newLemma.getSentences()
    #Finds all words that now has become unlockable
    for sentence in lemmaSentences:
        if isSentenceDirectlyUnlockable(sentence):
            unlockedLemma = sentence.getOnlyUncoveredLemma()
            sentenceAndLemmaScores.directlyUnlockableLemmas.add(unlockedLemma)
            sentenceAndLemmaScores.directlyUnlockableLemmasScore[unlockedLemma] = -unlockedLemma.getFrequency()

    #Scores all the sentences, especially those with newly unlockable words
    for sentence in lemmaSentences:
        addSentencePairWithScore(sentence, sentenceAndLemmaScores, getSentenceScore)

def printLearnedLemma(i, newLemma, rawSentence, shouldPrintToConsole):
    if (i < 2000 or i % 100 == 0) and shouldPrintToConsole:
        print(str(i) + ", " + newLemma.getRawLemma() + ", " + str(newLemma.getFrequency()) + " -> " + rawSentence)
    i += 1
    return i

def learnSentencePair(sentencePairToLearn, i, lemmasByFrequency, notForcedToLearn, orderedLearningList, sentenceAndLemmaScores: SentenceAndLemmaScores, getSentenceScore, shouldPrintToConsole):
    
    #TODO (*) Der mangler at blive fjernet en fejl i forbindelse med at opdaterer sætninger, hvis sentence score afhænger af andre sætninger.
    for sentence in sentencePairToLearn:
        if sentence == None:
            continue
        if sentence.associatedLearnableSentence != None:
            #As the sentence will be learned, it is removed as a score dependent sentence.
            sentence.associatedLearnableSentence.scoreDependentSentences.remove(sentence)
                
        newLemma = sentence.getOnlyUncoveredLemma()
        orderedLearningList.append((newLemma, sentence))
        i = printLearnedLemma(i, newLemma, sentence.rawSentence, shouldPrintToConsole)
        learnLemmaAndHandleSentencesWithLemmaFrequency(newLemma, notForcedToLearn, lemmasByFrequency, sentenceAndLemmaScores, getSentenceScore)            
    return i

def learnMostFrequentLemma(i, lemmasByFrequency, forcedWordLearningList, orderedLearningList, sentenceAndLemmaScores: SentenceAndLemmaScores, getSentenceScore, shouldPrintToConsole):
    newLemma = getHighestScoringLemma(lemmasByFrequency)
    orderedLearningList.append((newLemma, None))
    learnLemmaAndHandleSentencesWithLemmaFrequency(newLemma, forcedWordLearningList, lemmasByFrequency, sentenceAndLemmaScores, getSentenceScore)            
    i = printLearnedLemma(i, newLemma, "NONE", shouldPrintToConsole)
    return i

def learnLemmasByOrderOfScore(textDatabase, getSentenceScore, shouldPrintToConsole):
    # Scheme: Learn words as they become possible to learn, in terms of sentences, in order of score

    # Initialize everything, including the sentences
    textDatabase.initialize()
    
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
    numberOfLemmas = len(lemmasByFrequency)
    if shouldPrintToConsole:
        print("Start learning lemmas: " + str(len(lemmasByFrequency)))
    
    i = learnInitialSentence(textDatabase, i, lemmasByFrequency, unforcedWordLearningList, orderedLearningList, sentenceAndLemmaScores, getSentenceScore, shouldPrintToConsole)

    (highestScoringDirectlyLearnableSentencePair, highestScoringDirectlyLearnableSentencePairScore) = getHighestScoringDirectlyLearnablePair(sentenceAndLemmaScores.directlyUnlockableLemmasScore)
    while not hasLearnedAllLemmas(lemmasByFrequency):
        if hasDirectlyLearnableSentence(sentenceAndLemmaScores.directlyUnlockableLemmas):
            currentSentencePair = getHighestScoringUnforcedSentencePair(sentenceAndLemmaScores.sentencePairsBySentenceScore, highestScoringDirectlyLearnableSentencePair, highestScoringDirectlyLearnableSentencePairScore)
            # No new word in the sentence:
            if hasNoNewLemmas(currentSentencePair):
                continue
            else:
                # A new pair of words to learn: lets do it!
                i = learnSentencePair(currentSentencePair, i, lemmasByFrequency, unforcedWordLearningList, orderedLearningList, sentenceAndLemmaScores, getSentenceScore, shouldPrintToConsole) 
        else: 
            # There are no more "free" words - time to learn a frequent word, without an associated sentence:
            i = learnMostFrequentLemma(i, lemmasByFrequency, forcedWordLearningList, orderedLearningList, sentenceAndLemmaScores, getSentenceScore, shouldPrintToConsole)
        (highestScoringDirectlyLearnableSentencePair, highestScoringDirectlyLearnableSentencePairScore) = getHighestScoringDirectlyLearnablePair(sentenceAndLemmaScores.directlyUnlockableLemmasScore)
    
    if shouldPrintToConsole:
        print("Learned directly " + str(len(unforcedWordLearningList)) + " of " + str(numberOfLemmas) + " lemmas.")
    return orderedLearningList

def learnInitialSentence(textDatabase: TextParser, i,  lemmasByFrequency, notForcedToLearn, orderedLearningList, sentenceAndLemmaScores: SentenceAndLemmaScores, getSentenceScore, shouldPrintToConsole):
    """ Finds the sentence that contains the most frequent lemmas, so the learner has a base of learned lemmas to start from. """
    
    maxLenghtSentence = 8 #Maxmium number of words allowed in the sentence.

    #Finding the sentence by a linear scan
    bestSentence = None
    bestSentenceScore = -1
    for sentence in textDatabase.allSentences.values():
        if len(sentence.words) <= maxLenghtSentence:
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
        lemmasToLearn = list(bestSentence.uncoveredLemmas) # Neccessary, as bestSentence.uncoveredLemmas is changed in the for loop below.
        for newLemma in lemmasToLearn:
            learnLemmaAndHandleSentencesWithLemmaFrequency(newLemma, notForcedToLearn, lemmasByFrequency, sentenceAndLemmaScores, getSentenceScore)            
            i = printLearnedLemma(i, newLemma, bestSentence.rawSentence, shouldPrintToConsole)
    return i


def addSentencePairWithScore(sentence: Sentence, sentenceAndLemmaScores: SentenceAndLemmaScores, getSentenceScore):
    if isSentenceEmpty(sentence):
        #We do not care much for empty sentences
        sentence.associatedLearnableSentence = None
        sentenceAndLemmaScores.sentencePairsBySentenceScore[sentence] = missingWordFrequency
    elif isSentenceDirectlyUnlockable(sentence):
        #If the sentence is directly unlockable,
        #learning the sentence might unlock new learnable lemmas.
        #This is taken into account below.
        
        lemmaScore = getSentenceScore(sentence, sentenceAndLemmaScores.directlyUnlockableLemmas)
        sentenceAndLemmaScores.sentencePairsBySentenceScore[sentence] = lemmaScore.score        

        #Necessary for some cleanup later, when nextSentence becomes learnable, see below
        sentence.associatedLearnableSentence = lemmaScore.nextSentence
        if lemmaScore.nextSentence != None:
            lemmaScore.nextSentence.scoreDependentSentences.add(sentence)
        
        #There are some sentences whose score depends on the sentence becoming unlockable when they are learned.
        #They are rescored.
        for scoreDependentSentence in sentence.scoreDependentSentences:
            if scoreDependentSentence not in sentenceAndLemmaScores.sentencePairsBySentenceScore:
                continue
            sentenceAndLemmaScores.sentencePairsBySentenceScore.pop(scoreDependentSentence)
            #No infinite recursion because sentence.scoreDependentSentences is cleared afterwards. This can only go one step deeper.
            addSentencePairWithScore(scoreDependentSentence, sentenceAndLemmaScores, getSentenceScore)
        sentence.scoreDependentSentences.clear()


def getPriorityQueueOfDirectlyLearnableSentencesByLemmaScore(parser: TextParser, getSentenceScore) -> SentenceAndLemmaScores:
    directlyUnlockableLemmas= set()
    directlyUnlockableLemmasScore = heapdict()
    sentencePairsBySentenceScore = heapdict()
    sentenceAndLemmaScores = SentenceAndLemmaScores(directlyUnlockableLemmasScore, sentencePairsBySentenceScore, directlyUnlockableLemmas)

    #This will make it so that non-words do not counts towards words in the sentences
    parser.NotASentence.initializeForAnalysis() 

    #First adding all the senteces that are directly learnable to the directly learnable list.
    for sentence in parser.allSentences.values():
        sentence.initializeForAnalysis()
        if isSentenceDirectlyUnlockable(sentence):
            unlockableLemma = sentence.getOnlyUncoveredLemma() 
            directlyUnlockableLemmasScore[unlockableLemma] = -unlockableLemma.getFrequency()
            directlyUnlockableLemmas.add(unlockableLemma)

    # This is not done above, 
    # as it requires directlyUnlockableLemmas to be filled with all the directly unlockable lemmas
    for sentence in parser.allSentences.values():            
        addSentencePairWithScore(sentence, sentenceAndLemmaScores, getSentenceScore) 

    return sentenceAndLemmaScores

def hasNoNewLemmas(sentencePair):
    return sentencePair[0].getNumberOfUncoveredLemmas() == 0

def getPriorityQueueOfLemmasByFrequency(textDatabase):
    mostFrequentLemmas = heapdict()
    for lemma in textDatabase.allLemmas.values():
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

def hasDirectlyLearnableSentence(directlyUnlockableLemmas):
    can = len(directlyUnlockableLemmas) != 0
    return can

def hasCorrectLength(sentence):
    return (minSentenceLength <= len(sentence.words) and len(sentence.words) <= maxSentenceLength)

def isSentenceEmpty(sentence):
    return sentence.getNumberOfUncoveredLemmas() == 0

def isSentenceDirectlyUnlockable(sentence):
    return sentence.getNumberOfUncoveredLemmas() == 1 and hasCorrectLength(sentence) #The lenght should also be such that we actually want to learn the sentence

def isSecondaryUnlockable(sentence):
    return sentence.getNumberOfUncoveredLemmas() == 2 and hasCorrectLength(sentence)

                        
#if __name__ == '__main__':
def start():
    shouldResetSaveData = False
    loadTestText = False
    shouldPrintToConsole = True
    textDatabase = TextParser()
    if shouldResetSaveData:
        if loadTestText:
            textDatabase.addAllTextsFromDirectoryToDatabase("Texts/Test", shouldPrintToConsole)
            textDatabase.saveProcessedData(textDatabase.everything, "test")
        else:
            textDatabase.addAllTextsFromDirectoryToDatabase("Texts", shouldPrintToConsole)
            textDatabase.saveProcessedData(textDatabase.everything, "everything")
    else: 
        if loadTestText:
            test = textDatabase.loadProcessedData("test")
        else:            
            textDatabase.loadProcessedData("everything")        
        learningList = learnLemmasByOrderOfScore(textDatabase, getSentenceScoreByNextUnlockableLemma, shouldPrintToConsole)
        print(len(learningList))

    #Mulige forbedringer:
        #Bedre lemma classefier. Der er f.eks. mange -ed bøjninger der bliver klassificeret som sit eget ord. Kan nok fjerne 1/10 til 1/20 af alle lemaer.
        #Fjern navne og lignende.
        #Hastighedsforbedinger. 
        #Fjern meget korte sætninger, og meget lange sætninger.
        #Håndtering af "" i sætninger.
        #Scoring af sætninger, så der ses på forskellige bøjninger af et ord.
        #Split ord ved bindestreg



    print("done")

#https://www.dictionary.com/browse/walked
#https://cran.r-project.org/web/packages/corpus/vignettes/stemmer.html
#https://github.com/michmech/lemmatization-lists/
#https://www.machinelearningplus.com/nlp/lemmatization-examples-python/
#https://www.nltk.org/book/ch07.html
