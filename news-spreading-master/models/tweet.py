from mongoengine import Document, StringField, IntField, DateTimeField, ListField, EmbeddedDocument, BooleanField, EmbeddedDocumentListField


class Url(EmbeddedDocument):

    expanded_url = StringField(required=True, default='')
    url = StringField(required=True, default='')
    extended_url = StringField(required=True, default='')
    indices = ListField(IntField, default=[])


class UserMention(EmbeddedDocument):

    screen_name = StringField(required=True, default='')
    name = StringField(required=True, default='')
    id_str = StringField(required=True, default='')
    indices = ListField(IntField, default=[])

class Hashtag(EmbeddedDocument):
    text = StringField(required=True, default='')
    indices = ListField(IntField, default=[])


class Tweet(Document):
    #meta = {
    #    'auto_create_index': True,
    #    'indexes': [
    #        'twitter_id',
    #        'twitter_user_id',
    #        'source_page'
    #    ]
    #}

    twitter_id = StringField(required=True, primary_key=True)
    source_page = StringField(required=True, default='')
    twitter_user_id = StringField(required=True)
    text = StringField(required=True)
    hashtags = EmbeddedDocumentListField(Hashtag, default=[])
    urls = EmbeddedDocumentListField(Url, default=[])
    user_mentions = EmbeddedDocumentListField(UserMention, default=[])
    favorites = IntField(required=True)
    retweets = IntField(required=True)
    is_retweet = BooleanField(default=False)
    retweet_id = StringField()
    language = StringField()
    location = StringField()
    created_at = DateTimeField(required=True)
