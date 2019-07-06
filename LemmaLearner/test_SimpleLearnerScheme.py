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

        rawSentence1 = "Yes."
        rawSentence2 = "Yes, no."
        rawSentence3 = "Yes, maybe."
        rawSentence4 = "Yes, no, maybe, perfect."
        text = rawSentence1 + " " +  rawSentence2 + " " + rawSentence3 + " " + rawSentence4

        textDatabase = TextParser()

        textDatabase.addRawTextToDatabase(text, "TestText")
        textDatabase.addLemmasToDatabase(False)
        textDatabase.initialize()
        lemma1 = textDatabase.allLemmas[rawLemma1]
        lemma2 = textDatabase.allLemmas[rawLemma2]
        lemma3 = textDatabase.allLemmas[rawLemma3]
        lemma4 = textDatabase.allLemmas[rawLemma4]

        directlyUnlockableLemmasScore, sentencePairsBySentenceScore, directlyUnlockableLemmas = SimpleLearnerScheme.getPriorityQueueOfDirectlyLearnableSentencesByLemmaFrequency(textDatabase, SimpleLearnerScheme.getSentenceScoreByNextUnlockableLemma)
        lemmasByFrequency = SimpleLearnerScheme.getPriorityQueueOfLemmasByFrequency(textDatabase)
        forcedToLearn = []
        notForcedToLearn = []
        orderedLearningList = []

        self.assertEquals(2, len(directlyUnlockableLemmas))
        self.assertIn(textDatabase.NotAWordLemma, directlyUnlockableLemmas)
        self.assertIn(lemma1, directlyUnlockableLemmas)

        SimpleLearnerScheme.learnLemmaAndHandleSentencesWithLemmaFrequency(textDatabase.NotAWordLemma, notForcedToLearn, sentencePairsBySentenceScore, lemmasByFrequency, directlyUnlockableLemmasScore, directlyUnlockableLemmas, SimpleLearnerScheme.getSentenceScoreByNextUnlockableLemma)
        
        self.assertEquals(1, len(directlyUnlockableLemmas))
        self.assertIn(lemma1, directlyUnlockableLemmas)
        
        SimpleLearnerScheme.learnLemmaAndHandleSentencesWithLemmaFrequency(lemma1, notForcedToLearn, sentencePairsBySentenceScore, lemmasByFrequency, directlyUnlockableLemmasScore, directlyUnlockableLemmas, SimpleLearnerScheme.getSentenceScoreByNextUnlockableLemma)
        
        self.assertEquals(2, len(directlyUnlockableLemmas))
        self.assertIn(lemma2, directlyUnlockableLemmas)
        self.assertIn(lemma3, directlyUnlockableLemmas)
        
        SimpleLearnerScheme.learnLemmaAndHandleSentencesWithLemmaFrequency(lemma2, notForcedToLearn, sentencePairsBySentenceScore, lemmasByFrequency, directlyUnlockableLemmasScore, directlyUnlockableLemmas, SimpleLearnerScheme.getSentenceScoreByNextUnlockableLemma)
        
        self.assertEquals(1, len(directlyUnlockableLemmas))
        self.assertIn(lemma3, directlyUnlockableLemmas)
        
        SimpleLearnerScheme.learnLemmaAndHandleSentencesWithLemmaFrequency(lemma3, notForcedToLearn, sentencePairsBySentenceScore, lemmasByFrequency, directlyUnlockableLemmasScore, directlyUnlockableLemmas, SimpleLearnerScheme.getSentenceScoreByNextUnlockableLemma)
        
        self.assertEquals(1, len(directlyUnlockableLemmas))
        self.assertIn(lemma4, directlyUnlockableLemmas)

        SimpleLearnerScheme.learnLemmaAndHandleSentencesWithLemmaFrequency(lemma4, notForcedToLearn, sentencePairsBySentenceScore, lemmasByFrequency, directlyUnlockableLemmasScore, directlyUnlockableLemmas, SimpleLearnerScheme.getSentenceScoreByNextUnlockableLemma)
        
        self.assertEquals(0, len(directlyUnlockableLemmas))
    
    def test_OutputtedLearningListLearnsSequentially(self):
        textDatabase = TextParser()
        test = textDatabase.loadProcessedData("test")
        learningList = SimpleLearnerScheme.learnLemmasByOrderOfScore(textDatabase, SimpleLearnerScheme.getSentenceScoreByNextUnlockableLemma, False)
        learnedLemmas = {textDatabase.NotAWordLemma}
        for lemmaSentencePair in learningList:
            (currentLemma, currentSentence) = lemmaSentencePair
            self.assertFalse(currentLemma in learnedLemmas)
            learnedLemmas.add(currentLemma)
            if currentSentence != None: #Meaning< the word isn't forced           
                for word in currentSentence.words:
                    self.assertIn(word.lemma, learnedLemmas)

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