import datetime
import logging
from urllib.parse import urlparse

import requests

from fetchers.daq_news.base_news_fetcher import BaseNewsFetcher
from models.news import News
from settings.settings import load_settings

BASE_URL = 'https://api.newsriver.io/v2/search'

logger = logging.getLogger()


class NewsRiverFetcher(BaseNewsFetcher):

    SOURCE = 'newsriver'

    def fetch_news(self, subject):
        response = requests.get(self._build_url(subject), headers={'Authorization': self._get_api_token()})
        if response.status_code == 200:
            content = response.json()
            for news in content:
                yield news
        else:
            logger.log(logging.ERROR, 'Could not fetch news for url: %s' % self._build_url(subject))
            return
            yield

    def _to_db_format(self, raw_news, category, subject):
        news_model_args = {
            'category': category,
            'subject': subject,
            'title': raw_news.get('title'),
            'content': raw_news.get('text'),
            'created_at': datetime.datetime.strptime(raw_news.get('discoverDate'), '%Y-%m-%dT%H:%M:%S.%f+0000'),
            'internal_source': self.SOURCE,
            'internal_source_id': raw_news.get('id'),
            'language': 'en',
        }
        external_source = self._extract_external_source(raw_news)
        if external_source:
            news_model_args['external_source'] = external_source
        else:
            logger.error('News without external resource %s ' % raw_news)

        return News(**news_model_args)

    def _extract_external_source(self, raw_news):
        url = raw_news.get('url')
        website = raw_news.get('website')
        external_source = None

        if not url:
            return external_source

        elif not website:
            parsed_uri = urlparse(raw_news['url'])
            netlocation = '{uri.netloc}'.format(uri=parsed_uri)

            if 'www.' in netlocation:
                index = 1
            else:
                index = 0

            external_source ={
                'name': netlocation.split('.')[index],
                'url': url
            }
        else:
            external_source = {
                'name': website.get('name', 'Missing Name'),
                'website': website.get('hostName', 'Missing Website'),
                'url': url
            }
        return external_source

    def _get_api_token(self):
        return load_settings()['news_river']['api_token']

    def _build_url(self, subject):
        return (BASE_URL + '?query=text%3A%22' + subject.replace(' ', '%20') +
                '%22AND%20language%3AEN&sortBy=discoverDate&sortOrder=DESC&limit=100')

    def _news_exists(self, raw_news):
        if News.objects(internal_source=self.SOURCE, internal_source_id=raw_news.get('id')):
            return True
        return False

    def _get_news_id(self, raw_news):
        return raw_news['id']


if __name__ == '__main__':
    NewsRiverFetcher().run()

