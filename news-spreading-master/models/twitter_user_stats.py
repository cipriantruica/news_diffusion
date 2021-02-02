from mongoengine import Document, StringField, IntField, DateTimeField, EmbeddedDocument, EmbeddedDocumentListField


class TwitterUserStat(EmbeddedDocument):

    favourites = IntField(required=True, min_value=0, default=0)
    friends = IntField(required=True, min_value=0, default=0)
    followers = IntField(required=True, min_value=0, default=0)
    statuses = IntField(required=True, min_value=0, default=0)
    listed = IntField(required=True, min_value=0, default=0)
    at_time = DateTimeField(required=True)


class TwitterUserStats(Document):

    twitter_id = StringField(required=True, primary_key=True)
    stats = EmbeddedDocumentListField(TwitterUserStat, default=[])
