# -*- coding: utf-8 -*-
import unittest
import onlinedictionary
from Parser import TextParser

class Test_test1(unittest.TestCase):

    def test_OnlineDictionaryActualWordRecognition(self): #
        word = "gasped"
        print(onlinedictionary.meh())
        address = onlinedictionary.getOnlineDictionaryWordURL(word)
        filePath = onlinedictionary.getOnlineDictionaryFilePath(word)
        wordExists = onlinedictionary.checkAndSaveisInOnlineDictionary(address, filePath)
        self.assertTrue(wordExists)
            
    def test_OnlineDictionaryNonWordRecognition(self):
        word = "hohsaihseh"
        print(onlinedictionary.meh())
        address = onlinedictionary.getOnlineDictionaryWordURL(word)
        filePath = onlinedictionary.getOnlineDictionaryFilePath(word)
        wordExists = onlinedictionary.checkAndSaveisInOnlineDictionary(address, filePath)
        self.assertFalse(wordExists)
    
    def test_onlineDictionaryRecognition(self):
        parser = TextParser()
        rawText = "He gasped."
        parser.addRawTextToDatabase(rawText, "test")
        parser.addLemmasToDatabase(False)
        lemmas = parser.allLemmas.values()
        self.assertEqual(3, len(lemmas))

if __name__ == '__main__':
    unittest.main()