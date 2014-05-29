#!/usr/bin/env python3.2
#
# export PATH=/net/aps/64/bin:$PATH
# export PYTHONPATH=/net/aps/64/lib/python3.2

import io, sys
import alpinocorpus
from lxml import etree

if len(sys.argv) == 1:
    sys.stderr.write('\nUsage: {} filename(s)\n\n'.format(sys.argv[0]))
    sys.exit()

def resolve_index(node,tree):
    index = node.get('index')
    cat = node.get('cat')
    word = node.get('word')
    if cat or word:
        return node
    else:
        for ant in tree.iterfind('.//node[@index="{IX}"]'.format(IX=index)):
            nindex = ant.get('index')
            ncat = ant.get('cat')
            nword = ant.get('word')
            if index == nindex and ( ncat or nword):
                return ant


def lemma_of_head(node,tree):
    ant = resolve_index(node,tree)
    lemma = ant.get('lemma')
    cat = ant.get('cat')
    if lemma:
        return lemma
    if cat == 'mwu':
        lemmas = []
        for child in ant:
            childant = resolve_index(child,tree)
            lem = childant.get('lemma')
            lemmas.append(lem)
        return "_".join(lemmas)
    for child in ant:
        rel = child.get('rel')
        if rel == 'hd':
            return lemma_of_head(child,tree)
    return None

def pt_of_head(node,tree):
    ant = resolve_index(node,tree)
    pt = ant.get('pt')
    if pt:
        return pt
    return None

def createDict(bestand):
    emptyDict = {}
    file = open(bestand, "w")
    file.write(str(emptyDict))
    file.close()
    for filename in sys.argv[1:]:
        print("< Het corpus ", filename, " wordt nu geindexeerd. >")

        reader=alpinocorpus.CorpusReader(filename)

        dictionary = {}

        for file in reader.entries():
            xml = reader.read(file.name())
            xml = xml.encode('utf-8')
            tree = etree.XML(xml)

            for node in tree.iter():
                rel = node.get('rel')
                for target in ['su','obj1','obj2','app','mod','det','pc','hdf',
                           'pobj1','predc','svp','ld','me','predm','obcomp']:
                    if rel == target:
                        hd = lemma_of_head(node.getparent(),tree)
                        su = lemma_of_head(node,tree)
                        suPt = pt_of_head(node, tree)
                        if hd and su:
                            if suPt == 'n':
                                temp = hd + "." + target
                                if dictionary.get(su, "No") == "No":
                                    dictionary[su] = {temp:1}
                                else:
                                    dictionary[su][temp] = dictionary[su].get(temp, 0) + 1           # for conjuncts: generate a triple for each conjunct!
                if rel == 'cnj':
                    parent=node.getparent()
                    rel = parent.get('rel')
                    for target in ['su','obj1','obj2','app','mod','det','pc','hdf',
                               'pobj1','predc','svp','ld','me','predm','obcomp']:
                        if rel == target:
                            hd = lemma_of_head(parent.getparent(),tree)
                            su = lemma_of_head(node,tree)
                            suPt = pt_of_head(node, tree)
                            if hd and su:
                                if suPt == 'n':
                                    temp = hd + "." + target
                                    if dictionary.get(su, "No") == "No":
                                        dictionary[su] = {temp:1}
                                    else:
                                        dictionary[su][temp] = dictionary[su].get(temp, 0) + 1

        file = open(bestand, 'r')
        fileDict = eval(file.read())
        file.close()
        fileDict.update(dictionary)
        file = open(bestand, "w")
        file.write(str(fileDict))
        file.close()
        print("< Het corpus ", filename, " is succesvol geindexeerd. >")
    print("")
    print("< De dictionary ", bestand, " is succesvol gecreerd en opgeslagen. >")

def main():
    print("==========================SAME WORDS V1.0==========================")
    print("= Dit programma geeft u de mogelijkheid om een zelfstandig        =")
    print("= naamwoord in te voeren. Dit programma zal vervolgens in een     =")
    print("= corpus zoeken naar vergelijkbare woorden.                       =")
    print("= Om het zoeken te versnellen bied het programma de mogelijkheid  =")
    print("= om een externe dictionary te gebruiken. Deze externe dictionary =")
    print("= kan eveneens met dit programma worden gecreerd worden.          =")
    print("===================================================================")
    print("")
    question = input("Wilt u de dictionary creeren en opslaan? (y/n) > ")
    while question not in ['y', 'n', 'Y', 'N', 'yes', 'no', 'Yes', 'No']:
        print("< Vult u a.u.b. 'yes' or 'no' in! >")
        print("")
        question = input("Wilt u de dictionary creeren en opslaan? (y/n) > ")
    if question in ['y', 'Y', 'yes', 'Yes']:
        print("")
        bestandsnaam = input("Bestandsnaam > ")
        createDict(bestandsnaam)
        #createDict()
        print("")
    else:
        print("")
        print("U heeft ervoor gekozen geen nieuwe dictionary te creeren.")
        print("Welke bestaande externe dictionary wilt u gebruiken?")
        bestandsnaam = input("Bestandsnaam > ")
        print("")

    file = open(bestandsnaam, 'r')
    corpusDict = eval(file.read())
    file.close()
    # Create list with all keys
    corpusDictKeys = []
    for key in corpusDict.keys():
        corpusDictKeys.append(key)

    searchword = input("Welk woord wilt u zoeken? ( [ENTER] om te stoppen ) > ")
    while searchword != "":
        if searchword not in corpusDictKeys:
            print("< Het door u ingevoerde zoekwoord staat niet in het gebruikte >")
            print("< corpus. Voer een ander woord in dat wel in het corpus staat >")
            print("< of gebruik een uitgebreider corpus.                         >")
            print("")
        else:
            # Create search-vector
            searchDict = corpusDict[searchword]
            searchDictKeys = []
            for key in searchDict.keys():
                searchDictKeys.append(key)

            # Pop relations in 2nd demension
            deleteKeys = {}
            emptyList = []
            for key in corpusDict.keys():
                for relation in corpusDict[key].keys():
                    if relation not in searchDictKeys:
                        if key not in deleteKeys:
                            deleteKeys[key] = [relation]
                        else:
                            tempList = deleteKeys.get(key)
                            tempList.append(relation)
                            deleteKeys[key] = tempList

            for key, value in deleteKeys.items():
                for item in value:
                   corpusDict[key].pop(item)

            # Add relations with count 0 to 2nd demension
            for key in corpusDict.keys():
                relationList = []
                for relation in corpusDict[key].keys():
                    relationList.append(relation)
                for relation in searchDictKeys:
                    if relation not in relationList:
                        corpusDict[key][relation] = 0

            # Calculate distance and save in distDict
            searchDictDistance = []
            for relation in searchDictKeys:
                searchDictDistance.append(corpusDict[searchword][relation])

            distDict = {}
            for key, value in corpusDict.items():
                #if key != searchword:
                    distanceList = []
                    for relation in searchDictKeys:
                        distanceList.append(corpusDict[key][relation])
                    count = 0
                    for i in range(len(searchDictDistance)):
                        a = searchDictDistance[i]
                        b = distanceList[i]
                        count = count + ( min(a,b) / (a+b) )
                    distance = 2*count
                    distDict[key] = distance

            # Create sorted list from distDict
            distDictSorted = sorted(distDict, key=distDict.get)
            distDictSorted = reversed(distDictSorted)
            distDictSorted = list(distDictSorted)

            # Determine best 10 words
            print("")
            print("Best 10 matches:")
            print("")
            first10Words = distDictSorted[:10]
            for word in first10Words:
                match = ( distDict[word] * 100 ) / distDict[searchword]
                print("{0:<30}{1:<.2f}%".format(word, match))
            print("")

        # Initialize variables again
        searchDict = {}
        file = open(bestandsnaam, 'r')
        corpusDict = eval(file.read())
        file.close()
        corpusDictKeys = []
        for key in corpusDict.keys():
            corpusDictKeys.append(key)

        searchword = input("Welk woord wilt u zoeken? ( [ENTER] om te stoppen ) > ")

    print("===================================================================")
    print("= Dit programma werd u aangeboden door Aileen Bus,                =")
    print("= Reinard van Dalen, Mathijs van Maurik en Leon Melein.           =")
    print("= Graag vragen wij uw hulp om ons programma te verbeteren:        =")
    print("= (c) 2014 - info@vandalenwebdesign.nl                            =")
    print("==========================SAME WORDS V1.0==========================")

main()