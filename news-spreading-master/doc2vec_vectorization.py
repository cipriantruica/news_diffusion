import datetime
# import torch
import numpy as np
import os
import sys
import pickle
import gensim
import time
from models.tweet import Tweet
from models.tweet_stats import TweetStats
from models.twitter_user import TwitterUser
from process_mabed_results import load_data
from settings.settings import load_environment
from vocabulary import Vocabulary


def get_source(source_page):
    sources = ['BBCWorld', 'guardian','googlenews', 'WSJ', 'Telegraph', 'bloomberg', 'businessinsider']
    return [1 if w == source_page else 0 for w in sources]


def get_tweet_vocabulary(vocabulary, tweet):
    words = tweet['main_word'] + tweet['related_word']
    return np.array(vocabulary.get_words_codification(words))


def get_twitter_user_classes(results):
    users = set()
    users_followers = []

    for ev in results:
        for matched_tweet in ev['matched_tweets']:
            tw = Tweet.objects.get(twitter_id=matched_tweet['tweet_id'])
            users.add(tw.twitter_user_id)
    
    for tw_user_id in list(users):
        tw_user = TwitterUser.objects.get(twitter_id=tw_user_id)
        users_followers.append(tw_user.followers)
    
    sorted_followers = sorted(users_followers)
    followers_borders = _build_classes_borders(sorted_followers, 3)
    return {
        'bounds': followers_borders,
        'values': [sorted_followers[idx] for idx in followers_borders]
    }


def get_events_classes(results, classes_no):
    all_matched_tweets_events = []
    for ev in results:
        all_matched_tweets_events += [mt['tweet_id'] for mt in ev['matched_tweets']]

    stats_retweets = []
    stats_favorites = []
    all_matched_tweets = list(set(all_matched_tweets_events))
    print("All matched tweets %d" % len(all_matched_tweets))
    for tw_id in all_matched_tweets:
        try:
            tw_stats = TweetStats.objects.get(twitter_id=tw_id).stats[-1]
            last_stats = {
                'favorites': tw_stats.favorites,
                'retweets': tw_stats.retweets
            }
        except Exception:
            tw = Tweet.objects.get(twitter_id=tw_id)
            last_stats = {
                'favorites': tw.favorites,
                'retweets': tw.retweets
            }

        stats_retweets.append(last_stats['retweets'])
        stats_favorites.append(last_stats['favorites'])

    sorted_retweets = sorted(stats_retweets)
    sorted_favorites = sorted(stats_favorites)
    retweets_bounds = _build_classes_borders(sorted_retweets, classes_no)
    favorites_bounds = _build_classes_borders(sorted_retweets, classes_no)

    return {
        'favorites': {
            'bounds': favorites_bounds,
            'values': [sorted_favorites[idx] for idx in favorites_bounds]
        },
        'retweets': {
            'bounds': retweets_bounds,
            'values': [sorted_retweets[idx] for idx in retweets_bounds]
        },
    }


def _build_classes_borders(stats, classes_no):
    # compute groups by sorting an the list, break it into classes_number sections
    tweets_no = len(stats)
    step = int(tweets_no / classes_no)
    indexes = [step]
    while len(indexes) < classes_no - 1:
        indexes.append((len(indexes) + 1) * step)

    adjusted_indexes = []
    for idx in indexes:
        init_idx = idx
        if stats[idx] == stats[idx-1]:
            while idx < len(stats) and stats[idx] == stats[idx-1]:
                    idx += 1

            if idx == len(stats):
                idx = init_idx
                while idx > 0 and stats[idx] == stats[idx-1]:
                    idx -= 1

                if idx == 0:
                    print("Am data de belea")

        adjusted_indexes.append(idx)

    return adjusted_indexes

def get_event_class(classes, tw_stats):
    fav_class = None
    ret_class = None

    fav_classes = classes['favorites']['values']
    ret_classes = classes['retweets']['values']

    if tw_stats['favorites'] < fav_classes[0]:
        fav_class = 0
    elif tw_stats['favorites'] < fav_classes[1]:
        fav_class = 1
    else:
        fav_class = 2
        # for idx, upper_bound in enumerate(fav_classes):
        #     if tw_stats['favorites'] > upper_bound:
        #         continue
        #     fav_class = idx + 1
        #     break

    # if tw_stats['retweets'] < ret_classes[0]:
    #     ret_class = 0
    # else:
    #     for idx, upper_bound in enumerate(ret_classes):
    #         if tw_stats['retweets'] > upper_bound:
    #             continue
    #         ret_class = idx + 1
    #         break

    if tw_stats['retweets'] < ret_classes[0]:
        fav_class = 0
    elif tw_stats['retweets'] < ret_classes[1]:
        fav_class = 1
    else:
        fav_class = 2

    # if ret_class is None:
    #   ret_class = len(ret_classes)

    # if fav_class is None:
    #     fav_class = len(fav_classes)

    return fav_class, ret_class

def _build_experiment_one_hot_vectors(mabed_results, classes):
    """ [_one_hot_vectors_of_words], day of week, [publisher] -> class [3 classes between some numbers]"""
    experiment_filename = 'experiment_one_hot_vectors.pickle'
    dataset = {
        'data': [],
        'classes': classes
    }

    vocabulary = Vocabulary(mabed_results)

    classes = get_events_classes(mabed_results, 3)
    for result in mabed_results:
        for matched_tweet in result['matched_tweets']:
            tweet_id = matched_tweet['tweet_id']
            tw = Tweet.objects.get(twitter_id=tweet_id)
            try:
                tw_stats = TweetStats.objects.get(twitter_id=tweet_id)
                last_stats = tw_stats.stats[-1].to_mongo().to_dict()
            except Exception:
                last_stats = {'favorites': tw.favorites, 'retweets': tw.retweets, 'at_time': tw.created_at}

            tw_classes = get_event_class(classes, last_stats)

            dataset['data'].append({
                'tweet_id': tweet_id,
                'stats': last_stats,
                'vocabulary': np.array(vocabulary.get_words_codification(matched_tweet['main_word'] + matched_tweet['related_word'])),
                'publisher_page': np.array(get_source(tw.source_page)),
                'class': {
                    'favorites': tw_classes[0],
                    'retweets': tw_classes[1]
                }
            })

    with open(experiment_filename, 'wb') as experiment_file:
        pickle.dump(dataset, experiment_file)

    return dataset

def _build_experiment_w2v_skip(mabed_results, w2v_model, classes):
    """ [word2vec of words], [publisher] day of week -> class [3 classes between some numbers]"""
    experiment_filename = 'experiment_w2v_skip.pickle'
    dataset = {
        'data': [],
        'classes': classes
    }
    
    
    for result_no, result in enumerate(mabed_results):
        print("Event %s with %d matched tweets" % (result_no, len(result['matched_tweets'])))
        for matched_tweet in result['matched_tweets']:
            tweet_id = matched_tweet['tweet_id']
            tw = Tweet.objects.get(twitter_id=tweet_id)
            try:
                tw_stats = TweetStats.objects.get(twitter_id=tweet_id)
                last_stats = tw_stats.stats[-1].to_mongo().to_dict()
            except Exception:
                last_stats = {'favorites': tw.favorites, 'retweets': tw.retweets, 'at_time': tw.created_at}

            tw_classes = get_event_class(classes, last_stats)

            w2v_tweet = np.zeros((300,))
            count = 0
            for word in matched_tweet['main_word'] + matched_tweet['related_word']:
                try:
                    w2v_tweet += w2v_model.get_vector(word)
                    count +=1 
                except KeyError:
                    continue
                
            if count:
                w2v_tweet /= count
            
            dataset['data'].append({
                'tweet_id': tweet_id,
                'stats': last_stats,
                'words': w2v_tweet,
                'day': tw.created_at.weekday(),
                'publisher_page': np.array(get_source(tw.source_page)),
                'class': {
                    'favorites': tw_classes[0],
                    'retweets': tw_classes[1]
                }
            })

    with open(experiment_filename, 'wb') as experiment_file:
        pickle.dump(dataset, experiment_file)

    return dataset


def _build_experiment_w2v_random(mabed_results, w2v_model, classes):
    """ [word2vec of words], [publisher] day of week -> class [3 classes between some numbers]"""
    experiment_filename = 'experiment_w2v_random.pickle'
    dataset = {
        'data': [],
        'classes': classes
    }
    
    for result_no, result in enumerate(mabed_results):
        print("Event %s with %d matched tweets" % (result_no, len(result['matched_tweets'])))
        for matched_tweet in result['matched_tweets']:
            tweet_id = matched_tweet['tweet_id']
            tw = Tweet.objects.get(twitter_id=tweet_id)
            try:
                tw_stats = TweetStats.objects.get(twitter_id=tweet_id)
                last_stats = tw_stats.stats[-1].to_mongo().to_dict()
            except Exception:
                last_stats = {'favorites': tw.favorites, 'retweets': tw.retweets, 'at_time': tw.created_at}

            tw_classes = get_event_class(classes, last_stats)

            w2v_tweet = np.zeros((300,))
            count = 0
            for word in matched_tweet['main_word'] + matched_tweet['related_word']:
                try:
                    w2v_tweet += w2v_model.get_vector(word)
                except KeyError:
                    w2v_tweet += np.random.rand(300,)
                count +=1
                
            if count:
                w2v_tweet /= count
            
            dataset['data'].append({
                'tweet_id': tweet_id,
                'stats': last_stats,
                'words': w2v_tweet,
                'day': tw.created_at.weekday(),
                'publisher_page': np.array(get_source(tw.source_page)),
                'class': {
                    'favorites': tw_classes[0],
                    'retweets': tw_classes[1]
                }
            })

    with open(experiment_filename, 'wb') as experiment_file:
        pickle.dump(dataset, experiment_file)

    return dataset


def _build_experiment_w2v_skip_with_magniture(mabed_results, w2v_model, classes):
    """ [word2vec of words], [publisher] day of week -> class [3 classes between some numbers]"""
    experiment_filename = 'experiment_w2v_skip_with_magnitude.pickle'
    dataset = {
        'data': [],
        'classes': classes
    }
    
    
    for result_no, result in enumerate(mabed_results):
        print("Event %s with %d matched tweets" % (result_no, len(result['matched_tweets'])))
        for matched_tweet in result['matched_tweets']:
            tweet_id = matched_tweet['tweet_id']
            tw = Tweet.objects.get(twitter_id=tweet_id)
            try:
                tw_stats = TweetStats.objects.get(twitter_id=tweet_id)
                last_stats = tw_stats.stats[-1].to_mongo().to_dict()
            except Exception:
                last_stats = {'favorites': tw.favorites, 'retweets': tw.retweets, 'at_time': tw.created_at}

            tw_classes = get_event_class(classes, last_stats)

            w2v_tweet = np.zeros((300,))
            count = 0
            for word in matched_tweet['main_word'] + matched_tweet['related_word']:
                try:
                    w2v_tweet += w2v_model.get_vector(word) * _get_magnitude(result, word)
                    count +=1
                except KeyError:
                    continue
                
            if count:
                w2v_tweet /= count
            
            dataset['data'].append({
                'tweet_id': tweet_id,
                'stats': last_stats,
                'words': w2v_tweet,
                'day': tw.created_at.weekday(),
                'publisher_page': np.array(get_source(tw.source_page)),
                'class': {
                    'favorites': tw_classes[0],
                    'retweets': tw_classes[1]
                }
            })

    with open(experiment_filename, 'wb') as experiment_file:
        pickle.dump(dataset, experiment_file)

    return dataset


def _get_magnitude(event, word):
    for rw in event['event']['related_words']:
        if rw['word'] == word:
            return float(rw['magnitude'])
    
    return float(1)



def _build_experiment_w2v_skip_publisher_class(mabed_results, w2v_model, classes):
    """ [word2vec of words], [publisher] [day of week] [publisher_class] -> class [3 classes between some numbers]"""
    experiment_filename = 'experiment_w2v_w2v_skip_with_publisher_class.pickle'
    user_classes = {'bounds': [170, 340], 'values': [5336, 35234]}
    dataset = {
        'data': [],
        'classes': classes
    }
    
    for result_no, result in enumerate(mabed_results):
        print("Event %s with %d matched tweets" % (result_no, len(result['matched_tweets'])))
        for matched_tweet in result['matched_tweets']:
            tweet_id = matched_tweet['tweet_id']
            tw = Tweet.objects.get(twitter_id=tweet_id)
            try:
                tw_stats = TweetStats.objects.get(twitter_id=tweet_id)
                last_stats = tw_stats.stats[-1].to_mongo().to_dict()
            except Exception:
                last_stats = {'favorites': tw.favorites, 'retweets': tw.retweets, 'at_time': tw.created_at}

            tw_classes = get_event_class(classes, last_stats)

            w2v_tweet = np.zeros((300,))
            
            count = 0
            for word in matched_tweet['main_word'] + matched_tweet['related_word']:
                try:
                    w2v_tweet += w2v_model.get_vector(word) * _get_magnitude(result, word)
                    count +=1
                except KeyError:
                    continue
                
            if count:
                w2v_tweet /= count
            
            tw_user = TwitterUser.objects.get(twitter_id=tw.twitter_user_id)

            dataset['data'].append({
                'tweet_id': tweet_id,
                'stats': last_stats,
                'words': w2v_tweet,
                'day': tw.created_at.weekday(),
                'publisher_page': np.array(get_source(tw.source_page)),
                'user_class': get_user_class(tw_user, user_classes),
                'class': {
                    'favorites': tw_classes[0],
                    'retweets': tw_classes[1]
                }
            })

    with open(experiment_filename, 'wb') as experiment_file:
        pickle.dump(dataset, experiment_file)

    return dataset


def get_user_class(tw_user, classes):
    if tw_user.followers < classes['values'][0]:
        return 0

    if tw_user.followers < classes['values'][1]:
        return 1

    return 2


if __name__ == '__main__':
    load_environment()

    mabed_results = load_data('results_final_2500_2.json')
    # mabed_results = load_data('results_final_5000.pickle')
    classes = {'favorites': {'bounds': [13278, 26400], 'values': [15, 52]}, 'retweets': {'bounds': [13278, 26400], 'values': [11, 31]}}

    if len(sys.argv) == 1:
        print('Please add an experiment no')
        sys.exit(1)
        
    experiment_numbers = sys.argv[1:]
    
    w2v_model = None
    if any([True if int(exp_no) > 1 else False for exp_no in experiment_numbers]):
        w2v_model = gensim.models.KeyedVectors.load_word2vec_format('./GoogleNews-vectors-negative300.bin', binary=True)

    start = time.time()

    for experiment_no in experiment_numbers:
        
        if experiment_no == '1':
            vocabulary = Vocabulary(mabed_results)
            _build_experiment_one_hot_vectors(mabed_results, classes)
        elif experiment_no in ['2', '3', '4', '5']:    
            if experiment_no == '2':
                _build_experiment_w2v_skip(mabed_results, w2v_model, classes)
            if experiment_no == '3':
                _build_experiment_w2v_random(mabed_results, w2v_model, classes)
            if experiment_no == '4':
                _build_experiment_w2v_skip_with_magniture(mabed_results, w2v_model, classes)
            if experiment_no == '5':
                _build_experiment_w2v_skip_publisher_class(mabed_results, w2v_model, classes)
    elapsed = time.time() - start
    print(experiment_no, elapsed)
