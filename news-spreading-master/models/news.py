from mongoengine import Document, StringField, DateTimeField, EmbeddedDocument, EmbeddedDocumentField


class ExternalSource(EmbeddedDocument):
    name = StringField()
    url = StringField(required=True)
    website = StringField()


class News(Document):

    meta = {
        'auto_create_index': True,
        'indexes': [
            '$title',
            'external_source.name',
            {
                'fields': ['category', 'subject']
            },
            {
                'fields': ['internal_source', 'internal_source_id'],
                'unique': True
            }
        ]
    }

    category = StringField(required=True)
    subject = StringField(required=True)
    title = StringField(required=True)
    content = StringField(required=True)
    internal_source = StringField(required=True)
    internal_source_id = StringField(required=True)
    language = StringField()
    created_at = DateTimeField(required=True)
    external_source = EmbeddedDocumentField(ExternalSource)



