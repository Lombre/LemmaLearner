from Sentence import Sentence
import nltk

class Text:

    def __init__(self, rawText):
        self.rawText = rawText
        rawSentences = nltk.sent_tokenize(rawText)
        self.sentences = []
        for rawSentence in rawSentences:
            sentence = Sentence(self, rawSentence)
            self.sentences.append(sentence)
