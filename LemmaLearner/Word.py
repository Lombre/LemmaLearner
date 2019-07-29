
class Word:

    def __init__(self, rawWord, originSentence):
        self.rawWord = rawWord
        self.sentences = {originSentence.rawSentence: originSentence}
        self.frequency = 1
        self.lemma = None
        self.MAX_TIMES_LEARNED = 1
        self.timesLearned = 0
        self.hasBeenLearned = False

    #Marks the word as covered in the sentences it is found in.
    def coverSentences(self):
        for sentence in self.sentences.values():
            sentence.uncoveredWords.remove(self)

    def recoverLemma(self, allLemmas):
        #Ensuring that this words lemma points to the one that is in the complete list of lemmas.
        #self.lemma = allLemmas[self.lemma.rawLemma]

        self.lemma.addNewWord(self)

    def __getstate__(self):
        self.sentences = {}
        return  self.__dict__

    
    def __str__(self):
        return self.rawWord