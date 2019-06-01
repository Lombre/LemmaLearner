import SimpleLearnerScheme
import TextParser

print(u'\u201cRon, what \u2014 ?\u201d\n\n\u201cSCABBERS! kage')
test = TextParser.loadProcessedData("everything")
learningList = SimpleLearneScheme.learnLemmasByOrderOfScore(getSentenceScoreByNextUnlockableLemma)