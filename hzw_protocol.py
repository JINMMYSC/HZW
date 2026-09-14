from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Tuple

SOCKET_RESPONSE_LEN_XOR = 0xA5A5  # 42405, confirmed in V860 O0OO0OO
LCG_A = 214013
LCG_C = 2531011


def cid_sum(cid: str) -> int:
    """V860 computes the session key by summing Java char values of <cid...>."""
    return sum(ord(ch) for ch in cid)


def chain_encode(payload: bytes, key: int) -> bytes:
    """Encode with the V860 forward chained XOR used on wire payloads."""
    if not payload:
        return b""
    out = bytearray(len(payload))
    prev = key & 0xFF
    for i, b in enumerate(payload):
        out[i] = b ^ prev
        prev = out[i]
    return bytes(out)


def chain_decode(payload: bytes, key: int) -> bytes:
    """Decode V860 chained XOR. Equivalent to the client's reverse loop."""
    if not payload:
        return b""
    out = bytearray(payload)
    for i in range(len(out) - 1, 0, -1):
        out[i] ^= out[i - 1]
    out[0] ^= key & 0xFF
    return bytes(out)


def ror16(v: int, n: int) -> int:
    n &= 15
    v &= 0xFFFF
    if n == 0:
        return v
    return ((v >> n) | (v << (16 - n))) & 0xFFFF


def rol16(v: int, n: int) -> int:
    n &= 15
    v &= 0xFFFF
    if n == 0:
        return v
    return ((v << n) | (v >> (16 - n))) & 0xFFFF


@dataclass
class SessionState:
    cid: str = ""
    sn: int = 1  # O0OOOO.OOO0 starts at 1
    lcg_seed: int = 0  # reset to 0 when socket connection is established
    last_ack4: bytes = b"\x00\x00\x00\x00"
    rx_frames: int = 0
    tx_frames: int = 0
    username: str = ""
    logged_in: bool = False
    metadata: dict = field(default_factory=dict)

    @property
    def cid_key(self) -> int:
        return cid_sum(self.cid)

    def advance_server_payload(self) -> None:
        # Client increments OOO0 exactly once after parsing a complete server payload.
        self.sn += 1
        self.tx_frames += 1

    def next_lcg_rot(self, ack0: int) -> int:
        self.lcg_seed = (self.lcg_seed * LCG_A + LCG_C) & 0xFFFFFFFF
        # Java code: ((seed & 0xF0000) >>> 16 + ack[0]) & 15
        return (((self.lcg_seed & 0xF0000) >> 16) + (ack0 & 0xFF)) & 15


def encode_http_server_payload(text_or_bytes: str | bytes, state: SessionState) -> bytes:
    """Server -> V860 HTTP response: LE16(len ^ cid_sum), then chained XOR payload."""
    payload = text_or_bytes.encode("utf-8") if isinstance(text_or_bytes, str) else text_or_bytes
    encoded_len = (len(payload) ^ state.cid_key) & 0xFFFF
    h0 = encoded_len & 0xFF
    h1 = (encoded_len >> 8) & 0xFF
    encoded = chain_encode(payload, h0)
    state.advance_server_payload()
    return bytes((h0, h1)) + encoded


def decode_http_client_body(body: bytes, state: SessionState) -> bytes:
    """V860 HTTP POST body -> plaintext command bytes.

    Client code OO000OO(): header = payload_len ^ (cid_sum + sn), little endian,
    followed by chained-XOR bytes seeded with header byte 0.
    """
    if len(body) < 2:
        raise ValueError("HTTP client body shorter than 2-byte header")
    raw = body[0] | (body[1] << 8)
    expected_len = raw ^ ((state.cid_key + state.sn) & 0xFFFF)
    if expected_len < 0 or expected_len > len(body) - 2:
        raise ValueError(f"HTTP length mismatch: decoded={expected_len}, available={len(body)-2}")
    return chain_decode(body[2:2 + expected_len], body[0])


def encode_socket_server_payload(
    text_or_bytes: str | bytes,
    state: SessionState,
    ack4: bytes | None = None,
) -> bytes:
    """Server -> V860 socket frame.

    Confirmed receive code reads 6 bytes, obtains payload_len = LE16(h[4:6]) ^ 0xA5A5,
    decrypts payload with h[4] as chained-XOR key, and echoes h[0:4] in later client frames.
    """
    payload = text_or_bytes.encode("utf-8") if isinstance(text_or_bytes, str) else text_or_bytes
    if ack4 is None:
        # Deterministic per-frame token. Client does not interpret it, only echoes it.
        seq = (state.tx_frames + 1) & 0xFFFFFFFF
        ack4 = seq.to_bytes(4, "little")
    if len(ack4) != 4:
        raise ValueError("ack4 must be exactly 4 bytes")
    raw_len = (len(payload) ^ SOCKET_RESPONSE_LEN_XOR) & 0xFFFF
    h4 = raw_len & 0xFF
    h5 = (raw_len >> 8) & 0xFF
    state.last_ack4 = ack4
    encoded = chain_encode(payload, h4)
    state.advance_server_payload()
    return ack4 + bytes((h4, h5)) + encoded


def decode_socket_client_frame(header6: bytes, payload: bytes, state: SessionState) -> bytes:
    """Decode one V860 socket client frame after the initial 'kawa' bootstrap.

    Client O0O()/OO00() uses a 16-bit rotated payload length. Rotation comes from the
    Microsoft-style LCG plus the first echoed ACK byte. Payload starts at byte 6 and is
    chained-XOR encoded using header[4].
    """
    if len(header6) != 6:
        raise ValueError("socket header must be 6 bytes")
    ack4 = header6[:4]
    rot = state.next_lcg_rot(ack4[0])
    rotated_len = header6[4] | (header6[5] << 8)
    expected_len = rol16(rotated_len, rot)
    if expected_len != len(payload):
        raise ValueError(
            f"socket length mismatch: decoded={expected_len}, actual={len(payload)}, rot={rot}"
        )
    if state.last_ack4 != b"\x00\x00\x00\x00" and ack4 != state.last_ack4:
        # Do not reject: historical proxies/reconnects can make ACK state discontinuous.
        state.metadata["ack_mismatch"] = (state.last_ack4.hex(), ack4.hex())
    state.rx_frames += 1
    return chain_decode(payload, header6[4])


def encode_socket_client_frame_for_test(payload: bytes, state: SessionState, ack4: bytes) -> bytes:
    """Reference encoder used by unit tests to model the V860 client O0O() method."""
    if len(ack4) != 4:
        raise ValueError
    rot = state.next_lcg_rot(ack4[0])
    rotated_len = ror16(len(payload), rot)
    h4, h5 = rotated_len & 0xFF, (rotated_len >> 8) & 0xFF
    return ack4 + bytes((h4, h5)) + chain_encode(payload, h4)


def split_commands(payload: bytes) -> List[str]:
    text = payload.decode("utf-8", errors="replace")
    return [line.strip("\r") for line in text.split("\n") if line.strip("\r")]


def join_server_lines(lines: Iterable[str]) -> bytes:
    return ("\n".join(lines) + "\n").encode("utf-8")


def decode_dat_resource(data: bytes) -> bytes:
    """Decode V860 csys/*.dat chain format (key = file length low byte)."""
    return chain_decode(data, len(data) & 0xFF)


def encode_dat_resource(plain: bytes) -> bytes:
    """Inverse of decode_dat_resource, preserving original length-derived key."""
    return chain_encode(plain, len(plain) & 0xFF)
