import unittest

from payload_stream import (
    AmbiguousRecord,
    MapDownloadRecord,
    NormalRecord,
    TextLine,
    TruncatedRecord,
    UnknownSpecialRecord,
    parse_payload_stream,
    write_payload_analysis,
)
from world_protocol import make_map_download_block, make_map_switch_record


class PayloadStreamTests(unittest.TestCase):
    def test_parses_mixed_text_normal_and_marker_127_records(self):
        map_bytes = b"\x01\x02\x03\x04"
        raw = (
            b"<log_suc>\n"
            + make_map_switch_record("hzwlocal00")
            + make_map_download_block("hzwlocalsj", map_bytes)
        )

        records = parse_payload_stream(raw)

        self.assertEqual(len(records), 3)
        self.assertEqual(records[0], TextLine(0, b"<log_suc>\n", "<log_suc>"))
        self.assertIsInstance(records[1], NormalRecord)
        self.assertEqual(records[1].record_type, 1)
        self.assertEqual(records[1].raw, make_map_switch_record("hzwlocal00"))
        self.assertEqual(
            records[2],
            MapDownloadRecord(
                records[1].offset + len(records[1].raw),
                "hzwlocalsj",
                map_bytes,
                make_map_download_block("hzwlocalsj", map_bytes),
            ),
        )

    def test_preserves_unknown_special_markers_without_guessing_framing(self):
        for marker in (124, 125, 126):
            with self.subTest(marker=marker):
                raw = bytes((0, 0, marker, 0xAA, 0xBB, 0xCC))
                records = parse_payload_stream(raw)
                self.assertEqual(
                    records,
                    [UnknownSpecialRecord(0, marker, raw)],
                )

    def test_stops_after_unknown_special_marker_to_avoid_false_alignment(self):
        first = make_map_switch_record("hzwlocal00")
        unknown = b"\x00\x00\x7d\x05\x06\x07\x08"

        records = parse_payload_stream(first + unknown)

        self.assertEqual(len(records), 2)
        self.assertIsInstance(records[0], NormalRecord)
        self.assertEqual(records[1], UnknownSpecialRecord(len(first), 125, unknown))

    def test_reports_truncated_marker_127_block(self):
        raw = b"\x00\x00\x7fmap-key\x00\x04\x00\x01\x02"

        records = parse_payload_stream(raw)

        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], TruncatedRecord)
        self.assertIn("map payload", records[0].reason)
        self.assertEqual(records[0].raw, raw)

    def test_reports_truncated_normal_record(self):
        raw = b"\x00\x05\x01\x82A"

        records = parse_payload_stream(raw)

        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], TruncatedRecord)
        self.assertIn("normal record", records[0].reason)

    def test_large_normal_record_whose_length_starts_with_angle_bracket(self):
        payload = b"A" * 0x3C00
        raw = b"\x3c\x01\x01" + payload

        records = parse_payload_stream(raw)

        self.assertEqual(records, [NormalRecord(0, 1, payload, raw)])

    def test_angle_bracket_prefix_with_both_valid_framings_is_opaque(self):
        payload = b"A\n" + b"B" * (0x3C00 - 2)
        raw = b"\x3c\x01\x01" + payload

        records = parse_payload_stream(raw)

        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], AmbiguousRecord)
        self.assertEqual(records[0].raw, raw)

    def test_payload_report_refuses_to_overwrite_input(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temp:
            payload = Path(temp) / "capture.bin"
            payload.write_bytes(b"<log_suc>\n")
            with self.assertRaisesRegex(ValueError, "same file"):
                write_payload_analysis(payload, payload)


if __name__ == "__main__":
    unittest.main()
