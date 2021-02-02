import logging
import time

from fetchers.base_fetcher import BaseFetcher
from settings.settings import load_settings


logger = logging.getLogger()

class BaseNewsFetcher(BaseFetcher):
    SOURCE = None

    def __init__(self):
        super(BaseNewsFetcher, self).__init__()
        if not self.SOURCE:
            raise Exception('Please declare SOURCE field on fetcher')

    def _run(self):
        while True:
            for category, subjects in self._get_topics().items():
                for subject in subjects:
                    logging.debug('Fetching news for %s - %s' % (category, subject))
                    for news in self.fetch_news(subject):
                        self._process_single_news(news, category, subject)
            time.sleep(2 * 3600)

    def _process_single_news(self, news, category, subject):
        if self._news_exists(news):
            logger.info('News from %s with id: %s already exists' % (self.SOURCE,
            self._get_news_id(news)))
        else:
            self._process_news(news)
            model = self._to_db_format(news, category, subject)
            if model:
                try:
                    model.save()
                    logger.info('Successfully saved news: %s' % model.to_json())
                except Exception as e:
                    logging.error("Error %s saving the model: %s" % (e, model.to_json()))

    def _get_topics(self):
        settings = load_settings()
        return settings['topics']

    def fetch_news(self, subject):
        raise NotImplementedError()

    def _process_news(self, news):
        pass

    def _to_db_format(self, raw_news, category, subject):
        raise NotImplementedError()

    def _news_exists(self, raw_news):
        raise NotImplementedError()

    def _get_news_id(self, raw_news):
        raise NotImplementedError()
