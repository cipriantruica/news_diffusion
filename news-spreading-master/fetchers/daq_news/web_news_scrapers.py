import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger()


class BaseScrapper(object):

    INVALID_URLS_CHECKS = []

    def __init__(self):
        super(BaseScrapper, self).__init__()

    def is_valid_url(self, url):
        for url_check in self.INVALID_URLS_CHECKS:
            if url_check in url:
                return False

        return True

    def fetch_news(self, url):
        pass


class DailyMailScrapper(BaseScrapper):

    INVALID_URLS_CHECKS = ['/video/']

    def fetch_news(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            logger.error('Failed to retrieve news from %s', url)
            return {}

        result = {}
        soup = BeautifulSoup(response.text, 'html.parser')

        story_content_element = soup.find('div', {'itemprop': 'articleBody'})
        if not story_content_element:
            logger.error('Url %s invalid configuration for story content', url)
            return {}

        content_paragraphs = story_content_element.findAll('p', {'class': 'mol-para-with-font'}, recursive=False)
        if not content_paragraphs:
            logger.error('Url %s invalid configuration for content paragraphs', url)
            return {}

        result['content'] = ''.join([p.text for p in content_paragraphs])

        return result


class FinancialPostScraper(BaseScrapper):

    def fetch_news(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            logger.error('Failed to retrieve news from %s', url)
            return {}

        result = {}
        soup = BeautifulSoup(response.text, 'html.parser')

        story_content_element = soup.find('div', {'id': 'story-main-content'})

        if not story_content_element:
            logger.error('Url %s invalid configuration for story content', url)
            return {}

        content_paragraphs = story_content_element.findAll('p', {'class': None})
        if not content_paragraphs:
            logger.error('Url %s invalid configuration for content paragraphs', url)
            return {}

        content_paragraphs = [p for p in content_paragraphs if 'mail' not in p.text]
        result['content'] = ''.join([p.text for p in content_paragraphs])

        return result


class TheTelegraphScraper(BaseScrapper):

    def fetch_news(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            logger.error('Failed to retrieve news from %s', url)
            return {}

        result = {}
        soup = BeautifulSoup(response.text, 'html.parser')

        story_content_elements = soup.findAll('div', {'class': 'articleBodyText'})
        if not story_content_elements:
            logger.error('Url %s invalid configuration for story content', url)
            return {}

        content_paragraphs = []
        for story_content_element in story_content_elements:
            content_paragraphs.extend(story_content_element.findAll('p', {'class': None}))
        if not content_paragraphs:
            logger.error('Url %s invalid configuration for content paragraphs', url)
            return {}
        result['content'] = ''.join([p.text for p in content_paragraphs])

        return result


class WashingtonTimesScraper(BaseScrapper):

    def fetch_news(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            logger.error('Failed to retrieve news from %s', url)
            return {}

        result = {}
        soup = BeautifulSoup(response.text, 'html.parser')

        story_content_element = soup.find('div', {'class': 'bigtext'})
        if not story_content_element:
            logger.error('Url %s invalid configuration for story content', url)
            return {}

        content_paragraphs = story_content_element.findAll('p', {'class': None}, recursive=False)
        if not content_paragraphs:
            logger.error('Url %s invalid configuration for content paragraphs', url)
            return {}
        result['content'] = ''.join([p.text for p in content_paragraphs])

        return result


class ReutersScraper(BaseScrapper):

    def fetch_news(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            logger.error('Failed to retrieve news from %s', url)
            return {}

        result = {}
        soup = BeautifulSoup(response.text, 'html.parser')

        story_content_element = soup.find('div', {'class': 'StandardArticleBody_body'})
        if not story_content_element:
            logger.error('Url %s invalid configuration for story content', url)
            return {}

        content_paragraphs = story_content_element.findAll('p', {'class': None}, recursive=False)
        if not content_paragraphs:
            logger.error('Url %s invalid configuration for content paragraphs', url)
            return {}
        result['content'] = ''.join([p.text for p in content_paragraphs])

        return result


class NewYorkTimesScraper(BaseScrapper):

    def fetch_news(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            logger.error('Failed to retrieve news from %s', url)
            return {}

        result = {}
        soup = BeautifulSoup(response.text, 'html.parser')

        content_paragraphs = soup.findAll('p', {'class': 'css-1ygdjhk evys1bk0'})
        if not content_paragraphs:
            logger.error('Url %s invalid configuration for content paragraphs', url)
            return {}

        result['content'] = ''.join([p.text for p in content_paragraphs])
        return result


class BBCScraper(BaseScrapper):

    INVALID_URLS_CHECKS = ['/sport/', '/av/']

    def fetch_news(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            logger.error('Failed to retrieve news from %s', url)
            return {}

        result = {}
        soup = BeautifulSoup(response.text, 'html.parser')
        story_element = soup.find('div', {'class': 'story-body'})
        if not story_element:
            logger.error('Url %s invalid configuration for story', url)
            return result

        story_content_element = story_element.find('div', {'class': 'story-body__inner'})
        if not story_content_element:
            logger.error('Url %s invalid configuration for story content', url)
            return {}

        content_paragraphs = story_content_element.findAll('p', {'class': None}, recursive=False)
        if not content_paragraphs:
            logger.error('Url %s invalid configuration for content paragraphs', url)
            return {}
        content = ''.join([p.text for p in content_paragraphs])
        result['content'] = content

        return result
