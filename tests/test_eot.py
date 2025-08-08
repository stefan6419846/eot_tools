from io import BytesIO
from unittest import TestCase

from fontTools.ttLib import TTFont  # type: ignore[import-untyped]

from eot_tools.eot import EOTFile
from tests import get_file


class EOTFileTestCase(TestCase):
    def test_loading(self) -> None:
        with get_file("Maki.eot") as path:
            self.assertIsNotNone(EOTFile(path))
            self.assertIsNotNone(EOTFile(str(path)))
            self.assertIsNotNone(EOTFile(path.read_bytes()))

    def test_maki_eot(self) -> None:
        with get_file("Maki.eot") as path:
            eot = EOTFile(path)

        self.assertEqual(44636, eot.eot_size)
        self.assertEqual(131073, eot.version)
        self.assertEqual(0, eot.flags)
        self.assertEqual(b"\x02\x00\x05\t\x00\x00\x00\x00\x00\x00", eot.font_panose)
        self.assertEqual(1, eot.charset)
        self.assertEqual(0, eot.italic)
        self.assertEqual(400, eot.weight)
        self.assertEqual(0, eot.fs_type)
        self.assertEqual(3, eot.unicode_range1)
        self.assertEqual(0, eot.unicode_range2)
        self.assertEqual(0, eot.unicode_range3)
        self.assertEqual(0, eot.unicode_range4)
        self.assertEqual(1, eot.code_page_range1)
        self.assertEqual(0, eot.code_page_range2)
        self.assertEqual(3236315134, eot.check_sum_adjustment)
        self.assertEqual("Maki", eot.family_name)
        self.assertEqual("Regular", eot.style_name)
        self.assertEqual("Version 001.000", eot.version_name)
        self.assertEqual("Maki", eot.full_name)
        self.assertEqual([""], eot.root_string)
        self.assertEqual(-1, eot.root_string_checksum)
        self.assertEqual(-1, eot.eudc_code_page)
        self.assertEqual("", eot.signature)
        self.assertEqual(0, eot.eudc_flags)
        self.assertEqual(b"", eot.eudc_font_data)

        with get_file("Maki.ttf") as path:
            self.assertEqual(path.read_bytes(), eot.font_data)
        with TTFont(file=BytesIO(eot.font_data)):
            pass
