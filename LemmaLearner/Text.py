# -*- coding: utf-8 -*-
from Sentence import Sentence
import nltk
import re
from timeit import default_timer as timer
import SimpleLearnerScheme
#def splitSentences(rawText):
#    #There are two types of splitting that

#    #Matches a string consist of some normal text,
#    #followed by repeadtly matching (text in quotes like “kage er godt,” followed by normal text) -> notice that “kage er godt.” is not accepted
#    #with everything finally ending with a “Det er lagkage ogsaa.”
#    sentencePattern = ur'.*?\.' #ur'.*?(“.*?(?!.”)”.*?)*(\.+“.*?”)' 
#    in_quotes = re.findall(sentencePattern, rawText)
#    return in_quotes

class Text:

    #https://stackoverflow.com/questions/31046831/regex-to-capture-sentences-with-quotes
    def __init__(self, rawText, name, textDatabase, shouldRemoveUnlearnableSentences):
        self.rawText = rawText #self.formatText(rawText)
        self.name = name
        textDatabase.allTexts[self.name] = self
        self.sentences = self.exstractSentences(rawText, textDatabase, shouldRemoveUnlearnableSentences)
        self.lemmas = self.extractLemmas(self.sentences)

    def formatText(self, rawText):
        return  rawText.replace(u"\u2018", "'").replace(u"\u2019", "'").replace(u"\xa9", "e").replace(u"\u2014","-").decode("utf8")


    def splitIntoRawSentences(self, paragraphs):
        mission = "Split at punctuation: "
        startTime = timer() 
        print(mission + str(round(0/len(paragraphs)*100, 1)) + "% done.")
        splitAtPunctuation = []
        for i in range(0, len(paragraphs)):
            paragraph = paragraphs[i]
            splitAtPunctuation.append(self.splitAtPunctuation(paragraph))
            if startTime + 5 < timer():
                print(mission + str(round(i/len(paragraphs)*100, 1)) + "% done.")
                startTime = timer()
        print(mission + str(round(len(paragraphs)/len(paragraphs)*100, 1)) + "% done.")
        print()
        rawSentences = self.flatten(splitAtPunctuation)

        return rawSentences

    def removeUnlearnableSentences(self, textDatabase, shouldRemoveUnlearnableSentences):
        for sentence in self.sentences:
            textDatabase.removeSentenceIfUnlearnable(sentence, shouldRemoveUnlearnableSentences)
    

    def removeDanglingQuotations(self, rawSentence):
        quotationPair = {"\"": "\"", "“": "”", "”": "“"}
        #print(rawSentence)
        #if (rawSentence[0] in quotationPair):
        #    print(quotationPair[rawSentence[0]])
        if (rawSentence[0] in quotationPair and (not quotationPair[rawSentence[0]] in rawSentence[1:len(rawSentence)]) and 1 < len(rawSentence)):
            rawSentence = rawSentence[1:len(rawSentence)]
        elif (rawSentence[len(rawSentence)-1] in quotationPair and (not quotationPair[rawSentence[len(rawSentence)-1]] in rawSentence[0:len(rawSentence)-1]) and 1 < len(rawSentence)):                
            rawSentence = rawSentence[0:len(rawSentence)-1]
        return rawSentence

    def convertRawSentencesIntoSentences(self, rawSentences, textDatabase, shouldRemoveUnlearnableSentences):
        cleanSentences = []                
        startTime = timer()        
        print("Sentence splitting: " + str(round(0/len(rawSentences)*100, 1)) + "% done.")
        for i in range(0, len(rawSentences)):
            rawSentence = rawSentences[i]
            rawSentence = self.removeDanglingQuotations(rawSentence)
            sentence = Sentence(self, rawSentence, textDatabase)
            textDatabase.addSentenceToDatabase(sentence)
            #if (shouldRemoveUnlearnableSentences and textDatabase.isUnlearnableSentence(sentence)):
            #    #This needs to be here, as creating a sentence is not a pure function.
            #    textDatabase.removeSentenceFromDatabase(sentence)
            #    continue
            cleanSentences.append(sentence)
            if startTime + 5 < timer():
                print("Sentence splitting: " + str(round(i/len(rawSentences)*100, 1)) + "% done.")
                startTime = timer()
        print("Sentence splitting: " + str(round(len(rawSentences)/len(rawSentences)*100, 1)) + "% done.")
        return cleanSentences


    def splitIntoParagraphs(self, rawText):
        return [s.strip() for s in rawText.splitlines()]

    def exstractSentences(self, rawText, textDatabase, shouldRemoveUnlearnableSentences):   
        cleanText = self.cleanTextOfWeirdCharacters(rawText)
        paragraphs = self.splitIntoParagraphs(cleanText)
        rawSentences = self.splitIntoRawSentences(paragraphs)
        cleanSentences = self.convertRawSentencesIntoSentences(rawSentences, textDatabase, shouldRemoveUnlearnableSentences)

        return cleanSentences

    def extractLemmas(self, sentences):
        allLemmas = set()
        for sentence in sentences:
            for word in sentence.words:
                allLemmas.add(word.getFirstLemma())
        return allLemmas


    def cleanTextOfWeirdCharacters(self, rawText):
        cleanText = rawText.replace("\u2060", "").replace("\xad", "")
        return cleanText

    def flatten(self, input):
        if isinstance(input, list):
            flattenedList = []
            for element in input:
                flattenedList.extend(self.flatten(element))
            return flattenedList
        else:
           return [input]

    def splitAtPunctuation(self, rawText):
        return nltk.sent_tokenize(rawText)