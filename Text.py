from Sentence import Sentence
import nltk

class Text:

    def __init__(self, rawText, name):
        self.rawText = rawText#self.formatText(rawText)
        self.name = name
        rawSentences = nltk.sent_tokenize(rawText)
        self.sentences = []
        for rawSentence in rawSentences:
            sentence = Sentence(self, rawSentence)
            self.sentences.append(sentence)


    def formatText(self, rawText):
        return  rawText.replace(u"\u2018", "'").replace(u"\u2019", "'").replace(u"\xa9", "e").replace(u"\u2014","-").decode("utf8")