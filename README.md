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
- basic account/login/message responses
- recovered binary world bootstrap after successful login
- type-1 map switch + marker-127 map download
- type-4 local player entity + `<r>walk1` selector
- protocol smoke client for end-to-end TCP verification
- Windows one-click run/test/patch scripts
- detailed protocol logging
- JAR `csys/list.dat` patcher to redirect proxy group #3 to your server
- V860 resource extractor

Phase 3 includes a minimal protocol-bootstrap map so the original world renderer can be exercised. It is not yet the original Windmill Village; NPC, original map content, collision semantics and battle remain under recovery.

## Run

Python 3.10+; no third-party packages are required.

```bash
python phase3_server.py --debug
```

On Windows, double-click `scripts\\run_server.bat`.

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

The Phase-3 end-to-end smoke path should finish with `SMOKE_WORLD_OK`.

## Status

This remains an **alpha compatibility server**, but the real V860 client has already verified the Phase-2 transport/login path. Phase 3 now exercises the recovered world/map binary path with a minimal local field and a player entity using the client's bundled `c/14.chj` resource.

## Runbooks

- `docs/PHASE2_RUN_V860.md` — original-client launch/login baseline.
- `docs/PHASE3_WORLD_BOOTSTRAP.md` — map/player world-entry test.
