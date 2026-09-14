# Phase 3 — V860 world bootstrap

This milestone removes the compatibility placeholder menu and attempts to enter the original V860 world renderer.

## Recovered path

`<log_suc>` → binary record type 1 (map switch) → client `#map 60hzwlocalsj` → special marker 127 map download → binary record type 4 (player entity using local `c/14.chj`) → `<r>walk1`.

The first map is deliberately a minimal 24x24 bootstrap field. It proves the recovered world protocol; it is **not yet the original Windmill Village art/map**.

## Real-client test

1. Update the repository.
2. Close the old server window.
3. Double-click `scripts\\run_server.bat`.
4. Open the same patched V860 JAR in SjBoy.
5. Login/create the guest account.
6. Watch the server log for `#map 60hzwlocalsj` followed by `Serving bootstrap map key=hzwlocalsj`.
7. Capture the V860 screen and the last server log lines, whether it succeeds, goes black, errors, or shows a map/player.

## Automated validation

Run `python -m unittest discover -s tests -v` and then the end-to-end world smoke client. The smoke path must finish with `SMOKE_WORLD_OK`.
