# HZW V860 compatibility server — protocol recovery alpha

Experimental clean-room compatibility server for the uploaded J2ME **海贼王 V8.60.0** client.
It is intended for preservation/interoperability testing while the original protocol is being recovered.

## What works in this alpha

- V860 TCP listener (`5926` by default)
- V860 HTTP listener (`8080` by default)
- confirmed socket/HTTP chained-XOR codecs
- confirmed socket `0xA5A5` response length header
- confirmed client socket LCG/rotated-length decoder
- cid checksum and `sn` tracking
- initial `CONNECT` + `kawa` bootstrap handling
- basic account/login/message/menu test responses
- compatibility title/menu screen after successful login
- protocol smoke client for end-to-end TCP verification
- Windows one-click run/test/patch scripts
- detailed protocol logging
- JAR `csys/list.dat` patcher to redirect proxy group #3 to your server
- V860 resource extractor

Gameplay/map/battle behavior is intentionally **not fabricated** yet; those handlers will be added as their exact formats are recovered from the client.

## Run

Python 3.10+; no third-party packages are required.

```bash
python server.py --debug
```

This listens on:

- TCP `0.0.0.0:5926`
- HTTP `0.0.0.0:8080`

## Patch a copy of the original JAR

For an emulator running on the same computer:

```bash
python tools/patch_client.py /path/to/hzw-touch-360x360.jar \
  --out /path/to/hzw-touch-360x360-local.jar \
  --host 127.0.0.1
```

For a phone/emulator on another device, use the computer's LAN address instead, for example `192.168.1.50`.

The patcher changes only proxy group **#3**, which is the group referenced by the five server menu entries in this V860 client. Keep the original JAR untouched.

## Test

```bash
python -m unittest discover -s tests -v
```

## Status

This is an **alpha protocol harness**, not a completed recreation of the original backend. The framing code is based on direct bytecode analysis of the V860 client; gameplay handlers are placeholders until their parameters are documented.

## Phase 2 runbook

See `docs/PHASE2_RUN_V860.md` for the original-client launch milestone and Windows/LAN test flow.
