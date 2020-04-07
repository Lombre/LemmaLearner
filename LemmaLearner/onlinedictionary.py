# -*- coding: utf-8 -*-
import nltk
import re
import string
import io
import time
import urllib3
import os
import pickle

http = urllib3.PoolManager()
ERROR_CODE = "ERROR"

def meh():
    return 0

def isInOnlineDictionary(word, onlineDictionary):
    if word in onlineDictionary:
        return onlineDictionary[word]
    fullURL = getOnlineDictionaryWordURL(word)
    filePath = getOnlineDictionaryFilePath(word)
    if os.path.isfile(filePath):
        with open(filePath, 'r', encoding="utf-8") as file:
            possibleErrorCode = file.read(len(ERROR_CODE))
            inDictionary = possibleErrorCode != ERROR_CODE
            onlineDictionary[word] = inDictionary
    else:
        time.sleep(1) # So the website isn't getting spammed
        onlineDictionary[word] = checkAndSaveisInOnlineDictionary(fullURL, filePath)
    return onlineDictionary[word]

def getOnlineDictionaryWordURL(word): #getOnlineDictionaryWordAdress(word):
    baseURL = 'https://www.dictionary.com/browse/'
    fullURL = baseURL + word
    return fullURL

def getOnlineDictionaryFilePath(word):
    return "Websites/" + word + ".txt"

def checkAndSaveisInOnlineDictionary(fullURL, filePath):
    response = None
    response = http.request("GET", fullURL)
    webContent = response.data.decode('utf-8')
    try:
        with open(filePath, 'w+', encoding="utf-8") as file:
            file.write(webContent)
        if "<span class=\"no-results-title" in webContent:
            return False 
        else:
            return True
        return True
    except:
        if filePath != "Websites/aux.txt":
            with open(filePath, 'w+') as file:
                file.write(ERROR_CODE)
        return False


def loadOnlineDictionary(): 
    if os.path.isfile("onlineDictionary.pkl"):
        rawData = io.open("onlineDictionary" + ".pkl", 'rb').read()
        return pickle.loads(rawData)
    else:
        return {}

