
class Word:
    def __init__(self, rawWord, originSentence):
        self.rawWord = rawWord
        self.sentences = {originSentence.rawSentence: originSentence}
        self.frequency = 1
        self.lemma = None

    #Marks the word as covered in the sentences it is found in.
    def coverSentences(self):
        for sentence in self.sentences.values():
            sentence.uncoveredWords.remove(self)