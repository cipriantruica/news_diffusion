import spacy
import networkx as nx
import pylab as plt
import pandas as pd
import pickle
import sys
from tokenization import Tokenization
from datetime import datetime, timedelta
import time

start = time.time()

nlp = spacy.load("en_core_web_lg")

pickle_te = open(sys.argv[1], "rb")
pickle_ne = open(sys.argv[2], "rb")
pickle_nt = open(sys.argv[3], "rb")
tweets_by_event = pickle.load(pickle_te)
news_by_event = pickle.load(pickle_ne)
news_by_topic = pickle.load(pickle_nt)

# processing news topics
news_topics = []
idx = 0
for nmf_topic in news_by_topic:
    topic = "news_topic_" + str(idx).zfill(4)
    nmf_news = {}
    nmf_news['topic'] = topic
    nmf_news['text'] = ' '.join([elem[0] for elem in nmf_topic])
    news_topics.append(nmf_news)
    idx += 1

# processing twitter event
twitter_events = []
idx = 0
for event in tweets_by_event.events:
    curr_event = []
    start_date = tweets_by_event.corpus.to_date(event[1][0])
    end_date = tweets_by_event.corpus.to_date(event[1][1])
    curr_event.append(event[2])
    for related_word, weight in event[3]:
        curr_event.append(related_word)
    document = ' '.join(curr_event)
    if document:
        event_name = "twitter_event_" + str(idx).zfill(4)
        twitter_events.append({"event": event_name , "start_date": start_date , "end_date": end_date, "text": document})
        idx += 1

# processing news event
news_events = []
idx = 0
for event in news_by_event.events:
    curr_event = []
    start_date = news_by_event.corpus.to_date(event[1][0])
    end_date = news_by_event.corpus.to_date(event[1][1])
    curr_event.append(event[2])
    for related_word, weight in event[3]:
        curr_event.append(related_word)
    document = ' '.join(curr_event)
    if document:
        event_name = "twitter_event_" + str(idx).zfill(4)
        news_events.append({"event": event_name , "start_date": start_date , "end_date": end_date, "text": document})
        idx += 1    

# matching news topics with news events
sim_topic_news_event_news = []
for news_topic in news_topics:
    nt_doc = nlp(news_topic['text'])
    for news_event in news_events:   
        ne_doc = nlp(news_event['text'])
        curr_sim = nt_doc.similarity(ne_doc)
        sim_topic_news_event_news.append([news_topic['topic'], news_topic['text'], news_event["event"], news_event["start_date"], news_event["end_date"], news_event["text"], curr_sim])



# matching news events with twitter events
sim_news_event_twitter_event = []
for news_event in news_events:
    ne_doc = nlp(news_event['text'])
    for twitter_event in twitter_events:
        if twitter_event['start_date'] >= news_event['start_date'] and twitter_event['start_date'] <= news_event['start_date'] + timedelta(days=5):
            te_doc = nlp(twitter_event["text"])
            curr_sim = ne_doc.similarity(te_doc)
            sim_news_event_twitter_event.append([ news_event["event"], news_event["start_date"], news_event["end_date"], news_event["text"], twitter_event["event"], twitter_event["start_date"], twitter_event["end_date"],twitter_event["text"], curr_sim])
            


end = time.time()



df_news_topics_news_events = pd.DataFrame(sim_topic_news_event_news, columns=["news_topic", "news_topic_text", "news_event", "news_event_start_date", "news_event_end_date", "news_event_text", "similarity"])
df_news_events_twitter_events = pd.DataFrame(sim_news_event_twitter_event, columns=["news_event", "news_event_start_date", "news_event_end_date", "news_event_text", "twitter_event", "twitter_event_start_date", "twitter_event_end_date", "twitter_event_text", "similarity"])
df_news_topics_news_events.to_csv("news_topics_news_events.csv", index=False)
df_news_events_twitter_events.to_csv("news_events_twitter_events.csv", index=False)
