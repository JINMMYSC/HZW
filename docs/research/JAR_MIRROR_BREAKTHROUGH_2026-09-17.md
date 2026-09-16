# JAR mirror breakthrough — 2026-09-17

## Status

This is the strongest surviving-client lead found so far. It does **not** yet prove V860, but it proves that a JAR named for this game survives in at least two modern preservation collections.

## Lead A — Nokia QD 176x208 collection

Source:
https://www.quanjizhong.top/thread-233-1-1.html

The preservation thread states that its collection contains 372 Nokia QD-specific Java games at **176x208** resolution and that these are device-specific files. In the published file inventory it explicitly lists:

`海贼王-秘宝传说_诺基亚 QD系列(176x208).jar`

The same post says the archive is mirrored through Quark, Baidu, 123 and Xunlei cloud storage, but the actual resource links are hidden behind a forum reply/login gate.

### Restoration significance

- We now have an **exact surviving filename**, not merely a recollection that a JAR once existed.
- The device target is explicit: Nokia QD / 176x208.
- This is especially interesting because 2007 contemporary material names Nokia 40/60-series devices and an N70 test device; the QD build may preserve an older/small-screen resource layout or a compatible branch.
- Once acquired, this JAR should be treated as a candidate lineage sample and compared against V860 rather than assumed to be V860.

### Required validation when obtained

1. SHA-256/MD5.
2. `META-INF/MANIFEST.MF`: MIDlet-Name, MIDlet-Version, vendor, profile/configuration.
3. Class inventory and obfuscation pattern.
4. PNG dimensions/resource names.
5. RMS/store names.
6. Server domains/IP/ports.
7. Search strings: `随手互动`, `92le`, `无尽宝藏`, `七海寻缘`, `秘宝传说`, `860`, `859`, `810`, known island/NPC names.
8. Compare UI resources against Qinjiu videos and 2007-2012 screenshots.

## Lead B — 6000-game Java preservation bundle

Source:
https://www.91switch.com/posts/details/886

The public game inventory contains a separate entry:

`海贼王-秘宝传说`

The page also publishes downloadable preservation bundles via cloud storage. This appears independent of the QD-specific collection and therefore gives us a second path to a surviving JAR.

### Why two independent collections matter

If both archives can be acquired, compare hashes and manifests. If they differ, we may have two device/version branches. If they match, one can validate the other and provide redundant preservation.

## Classification

- `SURVIVING_JAR_LEAD`: confirmed by public inventory.
- `VERSION_UNKNOWN`: no evidence yet that either file is specifically V860.
- `HIGH_PRIORITY_ACQUISITION`: obtaining and statically inspecting these JARs now outranks generic search for the literal phrase `V860.jar`.

## Important caution

Do not merge QD 176x208 visuals directly into the V860 restoration until version and resource lineage are established. The value of this discovery is that a real binary candidate appears to survive, not that its exact version has already been identified.
