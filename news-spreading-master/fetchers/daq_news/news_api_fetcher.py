# coding=utf-8
import datetime
import logging
import re

from newsapi import NewsApiClient

from fetchers.daq_news.base_news_fetcher import BaseNewsFetcher
from fetchers.daq_news.web_news_scrapers import (BBCScraper, NewYorkTimesScraper, ReutersScraper, WashingtonTimesScraper,
                                                 TheTelegraphScraper, FinancialPostScraper, DailyMailScrapper)
from models.news import News
from settings.settings import load_settings

logger = logging.getLogger()


class NewsApiFetcher(BaseNewsFetcher):

    SOURCE = 'newsapi'

    def __init__(self):
        super(NewsApiFetcher, self).__init__()
        self.newsapi_client = NewsApiClient(api_key=self._get_api_token())
        self.source_scrapper_handlers = {
            'bbc-news': BBCScraper,
            'the-new-york-times': NewYorkTimesScraper,
            'reuters': ReutersScraper,
            'the-washington-times': WashingtonTimesScraper,
            'the-telegraph': TheTelegraphScraper,
            'financial-post': FinancialPostScraper,
            'daily-mail': DailyMailScrapper
        }

    def fetch_news(self, subject):
        sources = self._get_sources()
        response = self.newsapi_client.get_everything(q=subject, sources=sources,
                                                      page_size=100, language='en')
        if response['status'] != 'ok':
            return
            yield

        for news in response['articles']:
            if news.get('description'):
                yield news

    def _to_db_format(self, raw_news, category, subject):
        external_source = self._extract_external_source(raw_news)
        if not external_source:
            logger.info('News without external source %s' % raw_news)
            return None

        try:
            news_from_external_resource = self.fetch_news_from_external_source(raw_news)
        except Exception:
            logger.error('News with wrong format on external source %s' % raw_news)
            news_from_external_resource = {}

        if 'content' not in news_from_external_resource:
            logger.info('News without content: %s' % raw_news)
            return

        news_model_args = {
            'category': category,
            'subject': subject,
            'title': raw_news.get('title'),
            'content': news_from_external_resource['content'],
            'created_at': datetime.datetime.strptime(raw_news.get('publishedAt'), '%Y-%m-%dT%H:%M:%SZ'),
            'internal_source': self.SOURCE,
            'internal_source_id': self._get_news_id(raw_news),
            'language': 'en',
            'external_source': external_source
        }
        return News(**news_model_args)

    def _get_api_token(self):
        return load_settings()['news_api']['api_token']

    def _get_sources(self):
        return ', '.join(load_settings()['news_api']['sources'])

    def _extract_external_source(self, raw_news):
        return {
            'name': raw_news['source']['name'],
            'url': raw_news['url']
        }

    def _news_exists(self, raw_news):
        if News.objects(internal_source=self.SOURCE, internal_source_id=self._get_news_id(raw_news)):
            return True
        return False

    def _get_news_id(self, raw_news):
        regex = re.compile('[^a-zA-Z ]')
        id = regex.sub('', raw_news['title'])
        id = id.lower().replace(' ', '_')
        return id

    def _process_content(self, content):
        new_content = content.replace('…', '')
        return new_content

    def fetch_news_from_external_source(self, news):
        url = news.get('url')
        if not url:
            logger.error('News without URL: %s', news)
            return

        source_id = news.get('source', {}).get('id')
        if not source_id:
            return

        handler_class = self.source_scrapper_handlers.get(source_id)
        handler = handler_class()
        news_info = {}
        if handler.is_valid_url(url):
            news_info = handler.fetch_news(url)

        return news_info

if __name__ == '__main__':
    NewsApiFetcher().run()

