from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path


UNITS = {
    0: "ዜሮ",
    1: "አንድ",
    2: "ሁለት",
    3: "ሦስት",
    4: "አራት",
    5: "አምስት",
    6: "ስድስት",
    7: "ሰባት",
    8: "ስምንት",
    9: "ዘጠኝ",
}
TENS = {
    10: "አስር",
    20: "ሃያ",
    30: "ሠላሳ",
    40: "አርባ",
    50: "ሃምሳ",
    60: "ስድሳ",
    70: "ሰባ",
    80: "ሰማንያ",
    90: "ዘጠና",
}
SCALES = (
    (1_000_000_000_000_000, "ኳድሪሊዮን"),
    (1_000_000_000_000, "ትሪሊዮን"),
    (1_000_000_000, "ቢሊዮን"),
    (1_000_000, "ሚሊዮን"),
    (1_000, "ሺህ"),
)
ORDINAL_ENDINGS = {
    "አንድ": "አንደኛ",
    "ሁለት": "ሁለተኛ",
    "ሦስት": "ሦስተኛ",
    "አራት": "አራተኛ",
    "አምስት": "አምስተኛ",
    "ስድስት": "ስድስተኛ",
    "ሰባት": "ሰባተኛ",
    "ስምንት": "ስምንተኛ",
    "ዘጠኝ": "ዘጠነኛ",
    "አስር": "አስረኛ",
}
ETHIOPIC_VALUES = {
    "፩": 1,
    "፪": 2,
    "፫": 3,
    "፬": 4,
    "፭": 5,
    "፮": 6,
    "፯": 7,
    "፰": 8,
    "፱": 9,
    "፲": 10,
    "፳": 20,
    "፴": 30,
    "፵": 40,
    "፶": 50,
    "፷": 60,
    "፸": 70,
    "፹": 80,
    "፺": 90,
}
NUMBER_TOKEN = r"\d[\d,]*(?:\.\d+)?"
MONTH_NAMES = (
    "መስከረም|ጥቅምት|ኅዳር|ህዳር|ታኅሣሥ|ታህሳስ|ጥር|የካቲት|"
    "መጋቢት|ሚያዝያ|ግንቦት|ሰኔ|ሐምሌ|ሀምሌ|ነሐሴ|ነሀሴ|ጳጉሜ|"
    "ጃንዋሪ|ፌብርዋሪ|ማርች|ኤፕሪል|ሜይ|ጁን|ጁላይ|ኦገስት|"
    "ሴፕቴምበር|ኦክቶበር|ኖቬምበር|ዲሴምበር"
)
NUMBER_WORD_STARTS = (
    "ዜሮ|አንድ|ሁለት|ሦስት|አራት|አምስት|ስድስት|ሰባት|"
    "ስምንት|ዘጠኝ|አስር|አስራ|ሃያ|ሠላሳ|አርባ|ሃምሳ|"
    "ስድሳ|ሰባ|ሰማንያ|ዘጠና"
)


def integer_to_amharic(number: int) -> str:
    if number < 0:
        return f"ሲቀነስ {integer_to_amharic(abs(number))}"
    if number < 10:
        return UNITS[number]
    if number == 10:
        return TENS[number]
    if number < 20:
        return "አስራ " + UNITS[number - 10]
    if number < 100:
        tens, remainder = divmod(number, 10)
        words = TENS[tens * 10]
        return words if remainder == 0 else f"{words} {UNITS[remainder]}"
    if number < 1_000:
        hundreds, remainder = divmod(number, 100)
        words = f"{integer_to_amharic(hundreds)} መቶ"
        return words if remainder == 0 else f"{words} {integer_to_amharic(remainder)}"
    for value, name in SCALES:
        if number >= value:
            quotient, remainder = divmod(number, value)
            words = f"{integer_to_amharic(quotient)} {name}"
            return words if remainder == 0 else f"{words} {integer_to_amharic(remainder)}"
    raise ValueError(f"Unsupported number: {number}")


def number_to_amharic(value: str) -> str:
    normalized = value.replace(",", "")
    if "." not in normalized:
        return integer_to_amharic(int(normalized))
    integer, fraction = normalized.split(".", 1)
    if not fraction or set(fraction) == {"0"}:
        return integer_to_amharic(int(integer))
    fraction_words = " ".join(UNITS[int(digit)] for digit in fraction)
    return f"{integer_to_amharic(int(integer))} ነጥብ {fraction_words}"


def ordinal_to_amharic(number: int) -> str:
    words = integer_to_amharic(number).split()
    words[-1] = ORDINAL_ENDINGS.get(words[-1], words[-1] + "ኛ")
    return " ".join(words)


def ethiopic_numeral_to_int(value: str) -> int:
    if "፼" in value:
        left, right = value.split("፼", 1)
        multiplier = ethiopic_numeral_to_int(left) if left else 1
        return multiplier * 10_000 + (ethiopic_numeral_to_int(right) if right else 0)
    if "፻" in value:
        left, right = value.split("፻", 1)
        multiplier = ethiopic_numeral_to_int(left) if left else 1
        return multiplier * 100 + (ethiopic_numeral_to_int(right) if right else 0)
    return sum(ETHIOPIC_VALUES[char] for char in value)


def _replace_parentheses(text: str) -> str:
    pattern = re.compile(r"\(([^()]*)\)")
    while pattern.search(text):
        text = pattern.sub(
            lambda match: (
                f"፣ {match.group(1).strip()}፣"
                if match.group(1).strip().startswith(("ለምሳሌ", "ነገር ግን"))
                else f"፣ ማለትም {match.group(1).strip()}፣"
            ),
            text,
        )
    return text


def _spoken_numbers(text: str) -> str:
    text = re.sub(
        r"([^\s፣።]+)\s*\(\s*\d+\s*\)",
        r"\1",
        text,
    )
    text = re.sub(
        r"([፩-፼]+)ኛ",
        lambda match: ordinal_to_amharic(ethiopic_numeral_to_int(match.group(1))),
        text,
    )
    text = re.sub(
        r"([፩-፼]+)",
        lambda match: integer_to_amharic(ethiopic_numeral_to_int(match.group(1))),
        text,
    )
    text = re.sub(
        rf"({NUMBER_TOKEN})ኛ",
        lambda match: ordinal_to_amharic(int(match.group(1).replace(",", ""))),
        text,
    )
    text = re.sub(
        r"(\d{1,2}):00",
        lambda match: f"{integer_to_amharic(int(match.group(1)))} ሰዓት",
        text,
    )
    text = re.sub(
        rf"({NUMBER_TOKEN})\s*-\s*({NUMBER_TOKEN})\s*=\s*({NUMBER_TOKEN})",
        lambda match: (
            f"{number_to_amharic(match.group(1))} ሲቀነስ "
            f"{number_to_amharic(match.group(2))} እኩል "
            f"{number_to_amharic(match.group(3))}"
        ),
        text,
    )
    text = re.sub(
        rf"({NUMBER_TOKEN})\s*[-–—_]\s*({NUMBER_TOKEN})",
        lambda match: (
            f"{number_to_amharic(match.group(1))} እስከ "
            f"{number_to_amharic(match.group(2))}"
        ),
        text,
    )
    text = re.sub(
        rf"({NUMBER_TOKEN})\s*/\s*({NUMBER_TOKEN})",
        lambda match: (
            f"{number_to_amharic(match.group(1))} በ "
            f"{number_to_amharic(match.group(2))}"
        ),
        text,
    )
    text = re.sub(
        rf"({NUMBER_TOKEN})\s*\+\s*({NUMBER_TOKEN})",
        lambda match: (
            f"{number_to_amharic(match.group(1))} ሲደመር "
            f"{number_to_amharic(match.group(2))}"
        ),
        text,
    )
    text = re.sub(
        rf"({NUMBER_TOKEN})\s*=\s*({NUMBER_TOKEN})",
        lambda match: (
            f"{number_to_amharic(match.group(1))} እኩል "
            f"{number_to_amharic(match.group(2))}"
        ),
        text,
    )
    text = re.sub(
        rf"({NUMBER_TOKEN})%",
        lambda match: f"{number_to_amharic(match.group(1))} በመቶ",
        text,
    )
    text = re.sub(
        NUMBER_TOKEN,
        lambda match: f" {number_to_amharic(match.group(0))} ",
        text,
    )
    return text


def clean_sentence(sentence: str) -> str:
    text = unicodedata.normalize("NFC", sentence).strip()
    text = text.replace(
        "ሰላም ጤና ይስጥልን ውድ የዶክተር አለ ቤተሰቦች ለዛሬ "
        "ስለ ያልታወቀ የጤና እክል እንዳለቦት በማስብ መጨነቅ/# "
        "የምለው እርስ እናወራለን እንሆ፡፡",
        "ዛሬ ስለ ያልታወቀ የጤና እክል እንዳለ በማሰብ "
        "ስለሚፈጠር ጭንቀት እናወራለን።",
    )
    text = re.sub(
        r"በማይንድ ሞርኒንግ ቢሮ መገናኛ ስለሺ ህንፃ "
        r"\d+ኛ ወለል በ\d+ መደወል ይችላሉ።$",
        "መሆኑ ተገልጿል።",
        text,
    )
    replacements = {
        "እ.ኤ.አ": "እንደ አውሮፓውያን አቆጣጠር",
        "ዓ.ም.": "ዓመተ ምህረት",
        "ዓ/ም": "ዓመተ ምህረት",
        "ዓ.ም": "ዓመተ ምህረት",
        "ኣ.ም": "ዓመተ ምህረት",
        "ዓም": "ዓመተ ምህረት",
        "ዶ/ር": "ዶክተር",
        "ዶ /ር": "ዶክተር",
        "ወ/ሮ": "ወይዘሮ",
        "ፍ/ቤት": "ፍርድ ቤት",
        "ፍ/ስ/ስ/ህ/ቁ.": "ፍትሐ ብሔር ሥነ ሥርዓት ሕግ ቁጥር ",
        "ፍ/ሥ/ሥ/ሕ/ቁ.": "ፍትሐ ብሔር ሥነ ሥርዓት ሕግ ቁጥር ",
        "ፍ/ስ/ስ/ህ/ቁ": "ፍትሐ ብሔር ሥነ ሥርዓት ሕግ ቁጥር",
        "ፍ/ሥ/ሥ/ሕ/ቁ": "ፍትሐ ብሔር ሥነ ሥርዓት ሕግ ቁጥር",
        "ፍ/ብ/ሕ/ሥ/ሥ/": "ፍትሐ ብሔር ሕግ ሥነ ሥርዓት ",
        "ወ/መ/ሥ/ህ/ቁ": "የወንጀል መቅጫ ሥነ ሥርዓት ሕግ ቁጥር",
        "ሰ/መ/ቁጥር": "ሰበር መዝገብ ቁጥር",
        "ሰ/መ/ቁ.": "ሰበር መዝገብ ቁጥር ",
        "መ/መ/ቁ.": "መዝገብ ቁጥር ",
        "መ/ቁ": "መዝገብ ቁጥር",
        "ም/ቤት": "ምክር ቤት",
        "መ/ሰጭ": "መልስ ሰጪ",
        "አ.ማ.": "አክሲዮን ማህበር",
        "አ.ማ": "አክሲዮን ማህበር",
        "ሴ.ሜ": "ሴንቲ ሜትር",
        "ኪ.ሜ": "ኪሎ ሜትር",
        "ኤች. አይ..ቪ": "ኤች አይ ቪ",
        "ለብሶ/ሳ": "ለብሶ ወይም ለብሳ",
        "ምድብ ለ፦": "በምድብ ለ፣",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(
        rf"((?:{MONTH_NAMES})\s+\d{{1,2}})\s*/\s*(\d{{4}})",
        r"\1 ቀን \2",
        text,
    )
    text = re.sub(
        rf"((?:{MONTH_NAMES}))\s*/\s*(\d{{4}})",
        r"\1 \2",
        text,
    )
    text = re.sub(r"/\s*([\u1200-\u137f\s]+?)\s*/", r"፣ \1፣ ", text)
    text = _spoken_numbers(text)
    text = _replace_parentheses(text)
    text = re.sub(r"\bምሳ[ሌሴ]፦", "ለምሳሌ፣", text)
    text = text.replace("በቀላሉ ሲገለጽ፦", "በቀላሉ ሲገለጽ፣")
    text = text.replace("ጠቃሚ ምክር፦", "")
    text = re.sub(r"([^\s፣።]+)(?:፡-|፦)\s*", r"\1 ማለትም ", text)
    text = re.sub(r"\s*/\s*", " ወይም ", text)
    text = re.sub(r"[-–—_]", " ", text)
    text = text.replace("፡፡", "።").replace("፤", "፣").replace(";", "፣")
    text = text.replace("?", "።").replace("!", "።")
    text = re.sub(r"\.{2,}", "፣", text)
    text = text.replace(".", "።").replace(":", "፣")
    text = text.replace("፦", "፣")

    cleaned_chars: list[str] = []
    for char in text:
        if char in {"።", "፣"} or char.isspace():
            cleaned_chars.append(char)
            continue
        category = unicodedata.category(char)
        cleaned_chars.append(" " if category[0] in {"P", "S", "N"} else char)
    text = "".join(cleaned_chars)
    text = re.sub(r"\s*፣\s*", "፣ ", text)
    text = re.sub(r"\s*።\s*", "። ", text)
    text = re.sub(r"፣\s*።", "።", text)
    text = re.sub(r"(?:፣\s*){2,}", "፣ ", text)
    text = re.sub(r"(?:።\s*){2,}", "። ", text)
    text = re.sub(r"\s+", " ", text).strip(" ፣")
    text = re.sub(
        rf"(?<!\S)([በከለየ])\s+(?=(?:{NUMBER_WORD_STARTS})\b)",
        r"\1",
        text,
    )
    if not text.endswith("።"):
        text += "።"
    return text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--group-size", type=int, default=10)
    parser.add_argument("--fill-from", nargs="*", type=Path, default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_lines = [
        line
        for line in args.input.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    target_count = len(source_lines)
    sentences: list[str] = []
    seen: set[str] = set()
    for line in source_lines:
        sentence = clean_sentence(line)
        if sentence not in seen:
            seen.add(sentence)
            sentences.append(sentence)
    for path in args.fill_from:
        if len(sentences) >= target_count or not path.exists():
            break
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            sentence = clean_sentence(line)
            if sentence in seen:
                continue
            seen.add(sentence)
            sentences.append(sentence)
            if len(sentences) >= target_count:
                break
    output_lines: list[str] = []
    for index, sentence in enumerate(sentences, start=1):
        output_lines.append(sentence)
        if index % args.group_size == 0 and index != len(sentences):
            output_lines.append("")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
    print(
        f"Wrote {len(sentences)} sentences in "
        f"{(len(sentences) + args.group_size - 1) // args.group_size} groups "
        f"to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
