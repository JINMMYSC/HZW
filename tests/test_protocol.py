import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hzw_protocol import (
    SessionState, chain_encode, chain_decode, cid_sum,
    encode_socket_server_payload, encode_socket_client_frame_for_test,
    decode_socket_client_frame, encode_http_server_payload, decode_http_client_body,
)


class ProtocolTests(unittest.TestCase):
    def test_chain_roundtrip(self):
        p = b"new\nhello\n"
        c = chain_encode(p, 0x42)
        self.assertEqual(chain_decode(c, 0x42), p)

    def test_cid_sum(self):
        self.assertEqual(cid_sum("ABC"), 65 + 66 + 67)

    def test_socket_server_frame_shape(self):
        s = SessionState(cid="HZ123")
        frame = encode_socket_server_payload(b"<smg>ok\n", s, ack4=b"ABCD")
        self.assertEqual(frame[:4], b"ABCD")
        raw = frame[4] | (frame[5] << 8)
        self.assertEqual(raw ^ 0xA5A5, len(b"<smg>ok\n"))
        self.assertEqual(chain_decode(frame[6:], frame[4]), b"<smg>ok\n")

    def test_socket_client_roundtrip(self):
        enc_state = SessionState()
        dec_state = SessionState()
        ack = b"\x01\x02\x03\x04"
        p = b"new\n860.1HZ0000.NON5800.CT\n"
        frame = encode_socket_client_frame_for_test(p, enc_state, ack)
        got = decode_socket_client_frame(frame[:6], frame[6:], dec_state)
        self.assertEqual(got, p)

    def test_http_client_roundtrip_shape(self):
        s = SessionState(cid="ABC", sn=7)
        p = b"walk 1\n"
        h = len(p) ^ (cid_sum("ABC") + 7)
        h0, h1 = h & 0xff, (h >> 8) & 0xff
        body = bytes((h0, h1)) + chain_encode(p, h0)
        self.assertEqual(decode_http_client_body(body, s), p)

    def test_http_server_frame(self):
        s = SessionState(cid="ABC")
        frame = encode_http_server_payload(b"<smg>ok\n", s)
        raw = frame[0] | (frame[1] << 8)
        self.assertEqual(raw ^ cid_sum("ABC"), len(b"<smg>ok\n"))
        self.assertEqual(chain_decode(frame[2:], frame[0]), b"<smg>ok\n")


if __name__ == "__main__":
    unittest.main()
