import datetime
import json
import os
import pickle
import sys
import time

# import plotly.graph_objs as go
# from plotly.offline import plot

from models.tweet import Tweet
from models.tweet_stats import TweetStats
from settings.settings import load_environment

TWEETS_THREASHOLD = 0.3


TMP_EVENT_DATA_TEMPLATE = 'identified_%s_tweets.pickle'

def get_file_name(mabed_file):
    return mabed_file.split('.')[0]

def load_data(mabed_file):
    event_results = None

    mabed_filename = get_file_name(mabed_file)
    tmp_file = TMP_EVENT_DATA_TEMPLATE % get_file_name(mabed_filename)
    if os.path.isfile(tmp_file):
        with open(tmp_file, 'rb') as tmp_result:
            event_results = pickle.load(tmp_result)
    else:
        with open(mabed_file, 'r') as events_in:
            events = json.load(events_in)

        if not events:
            sys.exit(1)

        event_results = []
        for event_no, event in enumerate(events):
            print('event number %s ' % event_no)
            start_ts = _get_timestamp_from_date(event['start_date'])
            end_ts = _get_timestamp_from_date(event['end_date'])
            tweets = Tweet.objects(created_at__gte=datetime.datetime.fromtimestamp(start_ts),
                                   created_at__lte=datetime.datetime.fromtimestamp(end_ts + 86400 * 61))

            matched_tweets = []

            for tweet in tweets:
                main_words_found = []
                related_words_found = []

                for main_word in event['main_words']:
                    if main_word in tweet.text:
                        main_words_found.append(main_word)

                for related_word in event['related_words']:
                    if related_word['word'] in tweet.text:
                        related_words_found.append(related_word['word'])

                if len(event['main_words'] + event['related_words']) * 0.2 < len(related_words_found + main_words_found):
                    matched_tweets.append({'main_word': main_words_found, 'related_word': related_words_found,
                                           'tweet_id': tweet.twitter_id})

            event_results.append({'event': event, 'matched_tweets': matched_tweets})

        with open(tmp_file, 'wb') as tmp_result:
            pickle.dump(event_results, tmp_result)

    return event_results


def _get_latest_stats(stats, day):
    previous_stats = None

    for stat in stats:
        if stat.at_time.timestamp() > day + 86399:
            break
        previous_stats = stat

    if not previous_stats:
        return {
            'favorites': 0,
            'retweets': 0
        }

    return {
        'favorites': previous_stats.favorites,
        'retweets': previous_stats.retweets,
    }


def _get_timestamp_from_date(date):
    parsed_date = date.split(' ')[0]
    return int(time.mktime(datetime.datetime.strptime(parsed_date, "%Y-%m-%d").timetuple()))


def _compute_stats_for_event(event_with_tweets):
    event = event_with_tweets['event']

    start_ts = _get_timestamp_from_date(event['start_date'])
    end_ts = _get_timestamp_from_date(event['end_date']) + 86400 * 61

    event_days = [ts for ts in range(start_ts, end_ts+1, 86400)]
    tweet_stats_by_id = {tweet_stats.twitter_id: tweet_stats for tweet_stats in
                         TweetStats.objects(
                             twitter_id__in=[tweet['tweet_id'] for tweet in event_with_tweets['matched_tweets']]
                         )}

    stats = {}
    for day in event_days:
        if day > int(time.time()):
            break

        day_stats = {
            'total': {'favorites': 0, 'retweets': 0}
        }

        for matched_event in event_with_tweets['matched_tweets']:
            tweet_id = matched_event['tweet_id']
            tweet_stats = tweet_stats_by_id.get(tweet_id)
            if not tweet_stats:
                continue

            tweet_stats_list = tweet_stats.stats

            latest_stats = _get_latest_stats(tweet_stats_list, day)
            day_stats[tweet_id] = {'favorites': latest_stats['favorites'], 'retweets': latest_stats['retweets']}
            day_stats['total'] = {
                'favorites': day_stats['total']['favorites'] + latest_stats['favorites'],
                'retweets': day_stats['total']['retweets'] + latest_stats['retweets']
            }

        stats[day] = day_stats

    return stats


def _plot_event(event_stats, event, plot_filename):

    sorted_days_ts = sorted(event_stats.keys())
    sorted_days = [datetime.datetime.fromtimestamp(ts) for ts in sorted_days_ts]

    favorites_values = [stats[day]['total']['favorites'] for day in sorted_days_ts]
    retweets_values = [stats[day]['total']['retweets'] for day in sorted_days_ts]

    # plot fav
    if len(set(favorites_values)) > 1:
        output_plot_filename = '%s_favorites.html' % plot_filename
        trace = go.Scatter(
            x=sorted_days,
            y=favorites_values
        )

        layout = dict(
            title='Event defined by words (%s - %s)' % (event['main_words'], [r_w['word'] for r_w in event['related_words']]),
            xaxis=dict(title='Day'),
            yaxis=dict(title='favorites')
        )

        data = [trace]
        print(plot(dict(data=data, layout=layout), filename=output_plot_filename, auto_open=False))

    # plot retweets
    if len(set(retweets_values)) > 1:
        output_plot_filename = '%s_retweets.html' % plot_filename
        trace = go.Scatter(
            x=sorted_days,
            y=retweets_values
        )

        layout = dict(
            title='Event defined by words (%s - %s)' % (event['main_words'], [r_w['word'] for r_w in event['related_words']]),
            xaxis=dict(title='Day'),
            yaxis=dict(title='favorites')
        )

        data = [trace]
        print(plot(dict(data=data, layout=layout), filename=output_plot_filename, auto_open=False))


if __name__ == '__main__':
    load_environment()

    for mabed_file in sys.argv[1:]:
        file_name = get_file_name(mabed_file)
        tweets_by_event = load_data(mabed_file)







