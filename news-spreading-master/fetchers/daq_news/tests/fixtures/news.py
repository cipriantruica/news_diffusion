import codecs


def generate_bbc_test_fixtures():
    news_api_article = {
        "source": {
            "id": "bbc-news",
            "name": "BBC News"
        },
        "author": "BBC News",
        "title": "Herman Cain withdraws Federal Reserve bid",
        "description": "President Trump tweeted that he would respect Mr Cain's wishes and not pursue the nomination.",
        "url": "http://www.bbc.co.uk/news/world-us-canada-48017273",
        "urlToImage": "https://ichef.bbci.co.uk/news/1024/branded_news/15577/production/_106551478_gettyimages-137361799.jpg",
        "publishedAt": "2019-04-22T18:26:53Z",
        "content": "bla bla content"
    }

    html_fixture_page = _read_html_fixture('bbc')
    expected_news_content = 'The president said he would respect the former pizza chain executive\'s wishes and not pursue Mr Cain\'s nomination to join America\'s central bank. "My friend Herman Cain, a truly wonderful man, has asked me not to nominate him", Mr Trump wrote. Mr Trump first announced he intended to nominate Mr Cain earlier this month. Though the president did not formally nominate Mr Cain to the seven-member board, the announcement prompted backlash among Democrats and some Republicans in Congress.  It is unclear why Mr Cain withdrew his name for consideration. The president has been accused of putting forward political loyalists to the Fed.Arguably the world\'s most influential bank, it is traditionally an independent body.The president is a fierce critic of the central bank, and has also often called for lower interest rates - his predecessors have largely refrained from trying to sway monetary policy.Mr Cain would have required almost total Republican support in the Senate to be confirmed. As of last week, four of 53 Republican senators announced they plan to vote against him. Mitt Romney of Utah, Lisa Murkowski of Alaska, Cory Gardner of Colorado and North Dakota\'s Kevin Cramer all indicated they would vote no on the nomination.Mr Cain, a former executive of Godfather\'s Pizza, made a bid for the Republican presidential nomination in 2012, but dropped out amid allegations of sexual misconduct, which he denied. He is often remembered for his 9-9-9 tax reform plan during his campaign, and this viral campaign video by an adviser.He served as the chairman of the Kansas City Federal Bank from 1989 to 1991.'
    return news_api_article, html_fixture_page, expected_news_content


def _read_html_fixture(source):
    f = codecs.open('fetchers/daq_news/tests/fixtures/%s_news.html' % source, 'r')
    return f.read()
