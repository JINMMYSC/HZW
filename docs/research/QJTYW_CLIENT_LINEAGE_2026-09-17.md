# QJTYW client lineage evidence — 2026-09-17

Evidence classes used here: `CONFIRMED_INDEX`, `VERSION_DRIFT`, `NEEDS_JAR`.

## New direct public-index evidence

The still-indexed QJTYW pages expose a cluster of modified clients/helpers on the same old mobile-game portal. This is stronger than isolated search-engine snippets because the terms coexist on the site's own indexed category pages.

### CONFIRMED_INDEX

Source: https://qjtyw.cn/wapindex.aspx?classid=1&path=null%2Findex.aspx&sid=-2-0-0-393-0&siteid=1000

Visible entries include:

- `海贼王二版810加速`
- `海贼王860三合一原速版`
- `海贼五倍加速版V859`
- section/link wording `海坛.客户端`
- section/link wording `加强版海贼伴侣和辅助`

A second indexed QJTYW page independently exposes the same V810/V859/V860 cluster:

Source: https://qjtyw.cn/wapindex.aspx?classid=1&path=null%2Findex.aspx&sid=-3-0-0-1498-176&siteid=1000

This page again shows:

- `海贼王二版810加速`
- `海贼王860三合一原速版`
- `海贼五倍加速版V859`
- `加强版海贼伴侣和辅助`

Another indexed category page exposes:

Source: https://qjtyw.cn/wapindex-1000-1.html?path=null%2Findex.aspx

- `凯旋海贼伴侣最新优化V3`
- `海贼五倍加速版V859`
- `海贼王去经验框客户端V8...` (index text truncates the suffix)
- `加强版海贼伴侣和辅助`

## Interpretation / restoration significance

1. V810, V859 and V860 are not merely numbers recovered from unrelated modern recollections. They occur together in a historical mobile-client modification/download context.
2. V859 has an explicitly indexed `五倍加速版`; V860 has an explicitly indexed `三合一原速版`. Therefore speed modification and multi-feature packaging must be treated as client-mod variants, not assumed to be official V860 behavior.
3. `去经验框客户端` is independently visible on QJTYW. UI reconstruction must therefore distinguish official HUD/UI from helper/modded screenshots where the experience frame may have been removed.
4. `海贼伴侣` / `辅助` existed as a separate helper lineage. Any screenshots/videos made with it may expose overlays, automation or altered presentation not present in the stock client.
5. The `三合一` wording strongly suggests a bundle of modifications/features, but its exact three components are **not yet proven**. Do not infer them until the detail page, attachment name, JAR or contemporary post is recovered.

## NEEDS_JAR

Priority artifacts to recover and hash:

- stock V860 JAR/JAD
- `海贼王860三合一原速版`
- stock V859 and `海贼五倍加速版V859`
- `海贼王二版810加速`
- complete filename/version for `海贼王去经验框客户端V8...`
- `海贼伴侣` / `加强版海贼伴侣和辅助`

When recovered, compare MANIFEST.MF, class inventory, string table, resource PNGs, RMS names, server hosts/ports, timing constants and UI dimensions against the known V860 client.

## Caution

QJTYW is evidence for the existence/naming of these modified clients and helpers. It does **not** by itself prove that their modifications belong to the official V860 feature set.
