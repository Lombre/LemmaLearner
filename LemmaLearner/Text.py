# -*- coding: utf-8 -*-
from Sentence import Sentence
import nltk
import re

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


    def exstractSentences(self, rawText):        
        splitAtNewlines = [s.strip() for s in rawText.splitlines()]
        #splitAtQuotes = [splitSentenceAtQuotes(s) for s in splitAtNewlines]
        splitAtPunctuation = [self.splitAtPunctuation(s) for s in splitAtNewlines]
        rawSentences = self.flatten(splitAtPunctuation)

        cleanSentences = []

        for rawSentence in rawSentences:
            sentence = Sentence(self, rawSentence)
            cleanSentences.append(sentence)

        return cleanSentences

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