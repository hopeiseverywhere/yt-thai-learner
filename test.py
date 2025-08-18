# -*- coding: utf-8 -*-
# Naive Thai transliteration (improved):
# - handles silent thanthakhat: drop consonant+์ (e.g., การณ์ -> การ)
# - heuristic for สถาน... -> สะ + ถาน ...
# - keeps simple tone accents; add OVERRIDES for custom styles

import re

TONE_MARKS = {"่": "L", "้": "F", "๊": "H", "๋": "R"}
THANTHAKHAT = "์"

# per-word overrides (use this to exactly match your house style)
OVERRIDES = {
    # example to match your target exactly:
    # "สถานการณ์": "sà-tăa-ná-gaan"
}

CONS = set("กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬฮอ")
PRE_VOWELS = set("เแโไใ")
POST_VOWELS = set("ะาิีึืุูำๅ")
HIGH = set("ขฃฉฐถผฝศษสห")
MID  = set("กจฎฏดตบปอ")

init_map = {
    "ก":"g","ข":"kh","ฃ":"kh","ค":"k","ฅ":"k","ฆ":"kh",
    "ง":"ng","จ":"j","ฉ":"ch","ช":"ch","ซ":"s","ฌ":"ch",
    "ญ":"y","ฎ":"d","ฏ":"t","ฐ":"th","ฑ":"th","ฒ":"th","ถ":"th",
    "ท":"th","ธ":"th","ด":"d","ต":"dt",
    "ณ":"n","น":"n","บ":"b","ป":"bp",
    "ผ":"ph","พ":"ph","ภ":"ph","ฝ":"f","ฟ":"f",
    "ม":"m","ย":"y","ร":"r","ล":"l","ว":"w",
    "ศ":"s","ษ":"s","ส":"s","ห":"h","ฬ":"l","ฮ":"h","อ":""
}

coda_map = {
    **{c:"k" for c in "กขฃคฅฆ"},
    **{c:"t" for c in "ดฎตฏจชซศษส"},
    **{c:"p" for c in "บบปพฟภผฝ"},
    "ง":"ng", "น":"n", "ณ":"n", "ญ":"n", "ร":"n", "ล":"n", "ฬ":"n",
    "ม":"m", "ย":"y", "ว":"w", "อ":"", "ห":""
}

tone_to_accent = {"M": None, "L":"grave", "H":"acute", "R":"caron", "F":"circumflex"}
accent_map = {
    ("a","grave"):"à",("a","acute"):"á",("a","caron"):"ǎ",("a","circumflex"):"â",
    ("e","grave"):"è",("e","acute"):"é",("e","caron"):"ě",("e","circumflex"):"ê",
    ("i","grave"):"ì",("i","acute"):"í",("i","caron"):"ǐ",("i","circumflex"):"î",
    ("o","grave"):"ò",("o","acute"):"ó",("o","caron"):"ǒ",("o","circumflex"):"ô",
    ("u","grave"):"ù",("u","acute"):"ú",("u","caron"):"ǔ",("u","circumflex"):"û",
}

def cons_class(ch):
    if ch in HIGH: return "H"
    if ch in MID:  return "M"
    return "L"

def apply_tone(vowel_str, tone_code):
    acc = tone_to_accent.get(tone_code)
    if not acc: return vowel_str
    for i, ch in enumerate(vowel_str):
        base = ch.lower()
        if base in "aeiou":
            rep = accent_map.get((base, acc))
            if rep:
                return vowel_str[:i] + rep + vowel_str[i+1:]
    return vowel_str

def resolve_vowel(pre, marks):
    m = [c for c in marks if c in POST_VOWELS]
    if pre == "เ":
        if "า" in m: return "ao"   # เ◌า
        if "ะ" in m: return "e"    # เ◌ะ
        if "ิ" in m: return "er"   # เ◌ิ
        if "ี" in m: return "ee"   # เ◌ี
        return "er"                # เ◌อ
    if pre == "แ": return "ae"
    if pre == "โ": return "o"
    if pre in ("ไ","ใ"): return "ai"
    if "ำ" in m: return "am"
    if "ะ" in m: return "a"
    if "า" in m or "ๅ" in m: return "aa"
    if "ิ" in m: return "i"
    if "ี" in m: return "ii"
    if "ึ" in m: return "ue"
    if "ื" in m: return "uee"
    if "ุ" in m: return "u"
    if "ู" in m: return "uu"
    return "o"  # implicit

def calc_tone(lead, marks, tone_mark, coda):
    if tone_mark:
        return TONE_MARKS[tone_mark]
    cls = cons_class(lead[0]) if lead else "M"
    short_v = {"ะ","ิ","ึ","ุ"}
    is_short = any(ch in short_v for ch in marks)
    live = (coda_map.get(coda, "") in ("m","n","ng","y","w")) or (coda == "" and not is_short)
    if cls == "M":
        return "M" if live else ("L" if is_short else "F")
    if cls == "H":
        return "R" if live else "L"
    return "M" if live else ("H" if is_short else "F")

def preprocess(text: str) -> str:
    # 1) drop consonant + thanthakhat (e.g., ณ์ -> (drop ณ) + drop mark)
    text = re.sub(r"([\u0E00-\u0E7F])"+THANTHAKHAT, "", text)

    # 2) heuristic: สถาน… → สะ + ถาน…  (insert ะ after ส if followed by ถา)
    text = re.sub(r"ส(?=ถาน)", "สะ", text)

    # 3) common morpheme: การณ์ → การ
    text = text.replace("การณ์", "การ")
    return text

def split_syllables(s):
    out, i = [], 0
    while i < len(s):
        # non-Thai char passthrough
        if not (s[i] in CONS or s[i] in PRE_VOWELS):
            out.append(s[i]); i += 1; continue

        pre = s[i] if s[i] in PRE_VOWELS else ""
        if pre: i += 1

        lead = ""
        if i < len(s) and s[i] in CONS:
            lead += s[i]; i += 1
            # optional r/l/w cluster
            if i < len(s) and s[i] in "รลว" and (i+1 < len(s) and (s[i+1] in POST_VOWELS or s[i+1] in "่้๊๋็")):
                lead += s[i]; i += 1

        tone_mark = ""
        marks = ""
        while i < len(s) and (s[i] in POST_VOWELS or s[i] in "่้๊๋็์"):
            if s[i] in TONE_MARKS: tone_mark = s[i]
            marks += s[i]; i += 1

        coda = ""
        if i < len(s) and s[i] in CONS and not (i+1 < len(s) and s[i+1] in PRE_VOWELS):
            coda = s[i]; i += 1

        out.append({"pre": pre, "lead": lead, "marks": marks, "tone": tone_mark, "coda": coda})
    return out

def transliterate_thai(text: str) -> str:
    if text in OVERRIDES:
        return OVERRIDES[text]
    text = preprocess(text)
    syls = split_syllables(text)

    romans = []
    for syl in syls:
        if not isinstance(syl, dict):
            romans.append(syl if syl.strip() else " ")
            continue
        pre, lead, marks, tone_mark, coda = syl["pre"], syl["lead"], syl["marks"], syl["tone"], syl["coda"]
        init = "".join(init_map.get(ch, "") for ch in lead)
        vowel = resolve_vowel(pre, marks)
        tone = calc_tone(lead, marks, tone_mark, coda)
        vowel = apply_tone(vowel, tone)
        coda_rom = coda_map.get(coda, "")
        romans.append(init + vowel + coda_rom)

    # prefix hyphen for patterns like ประ-เมิน (ะ + next syll starts with เ)
    out = []
    for i in range(len(syls)):
        syl, token = syls[i], romans[i]
        if i > 0 and isinstance(syl, dict) and isinstance(syls[i-1], dict):
            if "ะ" in syls[i-1]["marks"] and syl["pre"] == "เ":
                if out and out[-1].endswith(" "): out[-1] = out[-1][:-1]
                out.append("-" + token); out.append(" "); continue
        out.append(token); out.append(" ")
    return " ".join("".join(out).strip().split())

# --- quick tests ---

# --- quick demo ---
print(transliterate_thai("คิดถึงวิวมิ้มประเมิน"))
# -> kít thǔeng wiw mîm bprà-mern

print(transliterate_thai("สถานการณ์"))
