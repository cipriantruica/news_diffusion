from mongoengine import Document, StringField, IntField, DateTimeField, EmbeddedDocument, EmbeddedDocumentListField


class TwitterStat(EmbeddedDocument):

    favorites = IntField(required=True, min_value=0, default=0)
    retweets = IntField(required=True, min_value=0, default=0)
    at_time = DateTimeField(required=True)


class TweetStats(Document):

    twitter_id = StringField(required=True, primary_key=True)
    stats = EmbeddedDocumentListField(TwitterStat, default=[])

