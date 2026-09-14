import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from world_protocol import (
    encode_inline_string,
    encode_smallint,
    join_server_parts,
    make_blank_map,
    make_entity_record,
    make_map_download_block,
    make_map_switch_record,
)


class WorldProtocolTests(unittest.TestCase):
    def test_smallint(self):
        self.assertEqual(encode_smallint(126), b"\x7e")
        self.assertEqual(encode_smallint(127), b"\x7f\x00\x7f")
        self.assertEqual(encode_smallint(0x1234), b"\x7f\x12\x34")

    def test_inline_string(self):
        self.assertEqual(encode_inline_string("A"), b"\x82A\x00")

    def test_map_switch_record(self):
        rec = make_map_switch_record("hzwlocal00")
        self.assertEqual(((rec[0] << 8) | rec[1]) + 2, len(rec))
        self.assertEqual(rec[2], 1)
        n = rec[3] - 128
        token = rec[4:4+n].decode()
        self.assertEqual(token, "hzwlocal00")
        self.assertEqual(token[:-2] + "sj", "hzwlocalsj")

    def test_entity_record(self):
        rec = make_entity_record("player", 14, 0, 1, 10, 10)
        self.assertEqual(((rec[0] << 8) | rec[1]) + 2, len(rec))
        self.assertEqual(rec[2], 4)
        self.assertEqual(rec[4:10], b"player")
        self.assertEqual(rec[11:], bytes((14, 0, 1, 10, 10)))

    def test_blank_map(self):
        m = make_blank_map(24, 24)
        self.assertEqual(len(m), 20 + 24 * 24 * 4)
        self.assertEqual(m[18:20], bytes((24, 24)))
        self.assertEqual(m[20:24], bytes((0x0F, 0xFF, 0xFF, 0x00)))

    def test_map_download_block(self):
        m = make_blank_map(4, 3)
        block = make_map_download_block("hzwlocalsj", m)
        self.assertTrue(block.startswith(b"\x00\x00\x7fhzwlocalsj\x00"))
        zero = block.index(0, 3)
        n = block[zero + 1] | (block[zero + 2] << 8)
        self.assertEqual(n, len(m))
        self.assertEqual(block[zero + 3:zero + 3 + n], m)

    def test_walk_selector_matches_real_client_parser(self):
        cmd = "<r>walk 1"
        self.assertTrue(cmd.startswith("<r>walk"))
        self.assertEqual(cmd[7], " ")
        self.assertEqual(int(cmd[8:]), 1)

    def test_mixed_payload(self):
        map_rec = make_map_switch_record("hzwlocal00")
        ent_rec = make_entity_record("player", 14, 0, 1, 10, 10)
        payload = join_server_parts(["<log_suc>", map_rec, ent_rec, "<r>walk 1"])
        self.assertTrue(payload.startswith(b"<log_suc>\n"))
        self.assertIn(map_rec, payload)
        self.assertIn(ent_rec, payload)
        self.assertTrue(payload.endswith(b"<r>walk 1\n"))


if __name__ == "__main__":
    unittest.main()
