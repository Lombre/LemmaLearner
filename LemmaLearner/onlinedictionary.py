# -*- coding: utf-8 -*-
import nltk
import re
import string
import io
import time
import urllib3
import os
import pickle
import sys

http = urllib3.PoolManager()
ERROR_CODE = "ERROR"

SHOULD_SAVE_WEBSITES = True

MISPELLING_MARKER = "<span class=\"no-results-title"


def meh():
    return 0

def isInOnlineDictionary(word, onlineDictionary):
    if word in onlineDictionary:
        return onlineDictionary[word]
    fullURL = getOnlineDictionaryWordURL(word)
    filePath = getOnlineDictionaryFilePath(word)
    if os.path.isfile(filePath):
        with open(filePath, 'r', encoding="utf-8") as file:
            fileContent = file.read()
            inDictionary = not(fileContent == ERROR_CODE or MISPELLING_MARKER in fileContent) or word == "notaword"
            onlineDictionary[word] = inDictionary
    else:
        time.sleep(1) # So the website isn't getting spammed
        onlineDictionary[word] = checkAndSaveisInOnlineDictionary(fullURL, filePath)
        saveOnlineDictionary(onlineDictionary)
    return onlineDictionary[word]

def getOnlineDictionaryWordURL(word): #getOnlineDictionaryWordAdress(word):
    baseURL = 'https://www.dictionary.com/browse/'
    fullURL = baseURL + word
    return fullURL

def getOnlineDictionaryFilePath(word):
    return "../Websites/" + word + ".txt"

def checkAndSaveisInOnlineDictionary(fullURL, filePath):
    response = None
    response = http.request("GET", fullURL)
    webContent = response.data.decode('utf-8')
    try:
        if SHOULD_SAVE_WEBSITES:
            with open(filePath, 'w+', encoding="utf-8") as file:
                file.write(webContent)
        if MISPELLING_MARKER in webContent:
            return False 
        else:
            return True
        return True
    except:
        #aux is used by the system, so you cannot create files with that name
        #This was learned the hard way :/
        if filePath != "../Websites/aux.txt" and SHOULD_SAVE_WEBSITES:
            with open(filePath, 'w+') as file:
                file.write(ERROR_CODE)
        return False

def saveOnlineDictionary(onlineDictionary):
    currentRecursionLimit = sys.getrecursionlimit()
    sys.setrecursionlimit(100000)
    pickle.dump(onlineDictionary, open("onlineDictionary" + '.pkl', 'wb'))
    sys.setrecursionlimit(currentRecursionLimit)

def loadOnlineDictionary(): 
    if os.path.isfile("onlineDictionary.pkl"):
        rawData = io.open("onlineDictionary" + ".pkl", 'rb').read()
        return pickle.loads(rawData)
    else:
        return {}

