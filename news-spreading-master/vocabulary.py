

class Vocabulary(object):
    _main_words = []
    _related_words = []
    _all_words = []

    def __init__(self, mabed_results):
        super().__init__()
        main_words = []
        related_words = []

        for result in mabed_results:
            event = result['event']
            main_words += event['main_words']
            related_words += [rw['word'] for rw in event['related_words']]

        self._main_words = list(set([s.lower() for s in main_words]))
        self._related_words = list(set([s.lower() for s in related_words]))
        self._all_words = self._main_words + self._related_words

    def get_main_words(self):
        return self._main_words

    def get_main_words(self):
        return self.get_related_words

    def get_words_codification(self, words):
        def word_codif(word, words):
            return 1 if word in words else 0

        return [word_codif(w, words) for w in self._all_words]

    def get_words_magnitude_codification(self, event, tweet):
        related_words = {rw['word']: rw['magnitude'] for rw in event['related_words']}
        return [1 if w in event['main_words'] else 0 for w in self._main_words] + [
            related_words[rw] if rw in related_words else 0 for rw in self._related_words
        ]

    def get_number_of_words(self):
        return len(self._all_words)
