import datetime
import logging
import time

import mongoengine
import requests
import twitter

from fetchers.base_fetcher import BaseFetcher
from models.tweet import Tweet
from models.tweet_stats import TweetStats, TwitterStat
from models.twitter_user import TwitterUser
from models.twitter_user_stats import TwitterUserStats, TwitterUserStat
from settings.settings import load_settings


logger = logging.getLogger()


class TwitterFetcher(BaseFetcher):

    SLEEP_TIME = 10
    MAX_FETCHING_TWEETS = 3200

    def __init__(self):
        super(TwitterFetcher, self).__init__()
        self.settings = load_settings()
        self.tw_client = twitter.Api(consumer_key=self.settings['twitter']['credentials']['consumer_key'],
                                     consumer_secret=self.settings['twitter']['credentials']['consumer_secret'],
                                     access_token_key=self.settings['twitter']['credentials']['access_token'],
                                     access_token_secret=self.settings['twitter']['credentials']['access_token_secret'])
        self.current_twitter_page = None

    def _run(self):
        for tw_page in self.settings['twitter']['pages']:
            self.current_twitter_page = tw_page

            new_tweets, new_users = 0, 0
            last_tweet_id = None
            fetched_tweets = 0
            current_tweet_id = None

            logger.info('Fetching tweets from %s' % tw_page)
            while self._should_fetch_more_tweets(fetched_tweets, last_tweet_id, current_tweet_id):
                logger.info('Fetching tweets from %s with max_id %s' % (tw_page, last_tweet_id))
                current_tweet_id = last_tweet_id

                try:
                    tweets = self.tw_client.GetUserTimeline(screen_name=tw_page, count=200, max_id=last_tweet_id)
                except Exception as e:
                    logger.error('Received error while fetching tweets for page %s: %r' % (tw_page, e))
                    break

                for tweet in tweets:
                    fetched_tweets += 1

                    if tweet.retweeted_status:
                        inserted_data = self._handle_tweet_post(tweet.retweeted_status)
                        new_tweets += inserted_data[0]
                        new_users += inserted_data[1]

                    inserted_data = self._handle_tweet_post(tweet)
                    new_tweets += inserted_data[0]
                    new_users += inserted_data[1]
                    last_tweet_id = tweet.id_str

            logger.info('For Twitter Page %s inserted %d new tweets and %d new users' % (tw_page, new_tweets, new_users))
            time.sleep(self.SLEEP_TIME)

    def _should_fetch_more_tweets(self, fetched_tweets, last_tweet_id, current_tweet_id):
        if last_tweet_id is None and current_tweet_id is None:
            return True

        if fetched_tweets >= self.MAX_FETCHING_TWEETS or last_tweet_id == current_tweet_id:
            return False

        return True

    def _handle_tweet_post(self, tweet):
        new_tweets, new_users = 0, 0
        if self._handle_tweet(tweet):
            new_tweets = 1

        if self._handle_twitter_user(tweet.user):
            new_users = 1

        return new_tweets, new_users

    def _handle_tweet(self, tweet):
        if Tweet.objects.filter(twitter_id=tweet.id_str):
            return self._update_tweet_stats(tweet)

        tweet_model = {
            'twitter_id': tweet.id_str,
            'source_page': self.current_twitter_page,
            'twitter_user_id': tweet.user.id_str,
            'text': tweet.retweeted_status.text if tweet.retweeted else tweet.text,
            'hashtags': [th.AsDict() for th in tweet.hashtags],
            'user_mentions': [tm.AsDict() for tm in tweet.user_mentions],
            'urls': [tu.AsDict() for tu in tweet.urls],
            'favorites': tweet.favorite_count,
            'retweets': tweet.retweet_count,
            'is_retweet': tweet.retweeted_status is not None,
            'retweet_id': tweet.retweeted_status.id_str if tweet.retweeted_status is not None else None,
            'language': tweet.lang,
            'location': tweet.location,
            'created_at': datetime.datetime.strptime(tweet.created_at, '%a %b %d %H:%M:%S +0000 %Y')
        }

        for url in tweet_model['urls']:
            url.update({'extended_url': self._unshorten_url(url['url'])})

        logger.info('Inserting new Tweet %r' % tweet_model)
        return Tweet(**tweet_model).save()

    def _update_tweet_stats(self, new_tweet):
        new_stats = {
            'retweets': new_tweet.retweet_count,
            'favorites': new_tweet.favorite_count,
        }
        # Fetch or create tweet stats
        try:
            tweet_stats = TweetStats.objects.get(twitter_id=new_tweet.id_str)
        except mongoengine.DoesNotExist:
            tweet_stats = TweetStats(twitter_id=new_tweet.id_str)

        # Compute last tweet stats
        db_tweet = Tweet.objects.get(twitter_id=new_tweet.id_str)
        if tweet_stats.stats:
            db_last_stats = tweet_stats.stats[-1]
            last_stats = {'retweets': db_last_stats.retweets,
                          'favorites': db_last_stats.favorites}
        else:
            last_stats = {'retweets': db_tweet.retweets,
                          'favorites': db_tweet.favorites}

        if new_stats != last_stats:
            new_stats['at_time'] = datetime.datetime.now()
            tweet_stats.stats.append(TwitterStat(**new_stats))
            logger.error('Updated stats for Twitter Tweet: %s', new_tweet.id_str)
            return tweet_stats.save()

        return None

    def _unshorten_url(self, url):
        if not url:
            return None

        try:
            response = requests.head(url)
        except Exception as e:
            logger.error('Invalid url: %s. Error %r', url, e)
            return ''

        status_code_category = int(response.status_code / 100)
        if status_code_category == 2:
            return url
        elif status_code_category in [4, 5]:
            return ''
        elif status_code_category == 3:
            next_url = response.headers.get('Location')
            if not next_url:
                next_url = response.headers.get('location')

            return self._unshorten_url(next_url)

    def _handle_twitter_user(self, user):
        if TwitterUser.objects.filter(twitter_id=user.id_str):
            return self._update_user_stats(user)

        twitter_user = {
            'twitter_id': user.id_str,
            'name': user.name,
            'screen_name': user.screen_name,
            'description': user.description,
            'location': user.location,
            'favourites': user.favourites_count,
            'followers': user.followers_count,
            'friends': user.friends_count,
            'listed': user.listed_count,
            'statuses': user.statuses_count,
            'created_at': datetime.datetime.strptime(user.created_at, '%a %b %d %H:%M:%S +0000 %Y'),
            'language': user.lang
        }

        logger.info('Inserting new Twitter user %r' % twitter_user)
        return TwitterUser(**twitter_user).save()

    def _update_user_stats(self, user):
        new_stats = {
            'favourites': user.favourites_count,
            'followers': user.followers_count,
            'friends': user.friends_count,
            'listed': user.listed_count,
            'statuses': user.statuses_count
        }

        # Fetch or create twitter user stats
        try:
            user_stats = TwitterUserStats.objects.get(twitter_id=user.id_str)
        except mongoengine.DoesNotExist:
            user_stats = TwitterUserStats(twitter_id=user.id_str)

        # Compute last twitter user stats
        db_user = TwitterUser.objects.get(twitter_id=user.id_str)
        if user_stats.stats:
            db_last_stats = user_stats.stats[-1]
            last_stats = {'favourites': db_last_stats.favourites,
                          'followers': db_last_stats.followers,
                          'friends': db_last_stats.friends,
                          'listed': db_last_stats.listed,
                          'statuses': db_last_stats.statuses}
        else:
            last_stats = {'favourites': db_user.favourites,
                          'followers': db_user.followers,
                          'friends': db_user.friends,
                          'listed': db_user.listed,
                          'statuses': db_user.statuses}

        if new_stats != last_stats:
            new_stats['at_time'] = datetime.datetime.now()
            user_stats.stats.append(TwitterUserStat(**new_stats))
            logger.error('Updated stats for Twitter User: %s', user.id_str)
            return user_stats.save()

        return None


if __name__ == '__main__':
    TwitterFetcher().run()
