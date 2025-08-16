
from pythainlp.tokenize import word_tokenize
from pythainlp.transliterate import romanize
from pythainlp.transliterate import transliterate

from utils.dict_util import load_dictionary, index_by_thai, \
    search_headwords_only

entries = load_dictionary("data/thai-eng-telex.csv")
index = index_by_thai(entries)
word_to_search = "ติดตาม"
result = search_headwords_only(entries, word_to_search)
# print(result)
# print(result.get_english_translations())


sample = "คิดถึงวิวมิ้ม"
text1 = romanize(sample)
print(text1)
text2 = transliterate(sample, engine="icu")
print(text2)



print("\nTokenize breakdown: --------")
lis = word_tokenize(sample)

print(lis)
for word in lis:
    # entry = index.get(word, [None])[0]
    # eng = entry.e_entry if (entry and entry.e_entry) else "(no English gloss)"

    res = search_headwords_only(entries, word)
    print(word, transliterate(word, engine="icu"),
          res.get_english_translations())


print("\nNormalization aka keep_whitespace=False:")
print(word_tokenize(sample, keep_whitespace=False))
