# Phase 2 — run original V860 against the compatibility server

## Goal

Original V860 JAR -> compatibility server -> login -> compatibility menu.

## Windows same-PC test

1. Install Python 3.10+.
2. Clone/download this repository.
3. Run `scripts\test_protocol.bat` first. Unit tests should pass and the smoke client should print `SMOKE_OK`.
4. Run `scripts\patch_client_local.bat ORIGINAL.jar` to create a localhost-patched copy.
5. Start the server with `scripts\run_server.bat`.
6. Open the generated `*-localhost.jar` in a J2ME emulator at 360x360.
7. Select one of the original server menu entries that use proxy group #3.

Expected server console flow:

```text
CONNECT 1hzg0
V860 bootstrap accepted
new
860.1HZ0000.NON5800.CT
<newacc>...
<log_suc>
<title>V860兼容服务器
<menu>...
```

## Phone / another device

`127.0.0.1` points to the phone itself. Patch with the server PC LAN IP instead:

```bat
scripts\patch_client_lan.bat hzw-touch-360x360.jar 192.168.1.50
```

Allow inbound TCP ports 5926 and 8080 in Windows Firewall.

## Current limitation

The login transport is implemented. The original player/map/NPC world bootstrap is still being recovered, so the current post-login screen is a compatibility menu rather than the original world.
