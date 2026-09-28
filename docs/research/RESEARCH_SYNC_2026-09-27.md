# Research sync — 2026-09-27

## Repository baseline

- Default branch checked: `main`
- Baseline commit: `f47de6c90470` (`research: add consolidated sync manifest`)
- Working branch: `work/v860-protocol-evidence-20260927`
- Newer implementation branch audited: `work/v860-evidence-full-server` at `a5e2976055c1`
- The implementation branch and `main` have diverged; this research/protocol batch is based on `main` so it preserves the complete `docs/research` history and does not silently merge REBUILD campaign data.

## Added in this batch

- `V860_PAYLOAD_124_127_AND_FIRST_PACKET_2026-09-27.md`
  - freezes known framing for normal records and marker 127;
  - leaves 124–126 unknown;
  - separates original-client/decompile evidence from smoke-client fixtures;
  - records the absence of a fresh original first-packet capture.
- `WINDMILL_MAP_01_EVIDENCE_SPEC_2026-09-27.md`
  - defines the smallest evidence-backed opening topology;
  - leaves V860 geometry, IDs, collision and visuals unknown.
- `windmill_map_01_evidence.json`
  - machine-readable evidence/unknown-field ledger for the first map node.
- `JAR_ARCHIVE_MIRROR_AND_DOSPY_AUDIT_2026-09-27.md`
  - records one public archive mirror chain and three additional DOSPY device candidates;
  - keeps all unverified binaries at `VERSION_DRIFT / JAR_CANDIDATE`.
- `payload_stream.py` and `tools/analyze_payload.py`
  - parse decoded mixed payloads conservatively;
  - preserve 124–126 as opaque bytes.
- `jar_diff.py` and `tools/diff_jars.py`
  - generate deterministic SHA-256, Manifest, class/resource and entry-level multi-JAR comparisons.

## Environment blockers recorded, not guessed around

- No original V860 JAR/JAD was present in the workspace or user profile search.
- No saved PCAP/PCAPNG/HAR matching HZW was present.
- No installed Java/J2ME emulator was found.
- QJTYW search cache exposes V860 device labels, but the origin domain was unreachable during direct retrieval.
- The 80joy historical game URL now renders `undefined`; its site search returns no HZW result.

These limitations prevent a truthful new first-packet capture and real multi-JAR result in this batch. The new tools make the next acquired artifacts immediately comparable without assigning unsupported semantics.
