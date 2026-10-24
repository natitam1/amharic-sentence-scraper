import unittest

from clean_training_sentences import (
    clean_sentence,
    ethiopic_numeral_to_int,
    integer_to_amharic,
    number_to_amharic,
    ordinal_to_amharic,
)


class TrainingCleanupTests(unittest.TestCase):
    def test_integer_words(self):
        self.assertEqual(integer_to_amharic(1), "አንድ")
        self.assertEqual(integer_to_amharic(10), "አስር")
        self.assertEqual(integer_to_amharic(21), "ሃያ አንድ")
        self.assertEqual(integer_to_amharic(110), "አንድ መቶ አስር")
        self.assertEqual(integer_to_amharic(2018), "ሁለት ሺህ አስራ ስምንት")
        self.assertEqual(integer_to_amharic(300_000), "ሦስት መቶ ሺህ")

    def test_decimal_and_ordinal_words(self):
        self.assertEqual(number_to_amharic("11.5"), "አስራ አንድ ነጥብ አምስት")
        self.assertEqual(ordinal_to_amharic(13), "አስራ ሦስተኛ")

    def test_ethiopic_numerals(self):
        self.assertEqual(ethiopic_numeral_to_int("፲፩"), 11)
        self.assertEqual(ethiopic_numeral_to_int("፲፰፻፹፰"), 1888)

    def test_spoken_cleanup(self):
        cleaned = clean_sentence(
            "ከ12-14 ዕድሜ ላሉ ልጆች 11.5% የሚሆነውን "
            "ውጤት (ለምሳሌ 3/2) አብራራ።"
        )
        self.assertNotRegex(cleaned, r"\d|[-/()%]")
        self.assertIn("አስራ ሁለት እስከ አስራ አራት", cleaned)
        self.assertIn("አስራ አንድ ነጥብ አምስት በመቶ", cleaned)
        self.assertTrue(cleaned.endswith("።"))

    def test_arithmetic_and_compound_cleanup(self):
        cleaned = clean_sentence(
            "ሂሳቡ $2000 - 1998 = 2$ ሲሆን ባዮ-ኮምፒውተር ይጠቀማል።"
        )
        self.assertIn("ሁለት ሺህ ሲቀነስ", cleaned)
        self.assertIn("እኩል ሁለት", cleaned)
        self.assertIn("ባዮ ኮምፒውተር", cleaned)
        self.assertNotIn("ባዮ ማለትም", cleaned)
        self.assertNotIn("፣።", cleaned)

    def test_dates_and_abbreviations(self):
        cleaned = clean_sentence(
            "ጥቅምት/2018 ዓ.ም እና ሰኔ 18/2018 ዓ/ም "
            "በፍ/ስ/ስ/ህ/ቁ 256 ተጠቅሰዋል።"
        )
        self.assertNotIn("ወይም ሁለት ሺህ", cleaned)
        self.assertIn("ሰኔ አስራ ስምንት ቀን", cleaned)
        self.assertIn("በፍትሐ ብሔር ሥነ ሥርዓት ሕግ ቁጥር", cleaned)
        self.assertNotIn("የየፍትሐ", cleaned)


if __name__ == "__main__":
    unittest.main()
