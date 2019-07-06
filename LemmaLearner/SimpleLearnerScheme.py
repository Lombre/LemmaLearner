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

class LemmaScore:

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

def getHighestScoringDirectlyLearnablePair(directlyUnlockableLemmasScore, sentencePairsBySentenceScore):
    if len(directlyUnlockableLemmasScore) == 0:
        return ((None, None), -missingWordFrequency)
    else:
        highestScoringLemma = directlyUnlockableLemmasScore.popitem()[0]
        if len(directlyUnlockableLemmasScore) == 0:
            directlyUnlockableLemmasScore[highestScoringLemma] = -highestScoringLemma.getFrequency()
            return ((highestScoringLemma.getDirectlyUnlockingSentence(), None), -highestScoringLemma.getFrequency())
        else:
            nextHighestScoringLemma = directlyUnlockableLemmasScore.popitem()[0]
            #We don't want to actually delete the sentences from the priority queue, so we place them back after use:
            directlyUnlockableLemmasScore[nextHighestScoringLemma] = -nextHighestScoringLemma.getFrequency()
            directlyUnlockableLemmasScore[highestScoringLemma] = -highestScoringLemma.getFrequency()
            return ( (highestScoringLemma.getDirectlyUnlockingSentence(), nextHighestScoringLemma.getDirectlyUnlockingSentence()) , -highestScoringLemma.getFrequency() + -nextHighestScoringLemma.getFrequency())

def  getSentenceScoreByNextUnlockableLemma(learnedSentence, directlyUnlockableLemmas):
    # Teknisk set ikke helt korrekt metode, da den tjekker det bedste par af to ord man kan lære,
    # men ikke tvinger en til at lære de ord lige efter hinanden:
    # så bliver de nogen gange ikke valgt lige efter hinanden, og det er dermed ikke et optimalt par.
    # Man skal være meget præcist for at få det helt korrekt, hvilket jeg ikke gider at være lige nu!

    unlockedLemma = learnedSentence.getOnlyUncoveredLemma()
    maxFrequencyUnlocked = 0
    maxFrequencySentence = None

    if True:
        sentences = unlockedLemma.getSentences()
        for sentence in sentences:
            if sentence.getNumberOfUncoveredLemmas() == 2: #Learning unlockedLemma might unlock a new word in this sentence:
                unlockedLemmas = list(sentence.uncoveredLemmas)
                newUnlockedLemma = unlockedLemmas[1] if (unlockedLemmas[0] == unlockedLemma) else unlockedLemmas[0]
                if newUnlockedLemma not in directlyUnlockableLemmas: #Now we know it definetly will unlock a new word!
                    if maxFrequencyUnlocked <  newUnlockedLemma.getFrequency():
                        maxFrequencyUnlocked = newUnlockedLemma.getFrequency()
                        maxFrequencySentence = sentence
                else:
                    #TODO Her mangler der at håndretes et case
                    continue

    return LemmaScore(-unlockedLemma.getFrequency() - maxFrequencyUnlocked, maxFrequencySentence)

def getSentenceScoreAsLemmaFrequency(sentence):
    return sentence.getOnlyUncoveredLemma().getFrequency()

def learnLemmaAndHandleSentencesWithLemmaFrequency(newLemma, wordList, sentencePairsBySentenceScore, lemmaQueue, directlyUnlockableLemmasScore, directlyUnlockableLemmas, getSentenceScore):
    wordList.append(newLemma)
    #It is learned: new sentences become available:
    newLemma.coverSentences()
    lemmaQueue.pop(newLemma)
    if newLemma in directlyUnlockableLemmas:
        directlyUnlockableLemmas.remove(newLemma)
        directlyUnlockableLemmasScore.pop(newLemma)

    lemmaSentences = newLemma.getSentences()
    #Finds all words that now has become unlockable
    for sentence in lemmaSentences:
        if sentence.getNumberOfUncoveredLemmas() == 1:
            unlockedLemma = sentence.getOnlyUncoveredLemma()
            directlyUnlockableLemmas.add(unlockedLemma)
            directlyUnlockableLemmasScore[unlockedLemma] = -unlockedLemma.getFrequency()

    #Scores all the sentences, especially those with newly unlockable words
    for sentence in lemmaSentences:
        addSentenceWithScore(directlyUnlockableLemmas, getSentenceScore, sentence, sentencePairsBySentenceScore)

def learnSentencePair(currentSentencePair, getSentenceScore, i, lemmasByFrequency, notForcedToLearn, orderedLearningList, sentencePairsBySentenceScore, directlyUnlockableLemmasScore, directlyUnlockableLemmas, shouldPrintToConsole):
    
   #TODO (*) Der mangler at blive fjernet en fejl i forbindelse med at opdaterer sætninger, hvis sentence score afhænger af andre sætninger.
    for sentence in currentSentencePair:
        if sentence == None:
            continue
        if sentence.associatedLearnableSentence != None:
            sentence.associatedLearnableSentence.scoreDependentSentences.remove(sentence)
    
        newLemma = sentence.getOnlyUncoveredLemma()
        orderedLearningList.append((newLemma, sentence))
        learnLemmaAndHandleSentencesWithLemmaFrequency(newLemma, notForcedToLearn, sentencePairsBySentenceScore, lemmasByFrequency, directlyUnlockableLemmasScore, directlyUnlockableLemmas, getSentenceScore)            
        if (i < 2000 or i % 100 == 0) and shouldPrintToConsole:
            print(str(i) + ", " + newLemma.getRawLemma() + ", " + str(newLemma.getFrequency()) + " -> " + sentence.rawSentence)
        i += 1
    return i

def learnMostFrequentLemma(forcedToLearn, getSentenceScore, i, lemmasByFrequency, orderedLearningList, sentencePairsBySentenceScore, directlyUnlockableLemmasScore, directlyUnlockableLemmas, shouldPrintToConsole):
    newLemma = getHighestScoringLemma(lemmasByFrequency)
    orderedLearningList.append((newLemma, None))
    learnLemmaAndHandleSentencesWithLemmaFrequency(newLemma, forcedToLearn, sentencePairsBySentenceScore, lemmasByFrequency, directlyUnlockableLemmasScore, directlyUnlockableLemmas, getSentenceScore)            
    if (i < 2000 or i % 100 == 0) and shouldPrintToConsole:
        print(str(i) + ", " + newLemma.getRawLemma() + ", " + str(newLemma.getFrequency()) + " -> " + "NONE")
    i += 1
    return i

def learnLemmasByOrderOfScore(textDatabase, getSentenceScore, shouldPrintToConsole):
    # Scheme: Learn words as they become possible to learn, in terms of sentences, in order of score

    # Initialize everything, including the sentences
    textDatabase.initialize()

    # Will only contain sentences with fewer than or equal to one missing word, marked in order of the missing words frequency
    directlyUnlockableLemmasScore, sentencePairsBySentenceScore, directlyUnlockableLemmas = getPriorityQueueOfDirectlyLearnableSentencesByLemmaFrequency(textDatabase, getSentenceScore)
    lemmasByFrequency = getPriorityQueueOfLemmasByFrequency(textDatabase)

    # Find which words one is forced to learn, without being able to isolate it to one sentence:
    forcedToLearn = []
    notForcedToLearn = []
    orderedLearningList = []
    #First we remove all words that are not true "words", for example names, by learning the NotAWordLemma lemma:
    learnLemmaAndHandleSentencesWithLemmaFrequency(textDatabase.NotAWordLemma, notForcedToLearn, sentencePairsBySentenceScore, lemmasByFrequency, directlyUnlockableLemmasScore, directlyUnlockableLemmas, getSentenceScore)

    i = 0
    numberOfLemmas = len(lemmasByFrequency)
    if shouldPrintToConsole:
        print("Start learning lemmas: " + str(len(lemmasByFrequency)))

    (highestScoringDirectlyLearnableSentencePair, highestScoringDirectlyLearnableSentencePairScore) = getHighestScoringDirectlyLearnablePair(directlyUnlockableLemmasScore, sentencePairsBySentenceScore)
    while not hasLearnedAllLemmas(lemmasByFrequency):
        if hasDirectlyLearnableSentence(directlyUnlockableLemmas):
            currentSentencePair = getHighestScoringUnforcedSentencePair(sentencePairsBySentenceScore, highestScoringDirectlyLearnableSentencePair, highestScoringDirectlyLearnableSentencePairScore)
            # No new word in the sentence:
            if hasNoNewLemmas(currentSentencePair):
                continue
            else:
                # A new pair of words to learn: lets do it!
                i = learnSentencePair(currentSentencePair, getSentenceScore, i, lemmasByFrequency, notForcedToLearn, orderedLearningList, sentencePairsBySentenceScore, directlyUnlockableLemmasScore, directlyUnlockableLemmas, shouldPrintToConsole) 
        else: 
            # There are no more free words: time to learn a frequent word:
            i = learnMostFrequentLemma(forcedToLearn, getSentenceScore, i, lemmasByFrequency, orderedLearningList, sentencePairsBySentenceScore, directlyUnlockableLemmasScore, directlyUnlockableLemmas, shouldPrintToConsole)
        (highestScoringDirectlyLearnableSentencePair, highestScoringDirectlyLearnableSentencePairScore) = getHighestScoringDirectlyLearnablePair(directlyUnlockableLemmasScore, sentencePairsBySentenceScore)
    if shouldPrintToConsole:
        print("Learned directly " + str(len(notForcedToLearn)) + " of " + str(numberOfLemmas) + " lemmas.")
    return orderedLearningList

def addSentenceWithScore(directlyUnlockableLemmas, getSentenceScore, sentence, sentencePairsBySentenceScore):
    if sentence.getNumberOfUncoveredLemmas() == 0:
        sentence.associatedLearnableSentence = None
        sentencePairsBySentenceScore[sentence] = missingWordFrequency
    elif sentence.getNumberOfUncoveredLemmas() == 1:
        lemmaScore = getSentenceScore(sentence, directlyUnlockableLemmas)
        sentence.associatedLearnableSentence = lemmaScore.nextSentence
        if lemmaScore.nextSentence != None:
            lemmaScore.nextSentence.scoreDependentSentences.add(sentence)
        sentencePairsBySentenceScore[sentence] = lemmaScore.score
        

        for scoreDependentSentence in sentence.scoreDependentSentences:
            if scoreDependentSentence not in sentencePairsBySentenceScore:
                k  = 1
            sentencePairsBySentenceScore.pop(scoreDependentSentence)
            #No infinite recursion because sentence.scoreDependentSentences is cleared afterwards. This can only go one step deeper.
            addSentenceWithScore(directlyUnlockableLemmas, getSentenceScore, scoreDependentSentence, sentencePairsBySentenceScore)
        sentence.scoreDependentSentences.clear()
    
def getPriorityQueueOfDirectlyLearnableSentencesByLemmaFrequency(parser, getSentenceScore):
    directlyUnlockableLemmas= set()
    directlyUnlockableLemmasScore = heapdict()
    sentencePairsBySentenceScore = heapdict()
    parser.NotASentence.initializeForAnalysis()
    for sentence in parser.allSentences.values():
        sentence.initializeForAnalysis()
        if sentence.getNumberOfUncoveredLemmas() == 1:
            unlockableLemma = sentence.getOnlyUncoveredLemma() 
            directlyUnlockableLemmasScore[unlockableLemma] = -unlockableLemma.getFrequency()
            directlyUnlockableLemmas.add(unlockableLemma)

    for sentence in parser.allSentences.values():            
        addSentenceWithScore(directlyUnlockableLemmas, getSentenceScore, sentence, sentencePairsBySentenceScore) 

    return directlyUnlockableLemmasScore, sentencePairsBySentenceScore, directlyUnlockableLemmas

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
