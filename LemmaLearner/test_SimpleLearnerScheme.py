# -*- coding: utf-8 -*-
import unittest
import SimpleLearnerScheme
import Text 
from Text import Text
import Parser
from Parser import TextParser

class Test_test1(unittest.TestCase):
   
    def test_CorrectUnlockingOfSentencesWhenWordsAreLearned(self):       
        rawLemma1 = "yes"
        rawLemma2 = "no"
        rawLemma3 = "maybe"
        rawLemma4 = "perfect"

        rawSentence1 = "Yes Yes Yes Yes Yes Yes Yes."
        rawSentence2 = "Yes, Yes, Yes, Yes, Yes, Yes, no."
        rawSentence3 = "Yes, Yes, Yes, Yes, Yes, Yes, maybe."
        rawSentence4 = "Yes, Yes, Yes, Yes, Yes, no, maybe, perfect."
        text = rawSentence1 + " " +  rawSentence2 + " " + rawSentence3 + " " + rawSentence4

        textDatabase = TextParser()
        
        textDatabase.addRawTextToDatabase(text, "TestText")
        textDatabase.addLemmasToDatabase(False)
        textDatabase.initialize()
        lemma1 = textDatabase.allLemmas[rawLemma1]
        lemma2 = textDatabase.allLemmas[rawLemma2]
        lemma3 = textDatabase.allLemmas[rawLemma3]
        lemma4 = textDatabase.allLemmas[rawLemma4]
        sentence1 = textDatabase.allSentences[rawSentence1]
        sentence2 = textDatabase.allSentences[rawSentence2]
        sentence3 = textDatabase.allSentences[rawSentence3]
        sentence4 = textDatabase.allSentences[rawSentence4]

        sentenceAndLemmaScores = SimpleLearnerScheme.getPriorityQueueOfDirectlyLearnableSentencesByLemmaScore(textDatabase, SimpleLearnerScheme.getSentenceScoreByConjugationFrequency)
        lemmasByFrequency = SimpleLearnerScheme.getPriorityQueueOfLemmasByFrequency(textDatabase)
        forcedToLearn = []
        notForcedToLearn = []
        orderedLearningList = []

        self.assertEquals(1, len(sentenceAndLemmaScores.sentenceScores))
        self.assertIn(sentence1, sentenceAndLemmaScores.sentenceScores)

        SimpleLearnerScheme.learnLemmaAndHandleSentencesWithLemmaFrequency(textDatabase.NotAWordLemma, notForcedToLearn, lemmasByFrequency, sentenceAndLemmaScores, SimpleLearnerScheme.getSentenceScoreByConjugationFrequency)
        
        self.assertEquals(1, len(sentenceAndLemmaScores.sentenceScores))
        self.assertIn(sentence1, sentenceAndLemmaScores.sentenceScores)
        SimpleLearnerScheme.getHighestScoringDirectlyLearnableLemma(sentenceAndLemmaScores.sentenceScores)
        
        SimpleLearnerScheme.learnLemmaAndHandleSentencesWithLemmaFrequency(lemma1, notForcedToLearn, lemmasByFrequency, sentenceAndLemmaScores, SimpleLearnerScheme.getSentenceScoreByConjugationFrequency)
        
        self.assertEquals(2, len(sentenceAndLemmaScores.sentenceScores))
        self.assertIn(sentence2, sentenceAndLemmaScores.sentenceScores)
        self.assertIn(sentence3, sentenceAndLemmaScores.sentenceScores)
        sentenceAndLemmaScores.sentenceScores[sentence2] = -100000 # Otherwise it might sometimes pop sentence 3 below
        SimpleLearnerScheme.getHighestScoringDirectlyLearnableLemma(sentenceAndLemmaScores.sentenceScores)
        
        SimpleLearnerScheme.learnLemmaAndHandleSentencesWithLemmaFrequency(lemma2, notForcedToLearn, lemmasByFrequency, sentenceAndLemmaScores, SimpleLearnerScheme.getSentenceScoreByConjugationFrequency)
        
        self.assertEquals(1, len(sentenceAndLemmaScores.sentenceScores))
        self.assertIn(sentence3, sentenceAndLemmaScores.sentenceScores)
        SimpleLearnerScheme.getHighestScoringDirectlyLearnableLemma(sentenceAndLemmaScores.sentenceScores)
        
        SimpleLearnerScheme.learnLemmaAndHandleSentencesWithLemmaFrequency(lemma3, notForcedToLearn, lemmasByFrequency, sentenceAndLemmaScores, SimpleLearnerScheme.getSentenceScoreByConjugationFrequency)
        
        self.assertEquals(1, len(sentenceAndLemmaScores.sentenceScores))
        self.assertIn(sentence4, sentenceAndLemmaScores.sentenceScores)
        SimpleLearnerScheme.getHighestScoringDirectlyLearnableLemma(sentenceAndLemmaScores.sentenceScores)
        
        SimpleLearnerScheme.learnLemmaAndHandleSentencesWithLemmaFrequency(lemma4, notForcedToLearn, lemmasByFrequency, sentenceAndLemmaScores, SimpleLearnerScheme.getSentenceScoreByConjugationFrequency)
        
        self.assertEquals(0, len(sentenceAndLemmaScores.sentenceScores))
    
    def test_OutputtedLearningListLearnsSequentially(self):
        textDatabase = TextParser()
        test = textDatabase.loadProcessedData("test")
        learningList = SimpleLearnerScheme.learnLemmasByOrderOfScore(textDatabase, SimpleLearnerScheme.getSentenceScoreByConjugationFrequency, False)
        learnedLemmas = {textDatabase.NotAWordLemma}
        #The first couple of words are simply learned from one sentence: this can be ignored
        initialSentence = learningList[0][1]

        for i in range(0, len(learningList)):
            (currentLemma, currentSentence) = learningList[i]
            self.assertFalse(currentLemma in learnedLemmas)
            learnedLemmas.add(currentLemma)
            if currentSentence != None and currentSentence != initialSentence: #Meaning< the word isn't forced           
                for word in currentSentence.words:
                    self.assertIn(word.lemma, learnedLemmas, "Error at lemma: " + word.lemma.rawLemma)

    def test_AllLemmasInTextAreLearned(self):
        textDatabase = TextParser()
        test = textDatabase.loadProcessedData("test")
        learningList = SimpleLearnerScheme.learnLemmasByOrderOfScore(textDatabase, SimpleLearnerScheme.getSentenceScoreByNextUnlockableLemma, False)
        self.assertEquals(len(learningList), len(textDatabase.allLemmas)-1) #NotAWordLemma is not included in learningList       
        for lemmaSentencePair in learningList:
            #All lemmas learned must be the same as those read from the files/those in the database
            (currentLemma, currentSentence) = lemmaSentencePair
            textParserLemma = textDatabase.allLemmas[currentLemma.rawLemma]
            self.assertEquals(currentLemma, textParserLemma)
        #NotAWordLemma must also be learned correctly
        self.assertEquals( textDatabase.allLemmas[textDatabase.NotAWordLemma.rawLemma], textDatabase.NotAWordLemma)
            
if __name__ == '__main__':
    unittest.main()