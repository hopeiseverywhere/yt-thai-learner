from utils.dict_util import load_dictionary_from_file, index_by_thai, \
    search_headwords_only
from config.settings import settings


class DictionaryService:
    def __init__(self, file: str):
        self.entries = None
        self.index = None
        self.csv_type = "auto"
        self.load_dictionary(file)

    def load_dictionary(self, file: str, csv_type: str = "auto"):
        if self.entries is None:
            print("Loading dictionary...")
            self.entries = load_dictionary_from_file(file, csv_type)
            self.index = index_by_thai(self.entries)
            print("Dictionary loaded!")

    def search_word(self, word: str):
        return search_headwords_only(self.entries, word)


# Singleton instance
dict_service_freq = DictionaryService(settings.dict_file_freq)
dict_service_full = DictionaryService(settings.dict_file_full)