# V860 direct download-page evidence — 2012-08-01

Classification: **V860_DIRECT_CONFIRMED**

Primary surviving page:
https://qjtyw.cn/download/book_view.aspx?classid=23&id=419&lpage=1&sid=-2-0-0-0-320&siteid=1000&sp=0

Alternate indexed route:
https://qjtyw.cn/download-419.html?lpage=1&sp=0

## Exact surviving metadata

- Software name: `海贼王秘宝传说更新版v860`
- Uploader: `超级管理员(1000)`
- Update date: **2012-08-01**
- Category: `回合`
- Historical page view count in surviving index: ~163k

## V860 change list preserved by the page

1. `法宝融合`
2. `新坐骑：雷象、剑齿兽`
3. `新副官：追猎者`
4. `修正V859版客户端选择菜单出现连点或菜单重叠的问题。`

This is the strongest direct V860 evidence currently recovered. It both identifies V860-specific content and explicitly names a V859 UI/client bug fixed by V860.

## V860 client/device build matrix preserved by the download page

The surviving page exposes these download labels:

- `HZW_E62` — shown as `jar/374`, historical downloads ~12.1k
- `HZW_E680`
- `HZW_E770`
- `HZW_GEHK`
- `HZW_GEHT`
- `HZW_GELK`
- `HZW_GELT`
- `HZW_GESEK`
- `HZW_GESK`
- `HZW_GESTK`
- `HZW_GETK`
- `ZW_K300`
- `HZW_K500`
- `ZW_K700`
- `HZW_L6`
- `HZW_MOTOV8`
- `HZW_N73D`
- `HZW_S700`

The page labels the additional variants as `共存版下载`.

Notable historical download counts visible in the index include roughly:

- HZW_E62: 12,124
- HZW_S700: 8,701
- HZW_E680: 4,458
- HZW_N73D: 4,139

Counts are archival context, not gameplay evidence.

## Restoration implications

### 1. V860 content baseline can now include these as direct evidence

- 法宝融合
- 雷象 mount
- 剑齿兽 mount
- 追猎者 deputy

These no longer need to be treated as generic late-server material.

### 2. V859 -> V860 UI delta is directly documented

V859 had a client selection-menu defect described as `连点或菜单重叠`; V860 explicitly fixes it. During UI reconstruction, any footage/screenshot showing overlapping selection menus or repeated selection behavior may represent V859 or an unpatched derivative rather than stock V860.

### 3. Device-specific builds are proven

The old V860 distribution was not one universal JAR. The page itself lists many named JAR/device variants. Therefore candidate archive files must retain device/build identity rather than being renamed to a generic `V860.jar`.

### 4. Priority recovery order changes

Highest-value exact search targets are now:

1. `HZW_E62.jar`
2. `HZW_S700.jar`
3. `HZW_N73D.jar`
4. `HZW_MOTOV8.jar`
5. remaining HZW/ZW variants above

Search both bare labels and combinations with `v860`, `海贼王`, `秘宝传说`, `92le`, `qjtyw`.

### 5. Candidate-JAR verification

For each recovered build record:

- SHA-256
- byte size
- MANIFEST.MF / MIDlet-Version / MIDlet-Name / MIDlet-Vendor
- class inventory
- resource filenames and dimensions
- PNG hashes
- embedded strings
- RMS/store names
- server hosts/IP/ports
- device/model checks
- menu implementation and timing constants

Then compare builds to determine whether they differ only in screen/key/device adaptation or also contain gameplay/content differences.

## Evidence discipline

The QJTYW page is direct evidence that a download entry named `海贼王秘宝传说更新版v860` existed on 2012-08-01 and exposed the above change list/build labels. It is **not yet proof that any modern mirror JAR is byte-identical to one of these 2012 files**. Modern archive JARs remain `NEEDS_BINARY_VERIFICATION` until hashes/manifests/strings are inspected.
