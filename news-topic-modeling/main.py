# coding: utf-8

__author__ = "Ciprian-Octavian Truică"
__copyright__ = "Copyright 2020, University Politehnica of Bucharest"
__license__ = "GNU GPL"
__version__ = "0.1"
__email__ = "ciprian.truica@cs.pub.ro"
__status__ = "Production"

from tokenization import Tokenization
from vectorization import Vectorization
from topicmodeling import TopicModeling
import sys
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import cpu_count
import time


def tkns(text):
    title = tkn.createCorpus(text['title'], apply_FE=False)
    content = tkn.createCorpus(text['content'], apply_FE=False)
    clean_text = title + content
    clean_text = ' '.join([' '.join(elem) for elem in clean_text])
    return clean_text 

def processElement(row):
    title = tkn.createCorpus(row[0], apply_FE=False)
    content = tkn.createCorpus(row[1], apply_FE=False)
    clean_text = title + content
    clean_text = ' '.join([' '.join(elem) for elem in clean_text])
    return clean_text

if __name__ == '__main__':
    fin = sys.argv[1]
    num_topics = int(sys.argv[2])
    num_words = int(sys.argv[3])
    num_iterations = int(sys.argv[4])
    no_threads = cpu_count() - 2

    print("Start Read File!")
    df = pd.read_csv(fin)
    print("End Read File!")
    

    print("Start Tokenization!")
    start = time.time() * 1000
    tkn = Tokenization()
    # with UDF 
    # df = df.apply(tkns, axis=1)
    # clean_texts = df.to_list()

    clean_texts = []
    with ProcessPoolExecutor(max_workers=no_threads) as worker:
        for result in worker.map(processElement, df.to_numpy()):
            if result:                
                clean_texts.append(result)
    end = time.time() * 1000
    print("Execution time (ms)", end - start)
    print("End Tokenization!")

    print("Start Vectorization!")
    vec = Vectorization(clean_texts)
    vec.vectorize()
    id2word = vec.getID2Word()
    corpus = vec.getTFIDFNorm()
    print("End Vectorization!")
    
    tm = TopicModeling(id2word=id2word, corpus=corpus)

    print("Start Topic Modeling NNF!")
    start = time.time()
    topicsNMF = tm.topicsNMF(num_topics=num_topics, num_words=num_words, num_iterations=num_iterations)
    print("=============NMF=============")
    for topic in topicsNMF:
        print("TopicID", topic[0], topic[1])
    print("=============================")
    end = time.time()
    print("Execution time (ms)", end - start)
    print("End Topic Modeling NNF!")

    # print("Start Topic Modeling LDA!")
    # print("=============LDA=============")
    # topicsLDA = tm.topicsLDA(num_topics=num_topics, num_words=num_words, num_iterations=num_iterations)
    # for topic in topicsLDA:
    #     print("TopicID", topic[0], topic[1])
    # print("=============================")
    # print("End Topic Modeling LDA!")

    