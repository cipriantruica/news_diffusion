from mock import patch, Mock

from core.base_backend_test import BaseBackendTest
from fetchers.daq_news.news_api_fetcher import NewsApiFetcher
from fetchers.daq_news.tests.fixtures.news import generate_bbc_test_fixtures
from models.news import News


class MyTestClass(BaseBackendTest):

    @patch('fetchers.daq_news.web_news_scrapers.requests.get')
    def test_news_api_bbc_source(self, requests_get_mock):
        news_api_article, html_fixture_page, expected_news_content = generate_bbc_test_fixtures()

        response_mock = Mock()
        response_mock.status_code = 200
        response_mock.text = html_fixture_page

        requests_get_mock.return_value = response_mock

        NewsApiFetcher()._process_single_news(news_api_article, 'category', 'subject')

        db_news = News.objects[0]
        self.assertEquals('category', db_news.category, 'Invalid category in db')
        self.assertEquals('subject', db_news.subject, 'Invalid subject in db')
        self.assertEquals('Herman Cain withdraws Federal Reserve bid', db_news.title, 'Invalid category in db')
        self.assertEquals('newsapi', db_news.internal_source, 'Invalid category in db')
        self.assertEquals('herman_cain_withdraws_federal_reserve_bid', db_news.internal_source_id,
                          'Invalid category in db')
        self.assertEquals('BBC News', db_news.external_source.name, 'Invalid external source name in db')
        self.assertEquals('http://www.bbc.co.uk/news/world-us-canada-48017273', db_news.external_source.url,
                          'Invalid external source url in db')
        self.assertEquals(expected_news_content, db_news.content,
                          'Invalid content in db')
