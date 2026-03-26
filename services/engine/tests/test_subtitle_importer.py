import unittest
from pathlib import Path

from subtitle_rescue_engine.contracts import SubtitleFormat
from subtitle_rescue_engine.subtitles import SubtitleParseError, import_subtitle_file

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "subtitles"


class SubtitleImporterTestCase(unittest.TestCase):
    def test_import_srt_preserves_order_and_timing(self) -> None:
        result = import_subtitle_file(FIXTURES_DIR / "simple.srt")

        self.assertEqual(result.format, SubtitleFormat.SRT)
        self.assertEqual(result.segments[0].id, 1)
        self.assertEqual(result.segments[0].start_ms, 1_000)
        self.assertEqual(result.segments[0].end_ms, 3_200)
        self.assertEqual(result.segments[0].source_text, "你好！\n欢迎来到 这部电影。")
        self.assertEqual(result.segments[2].normalized_source_text, "字幕结束。")

    def test_import_ass_strips_style_markup_and_newline_tokens(self) -> None:
        result = import_subtitle_file(FIXTURES_DIR / "simple.ass")

        self.assertEqual(result.format, SubtitleFormat.ASS)
        self.assertEqual(result.segments[0].start_ms, 1_000)
        self.assertEqual(result.segments[0].source_text, "你好\n欢迎来到这部电影")
        self.assertEqual(result.segments[1].normalized_source_text, "这是第二行")

    def test_invalid_srt_raises_parse_error(self) -> None:
        with self.assertRaises(SubtitleParseError):
            import_subtitle_file(FIXTURES_DIR / "malformed.srt")


if __name__ == "__main__":
    unittest.main()
