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
import stanfordnlp
#sys.stdout = codecs.getwriter('utf8')(sys.stdout)

missingWordFrequency = -100000000
minSentenceLength = 5
maxSentenceLength = 15
MAX_TIMES_LEARNED_WORD = 3
WORD_SCORING_MULTIPLIER = 2

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
        
def getHighestScoringDirectlyLearnableLemma(directlyUnlockableLemmasScore):
    return [directlyUnlockableLemmasScore.popitem()[0]]

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

def getSentenceScoreByLemmaFrequency(learnedSentence: Sentence) -> LemmaScore:    
    unlockedLemma = learnedSentence.getOnlyUncoveredLemma()
    return LemmaScore(-unlockedLemma.getFrequency(), None)


def getSentenceScoreByConjugationFrequency(learnedSentence: Sentence) -> LemmaScore:
    unlockedLemma = learnedSentence.getOnlyUncoveredLemma()
    totalConjugationFrequency = 0
    for word in set(learnedSentence.words):  
        if word.timesLearned < MAX_TIMES_LEARNED_WORD and word.lemmas[0].rawLemma != "NotALemma":
            learningModefier = (1/WORD_SCORING_MULTIPLIER)**(word.timesLearned+1)
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
        word.timesLearned += 1
        if word.timesLearned < MAX_TIMES_LEARNED_WORD:
            # There might be some sentences in the priorityqueue with a score that depends on this conjugation.
            # Their score therefore needs to be updated:
            for sentence in word.sentences.values():
                if isSentenceDirectlyUnlockable(sentence):                    
                    sentenceScores[sentence] = getSentenceScore(sentence).score 


def learnSentenceList(sentenceList, i, lemmasByFrequency, notForcedToLearn, orderedLearningList, sentenceAndLemmaScores: SentenceAndLemmaScores, getSentenceScore, shouldPrintToConsole):
    
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

def learnLemmasByOrderOfScore(maxNumberOfLemmasToLearn, textDatabase, getSentenceScore, shouldPrintToConsole):
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
        print("Number of directly learnable lemmas: " + str(len(sentenceAndLemmaScores.directlyUnlockableLemmas)))
    
    i = learnInitialSentence(textDatabase, i, lemmasByFrequency, unforcedWordLearningList, orderedLearningList, sentenceAndLemmaScores, getSentenceScore, shouldPrintToConsole)
    
    #TODO Obs. fejl i pointgivningen af sætninger, det ser ud til at den runder ned når den skal vælge imellem dem. Kommatal er derfor ligegyldigt?

    while (not hasLearnedAllLemmas(lemmasByFrequency)) and (i <= maxNumberOfLemmasToLearn or maxNumberOfLemmasToLearn == -1):
        if hasDirectlyLearnableSentence(sentenceAndLemmaScores.sentenceScores):
            #Chosing between to directly learnable lemmas, or one direcytly learnable lemma and a lemma it unlocks, based on the score:
            #currentSentencePair = getHighestScoringUnforcedSentencePair(sentenceAndLemmaScores.sentencePairsBySentenceScore, highestScoringDirectlyLearnableSentencePair, highestScoringDirectlyLearnableSentencePairScore)
            
            currentSentence = getHighestScoringDirectlyLearnableLemma(sentenceAndLemmaScores.sentenceScores)

            # No new word in the sentence:
            if hasNoNewLemmas(currentSentence):
                continue
            else:

                printAlternativeSentences(5, currentSentence, getSentenceScore, i, sentenceAndLemmaScores, shouldPrintToConsole)

                # A new pair of words to learn: lets do it!
                i = learnSentenceList(currentSentence, i, lemmasByFrequency, unforcedWordLearningList, orderedLearningList, sentenceAndLemmaScores, getSentenceScore, shouldPrintToConsole) 
        else: 
            # There are no more "free" words - time to learn a frequent word, without an associated sentence:
            i = learnMostFrequentLemma(i, lemmasByFrequency, forcedWordLearningList, orderedLearningList, sentenceAndLemmaScores, getSentenceScore, shouldPrintToConsole)
                
        if ((i < 2000 or i % 100 == 0) and False) and shouldPrintToConsole:
            print("Number of directly learnable lemmas: " + str(len(sentenceAndLemmaScores.directlyUnlockableLemmas)))
        if (i % 100 == 0 and False):
            printNumberOfCoveredSentences(shouldPrintToConsole, textDatabase)

    if shouldPrintToConsole:
        print("Learned directly " + str(len(unforcedWordLearningList)) + " of " + str(numberOfLemmas) + " lemmas.")
    

    lemmasLearned = set([lemmaSentencePair[0] for lemmaSentencePair in orderedLearningList])
    wordsWithLearnedLemmas = [word for word in  textDatabase.allWords.values() if (word.lemmas[0] in lemmasLearned) and word.lemmas[0] != textDatabase.NotAWordLemma]
    print("Number of conjugations of learned lemmas: " + str(len(wordsWithLearnedLemmas)))
    for i in range(0, 11):
        wordLearnedITimes = set()
        for word in wordsWithLearnedLemmas:
            if word.timesLearned == i:
                wordLearnedITimes.add(word)
        if shouldPrintToConsole:
            print("Number of words learned " + str(i) + " times: " + str(len(wordLearnedITimes)))

    print()
    
    for i in range(0, 11):
        lemmasLearnedITimes = set()
        for lemma in lemmasLearned:
            if lemma.getTimesLearned() == i:
                lemmasLearnedITimes.add(lemma)
        if shouldPrintToConsole:
            print("Number of lemmas learned " + str(i) + " times: " + str(len(lemmasLearnedITimes)))



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
    return sentence.getNumberOfUncoveredLemmas() == 1 and hasCorrectLength(sentence) #The lenght should also be such that we actually want to learn the sentence

def isSecondaryUnlockable(sentence):
    return sentence.getNumberOfUncoveredLemmas() == 2 and hasCorrectLength(sentence)

                        
#if __name__ == '__main__':
def start():
    shouldResetSaveData = False
    shouldComputeLearningList = True
    loadTestText = False
    shouldPrintToConsole = True
    maxNumberOfLemmasToLearn = 12000
    textDatabase = TextParser()



    if shouldResetSaveData:
        if loadTestText:
            textDatabase.addAllTextsFromDirectoryToDatabase("Texts/Test", shouldPrintToConsole)
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
        #print(len(learningList))
    #testTest()

    #Mulige forbedringer:
        #Bedre lemma classefier. 
        #Fjern navne og lignende. -> Nope, løsningen vil være for afhængigt af sproget der skal læres.
        #Hastighedsforbedinger. 
        #Scoring af sætninger, så der ses på forskellige bøjninger af et ord.
        #Split ord ved bindestreg
        #Mere aggresiv frasortering af sætninger.
    print("done")


def testStanford():    
    nlp = stanfordnlp.Pipeline() # This sets up a default neural pipeline in English
    #nlp = stanfordnlp.Pipeline(processors='tokenize,mwt,pos,lemma')
    doc = nlp("Barack Obama was born in Hawaii.")
    print(*[f'word: {word.text+" "}\tlemma: {word.lemma}' for sent in doc.sentences for word in sent.words], sep='\n')


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