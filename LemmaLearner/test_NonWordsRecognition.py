# -*- coding: utf-8 -*-
import unittest
import SimpleLearnerScheme
import Text 
from Text import Text
import os
import Parser  
import nltk
import Sentence
from Sentence import Sentence
import numpy
from nltk import ne_chunk, pos_tag, word_tokenize
from nltk.tree import Tree
from Parser import TextParser

class Test_test1(unittest.TestCase):

    def test_SimpleNameIsNotRecognizedAsWord(self):
        rawSentence = "My name is Harry Potter." 
        sentence = Sentence("Test", rawSentence)
        wordsToPosTags = sentence.wordsToTags

        self.assertEquals(len(wordsToPosTags["my"]), 1)
        self.assertEquals(list(wordsToPosTags["my"])[0], Sentence.getRealWordTag())

        self.assertEquals(len(wordsToPosTags["name"]), 1)
        self.assertEquals(list(wordsToPosTags["name"])[0], Sentence.getRealWordTag())

        self.assertEquals(len(wordsToPosTags["is"]), 1)
        self.assertEquals(list(wordsToPosTags["is"])[0], Sentence.getRealWordTag())

        self.assertEquals(len(wordsToPosTags["harry"]), 1)
        self.assertNotEquals(list(wordsToPosTags["harry"])[0], Sentence.getRealWordTag())

        self.assertEquals(len(wordsToPosTags["potter"]), 1)
        self.assertNotEquals(list(wordsToPosTags["potter"])[0], Sentence.getRealWordTag())

    def test_LongSentenceNameRecognition(self):
        rawSentence = "At half past eight, Mr. Dursley picked up his briefcase, pecked Mrs. Dursley on the cheek, and tried to kiss Dudley good-bye but missed, because Dudley was now having a tantrum and throwing his cereal at the walls."
        names = {"mr", "mrs", "dursley", "dudley"}       
        sentence = Sentence("Test", rawSentence)
        words = sentence.words
        wordsToPosTags = sentence.wordsToTags
        for word in words:        
            self.assertEquals(len(wordsToPosTags[word.rawWord]), 1)
            if word.rawWord in names:                
                self.assertNotEquals(list(wordsToPosTags[word.rawWord])[0], Sentence.getRealWordTag())
            else:                
                self.assertEquals(list(wordsToPosTags[word.rawWord])[0], Sentence.getRealWordTag())

    def test_WordThatCanBeNameRecognizedAsNotAName(self):
        self.fail("Not implemented yet")
    

if __name__ == '__main__':
    unittest.main()