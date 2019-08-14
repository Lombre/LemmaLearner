import os.path
import time
import io





extraLemmasFoundInText = {}
conjugationToLemmas = {}


def initialize(filename):        
    file = io.open(filename, 'rU', encoding='utf-8')    
    line: str = file.readline()
    doubletes = set()
    numberOfLines = 0
    while line:             
        numberOfLines += 1
        line = line.replace(" ", "").replace("\n", "")
        [lemma, conjugations] = line.split("->")
        rawLemma = lemma.split("/")[0]
        rawConjugations = set(conjugations.split(","))
        rawConjugations.add(rawLemma)
        for conjugation in rawConjugations:
            if conjugation in conjugationToLemmas:
                lemmaList = conjugationToLemmas[conjugation]
                if conjugation == conjugationToLemmas[conjugation][0]:
                    continue
                elif conjugation == rawLemma:
                    lemmaList = [rawLemma]
                    if conjugation in doubletes:
                        doubletes.remove(conjugation)
                else:
                    doubletes.add(conjugation)
                    lemmaList.append(rawLemma)
            else:
                conjugationToLemmas[conjugation] = [rawLemma]
        line = file.readline()
    k = 1

def lemmatize(rawWord: str):
    if rawWord in conjugationToLemmas:
        return conjugationToLemmas[rawWord]
    elif rawWord in extraLemmasFoundInText:
        return extraLemmasFoundInText[rawWord]
    else:
        extraLemmasFoundInText[rawWord] = [rawWord]
        return [rawWord]