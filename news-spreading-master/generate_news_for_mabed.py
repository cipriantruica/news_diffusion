import csv

from core.connect_db import connect_db
from models.news import News
from settings.settings import load_settings

if __name__ == '__main__':
    settings = load_settings()
    mongo_config = settings['dbs']['mongo']
    con = connect_db(**mongo_config)

    formed_news = []

    for news in News.objects:
        source = news.external_source
        formed_news_text = news.content

        formed_news_text = ' '.join(formed_news_text.splitlines())
        for char in ['\n', '\r', '…', '\t', ',', '\'', '"']:
            formed_news_text = formed_news_text.replace(char, '')

        for exclude_string in ['Media Contact:', 'To learn more']:
            index = formed_news_text.find(exclude_string)
            if index:
                formed_news_text = formed_news_text[:index]

        if not formed_news_text or not str(news.created_at):
            continue

        formed_news.append([formed_news_text, news.created_at.strftime('%Y-%m-%d %H:%M:%S'), source.name])

    print(len(formed_news))

    with open('news.csv', 'w') as tweets_file:
        writer = csv.writer(tweets_file, delimiter=',')
        writer.writerow(['text', 'date', 'author'])
        for line in formed_news:
            writer.writerow(line)
