from mongoengine import Document, StringField, IntField, DateTimeField


class TwitterUser(Document):
    meta = {
        'auto_create_index': True,
        'indexes': [
            'twitter_id',
        ]
    }

    twitter_id = StringField(required=True)
    name = StringField(default='')
    screen_name = StringField(default='')
    description = StringField(default='')
    location = StringField(default='')

    favourites = IntField(required=True, default=0)
    friends = IntField(required=True, default=0)
    followers = IntField(required=True, default=0)
    statuses = IntField(required=True, default=0)
    listed = IntField(required=True, default=0)
    created_at = DateTimeField(required=True)
    language = StringField()
