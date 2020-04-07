# -*- coding: utf-8 -*-
from Sentence import Sentence
import nltk
import re
from timeit import default_timer as timer
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
    def __init__(self, rawText, name):
        self.rawText = rawText #self.formatText(rawText)
        self.name = name
        self.sentences = self.exstractSentences(rawText)

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

    def convertRawSentencesIntoSentences(self, rawSentences):
        cleanSentences = []                
        startTime = timer()        
        print("Sentence splitting: " + str(round(0/len(rawSentences)*100, 1)) + "% done.")
        for i in range(0, len(rawSentences)):
            rawSentence = rawSentences[i]
            sentence = Sentence(self, rawSentence)
            cleanSentences.append(sentence)
            if startTime + 5 < timer():
                print("Sentence splitting: " + str(round(i/len(rawSentences)*100, 1)) + "% done.")
                startTime = timer()
        print("Sentence splitting: " + str(round(len(rawSentences)/len(rawSentences)*100, 1)) + "% done.")
        return cleanSentences

    def splitIntoParagraphs(self, rawText):
        return [s.strip() for s in rawText.splitlines()]

    def exstractSentences(self, rawText):   
        cleanText = self.cleanTextOfWeirdCharacters(rawText)
        paragraphs = self.splitIntoParagraphs(cleanText)
        rawSentences = self.splitIntoRawSentences(paragraphs)
        cleanSentences = self.convertRawSentencesIntoSentences(rawSentences)

        return cleanSentences

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