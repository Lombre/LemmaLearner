# -*- coding: utf-8 -*-
from Word import Word
import nltk
import re
import string

compoundWordPattern = re.compile(u'.*(-|­—|_­}).*')
extraPunctuation = u"…"
REAL_WORD_TAG = "REAL_WORD"


def isCompoundWord(word):
    return compoundWordPattern.match(word)

def shouldIgnore(rawWord):
    return not (1 < len(rawWord) and rawWord[0] != "`" and rawWord[0] != "'") #or isCompoundWord(rawWord) #I don't care much for compound words


def cleanWord(rawWord):
    return re.sub('[' + string.punctuation + extraPunctuation + ']', '', rawWord).lower()


class Sentence:

    def __init__(self, originText, rawSentence):

        self.text = originText
        self.rawSentence = rawSentence
        cleanSentence = self.cleanRawSentence(rawSentence)
        rawWords = nltk.word_tokenize(cleanSentence)
        rawWords = self.splitCompoundWords(rawWords)
        self.words = self.exstractWords(rawWords)
        self.uncoveredWords = set() #All the words found in the sentence, that haven't been learned yet. Must be initialized.
        self.uncoveredLemmas = set() #Same as above, but with lemmas.

        #For use later, when actually learning the words.
        self.associatedLearnableSentence = None
        self.scoreDependentSentences = set()
        #self.wordsToTags = self.getWordsToTags(rawWords) #It maps a word to a set of POS tags, as a specific word might have more than one pos tag.
        
    def exstractWords(self, rawWords):
        words = []
        for rawWord in rawWords:
            #Ignores word if 1 => length, as it is probably just something like a comma, a single character or \":
            if not shouldIgnore(rawWord):
                word = cleanWord(rawWord)
                if 0 < len(word):
                    words.append(Word(word.lower(), self))
        return words

    def splitCompoundWords(self, rawWords):
        splitRawWords = []
        for rawWord in rawWords:
            splitWords = re.split("-|—|_| de", rawWord) #("-|—")

            for splitWord in splitWords:
                if splitWord != "" and splitWord != " ":
                    splitRawWords.append(splitWord)
        return splitRawWords
    
    def initializeForAnalysis(self):
        #Reseting:
        self.uncoveredWords = set()
        self.uncoveredLemmas = set()
        if self.rawSentence == 'Every shade of colour they were—straw, lemon, orange, brick, Irish-setter, liver, clay; but, as Spaulding said, there were not many who had the real vivid flame-coloured tint.':
            k=1
        #Initializing
        for word in self.words:
            self.uncoveredWords.add(word)
            for lemma in word.lemmas:
                self.uncoveredLemmas.add(lemma)
        if len(self.uncoveredLemmas) == 0:
            k = 1

    def rescoreScoreDependentSentences(getSentenceScore):
        return None

    def getNumberOfUncoveredWords(self):
        return len(self.uncoveredWords)

    def getNumberOfUncoveredLemmas(self):
        return len(self.uncoveredLemmas)

    def getOnlyUncoveredLemma(self):
        if self.getNumberOfUncoveredLemmas() != 1:
            raise Exception("There are " + str(self.getNumberOfUncoveredLemmas()) + " uncovered lemmas, not 1.")
        elif list(self.uncoveredLemmas)[0] == None:
            raise Exception("A word does not contain a lemma")
        else:
            #Faster than: list(self.uncoveredLemmas)[0]
            for uncoveredLemma in self.uncoveredLemmas:
                return uncoveredLemma

    def recoverWords(self, allWords):
        for i in range(0, len(self.words)):
            #Ensuring that the word's associated sentence points to this sentence.
            self.words[i].sentences[self.rawSentence] = self

    
    def getWordsToTags(self, rawWords):   
        wordsToTags = {}
        #Every words initally have no tags:
        for rawWord in rawWords:
            wordsToTags[cleanWord(rawWord)] = set()

        wordChunks = nltk.ne_chunk(nltk.pos_tag(rawWords))
        for chunk in wordChunks:
            if hasattr(chunk,'_label'): #chunk contains one or more special words, like a name.
                for leaf in chunk.leaves():
                    word = cleanWord(leaf[0])
                    wordsToTags[word].add(chunk._label)
            else: 
                word = cleanWord(chunk[0])
                wordsToTags[word].add("REAL_WORD")
        return wordsToTags
        
    def __str__(self):
        return self.rawSentence

       
    def getRealWordTag():
        return REAL_WORD_TAG

    def cleanRawSentence(self, rawSentence):
        cleanSentence = (rawSentence.replace('\\', " "))
        return cleanSentence