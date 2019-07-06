# -*- coding: utf-8 -*-
import unittest
import SimpleLearnerScheme
import Text 
from Sentence import Sentence
from Text import Text
import Parser
from Parser import TextParser

class Test_test1(unittest.TestCase):
       
    def test_SentenceSplittingSingleSentenceWithPunctuation(self):
        sentence = "This, is a simple sentence."
        text = Text(sentence, "test")
        sentences = text.sentences
        self.assertEquals(1, len(sentences))
        self.assertEquals(sentence, sentences[0].rawSentence)
            
    def test_SentenceSplittingSingleSentenceWithoutPunctuation(self):
        sentence = "This is a simple sentence"
        text = Text(sentence, "test")
        sentences = text.sentences
        self.assertEquals(1, len(sentences))
        self.assertEquals(sentence, sentences[0].rawSentence)
               
    def test_SentenceSplittingTwoSentencesWithPunctuation(self):
        sentence1 = "This, is a simple sentence."
        sentence2 = "It is followed by another simple sentence."
        rawText = sentence1 + " " + sentence2
        text = Text(rawText, "test")
        sentences = text.sentences
        self.assertEquals(2, len(sentences))
        self.assertEquals(sentence1, sentences[0].rawSentence)
        self.assertEquals(sentence2, sentences[1].rawSentence)
        
    def test_SentenceSplittingTwoSentencesWithoutEndingPunctuation(self):
        sentence1 = "This, is a simple sentence."
        sentence2 = "It is followed by another simple sentence"
        rawText = sentence1 + " " + sentence2
        text = Text(rawText, "test")
        sentences = text.sentences
        self.assertEquals(2, len(sentences))
        self.assertEquals(sentence1, sentences[0].rawSentence)
        self.assertEquals(sentence2, sentences[1].rawSentence)

    def test_SentenceSplittingAtNewlines(self):
        
        sentence1 = "This, is a simple sentence"
        sentence2 = "Split by a new line."        
        rawText = sentence1 + "\n" + sentence2
        text = Text(rawText, "test")
        sentences = text.sentences
        self.assertEquals(2, len(sentences))
        self.assertEquals(sentence1, sentences[0].rawSentence)
        self.assertEquals(sentence2, sentences[1].rawSentence)

    def test_WordSplittingAtBindestrej(self):
        rawSentence = "The power-hungry shall fail, and the muggle-born"
        sentence = Sentence("test", rawSentence)
        self.assertEqual(9, len(sentence.words))
        
        self.assertEqual("the", sentence.words[0].rawWord)
        self.assertEqual("power", sentence.words[1].rawWord)
        self.assertEqual("hungry", sentence.words[2].rawWord)
        self.assertEqual("shall", sentence.words[3].rawWord)
        self.assertEqual("fail", sentence.words[4].rawWord)
        self.assertEqual("and", sentence.words[5].rawWord)
        self.assertEqual("the", sentence.words[6].rawWord)
        self.assertEqual("muggle", sentence.words[7].rawWord)
        self.assertEqual("born", sentence.words[8].rawWord)


    #def test_SentenceSplittingWithQuotes(self):
    #    self.fail("Not implemented yet.")

if __name__ == '__main__':
    unittest.main()
