import csv

from core.connect_db import connect_db
from models.tweet import Tweet
from models.twitter_user import TwitterUser
from settings.settings import load_settings

if __name__ == '__main__':
    settings = load_settings()
    mongo_config = settings['dbs']['mongo']
    con = connect_db(**mongo_config)

    formed_tweets = []

    twitter_users_mapping = {user.twitter_id: user.screen_name for user in TwitterUser.objects}

    for tweet in Tweet.objects:
        if tweet.twitter_user_id in twitter_users_mapping:
            tweet_author_name = twitter_users_mapping[tweet.twitter_user_id]
        else:
            tweet_author_name = 'UNKNOWN'
        formed_tweet_text = tweet.text

        for char in ['\n', '\r', '…']:
            formed_tweet_text.replace(char, '')
        formed_tweets.append([formed_tweet_text, str(tweet.created_at), tweet_author_name])

    print(len(formed_tweets))

    with open('tweets.csv', 'w') as tweets_file:
        writer = csv.writer(tweets_file, delimiter=',')
        writer.writerow(['text', 'date', 'author'])
        for line in formed_tweets:
            writer.writerow(line)
