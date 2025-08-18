from pythainlp.tokenize import word_tokenize
from pythainlp.transliterate import romanize
from pythainlp.transliterate import transliterate

from services.dictionary_service import DictionaryService
from services.subtitle_alignment_service import subtitle_alignment_service
from utils.dict_util import load_dictionary_from_file, index_by_thai, \
    search_headwords_only
from utils.word_util import process_thai_word
import time
from config.settings import settings


# entries = load_dictionary_from_file("data/thai-eng-telex.csv")
entries = load_dictionary_from_file("data/thai-freq-matches.csv", "freq")
index = index_by_thai(entries)
word_to_search = "ติดตาม"
result = search_headwords_only(entries, word_to_search)
print(result)
# print(result.get_english_translations())

dict_service = DictionaryService(settings.dict_file_freq)
dict_service2 = DictionaryService(settings.dict_file_full)

sample = "คิดถึงวิวมิ้มประเมินประเมินสถานการณ์"
text1 = romanize(sample)
print(text1)
# text2 = transliterate(sample, engine="tltk_g2p")
# print("tltk_g2p", text2)
# text2 = transliterate(sample, engine="ipa")
# print("ipa", text2)
text2 = transliterate(sample, engine="icu")
print("icu", text2)
# text2 = transliterate(sample, engine="iso_11940")
# print("iso_11940", text2)

print("\nTokenize breakdown: --------")
lis = word_tokenize(sample)

print(lis)
for word in lis:
#     # entry = index.get(word, [None])[0]
#     # eng = entry.e_entry if (entry and entry.e_entry) else "(no English gloss)"
#
#     # res = search_headwords_only(entries, word)
#     # print(word, transliterate(word, engine="icu"),
#     #       res.get_english_translations())
    print(process_thai_word(word, dict_service))

print("\nNormalization aka keep_whitespace=False:")
print(word_tokenize(sample, keep_whitespace=False))

print("Process subtitles-----")
start_time = time.time()
learning_result = subtitle_alignment_service.process_video_for_learning("jTHo90l4EMI")
# print(learning_result)

for entry in learning_result["learning_entries"]:
    print(f"Thai: {entry['thai_text']}")
    print(f"English: {entry['english_text']}")

    for word_dict in entry["word_breakdown"]:
        # These are now properly typed TokenizedThaiWord objects converted to dict
        print(
            f"  {word_dict['thai']} ({word_dict['transliterated']}) -> {word_dict['english_translations']}")


end_time = time.time()
print(end_time-start_time)

