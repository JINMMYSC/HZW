# HZW 客户端实体 / APK 线索 — 2026-09-15

> 目标：把“网页提到过客户端”与“已经定位可取得实体”严格分开。未拿到文件并验证 Manifest / 版本字符串 / 资源前，不把候选 JAR 冒充成 V860。

## 1. 当前最高优先级：DOSPY E62

来源：

- https://www.dospy.wang/thread-19446-1-1.html
- QJTYW V860 页面：https://qjtyw.cn/download/book_view.aspx?classid=23&id=419&lpage=1&sid=-2-0-0-0-320&siteid=1000&sp=0

DOSPY 帖保留附件：

`海贼王-秘宝传说_诺基亚 E62系列(320×240)-382392.jar` — 373.43KB

QJTYW V860 更新页的 E62 下载项显示：

`HZW_E62 (jar/374)`

两者文件体量高度接近，因此当前分类：

`JAR_CANDIDATE_HIGH`

仍需：

- 取得 JAR 实体；
- SHA-256；
- `META-INF/MANIFEST.MF`；
- MIDlet 名称/版本/Vendor；
- class / strings / PNG 列表；
- server URL / IP / opcode 相关字符串；
- 与 V859 / 804 / 810 做 diff。

## 2. 4500 Java 游戏合集：公开网盘入口已定位

来源页面：

https://www.game1319.com/7708.html

目录明确列有：

`海贼王-秘宝传说(320x240)`

页面公开给出两个分享入口：

- 百度网盘：https://pan.baidu.com/s/1hu_NEZnwkWiJ-hRybMAjeg
- 夸克网盘：https://pan.quark.cn/s/6caedd521c6c

当前阻塞：页面把提取码放在付费可见区域。

分类：

`JAR_CANDIDATE / ARCHIVE_LOCATED / EXTRACTION_CODE_BLOCKED`

注意：仅凭合集名称不能证明该包内版本是 V860。拿到文件后必须与 DOSPY E62、QJTYW V860 机型/体量/字符串交叉比对。

## 3. A9VG 6000 J2ME 游戏整合包

来源：

https://bbs.a9vg.com/thread-9056012-1-1.html

目录明确列：

`海贼王-秘宝传说`

当前附件/下载存在登录或权限墙。

分类：

`JAR_CANDIDATE / ARCHIVE_LOCATED / LOGIN_BLOCKED`

价值：这是独立于 DOSPY / QJTYW / game1319 的另一份存档源，可用于验证是否保存不同分辨率或不同历史版本。

## 4. 80joy 在线 J2ME MIDlet

页面：

https://www.80joy.com/j2me/%E6%B5%B7%E8%B4%BC%E7%8E%8B-%E7%A7%98%E5%AE%9D%E4%BC%A0%E8%AF%B4

页面当前仍能显示在线 J2ME 模拟器流程：

`Downloading midlet... -> Starting midlet...`

并提供完整数字键/软键模拟控件。

分类：

`JAR_CANDIDATE / LIVE_MIDLET_HOST`

下一步：

- 追页面 JS / WASM 配置；
- 搜 `.jar` / `.jad` / `midlet` / ROM 资源路径；
- 查网络请求或公开资源清单；
- 若取得 JAR，立即提取 Manifest / classes / strings / PNG。

## 5. 其他明确 JAR 名称来源

### Sony Ericsson K700

来源：全机种 Java 游戏目录。

`海贼王-秘宝传说_索爱 K700系列(176x220).jar`

与 QJTYW V860 页面 K700 机型线可交叉验证，但当前仍只能标：

`JAR_CANDIDATE`

### Motorola V8

来源：全机种 Java 游戏目录。

`海贼王-秘宝传说_摩托罗 V8拉系列(240x320).jar`

与 QJTYW 的 `MOTOV8` 机型线可交叉验证。

当前：`JAR_CANDIDATE`。

## 6. Android 客户端：历史存在已有司法证据

2017 年相关法院判决正文记录，随手互动一方提交过：

> 在 Google Play / 谷歌商店下载安卓版“海贼王”游戏的下载页面打印件。

因此“历史上存在 Android 版”不再只是论坛传闻，应记录为：

`ORIGINAL_DOC / ANDROID_EXISTENCE_EVIDENCED`

但目前仍未恢复：

- package name；
- APK 文件；
- versionCode/versionName；
- signing certificate；
- assets；
- server URL；
- opcode / protocol classes。

当前对 AppChina / 豌豆荚 / 安智 / 当乐 Android / 百度手机助手 / APKPure / APKCombo 等公开索引的定向搜索尚未得到可以可靠对应“随手互动 HZW”的 APK 实体。

因此 APK 当前分类：

`APK_CANDIDATE_UNKNOWN / NEEDS_APK`

## 7. 同一司法材料可固定的历史名称与年代

司法材料还记录：

- 随手互动从 2007 年开始创作并提供《海贼王》游戏下载；
- 2008 年相关材料中出现 `海贼王online：七海寻缘`；
- `海贼王online：七海寻缘` 获 2008 ChinaJoy 金翎奖“最佳手机网络游戏”；
- 另记录 2007/2008 前后《海贼王》获得手机网游相关奖项。

这些可以用于证明“七海寻缘”为真实历史官方名称，但奖项/名称不能自动裁决某个 JAR 的具体版本号。

## 8. 实体取得后的统一检查脚本目标

任何 JAR/APK 一旦取得，第一时间生成：

```text
sha256
size
manifest / AndroidManifest
file tree
class list
resource list
PNG dimensions
all printable strings
URL/IP/domain list
map-like strings
NPC strings
item strings
deputy strings
quest strings
menu/key strings
protocol/opcode candidate constants
```

随后做版本差分：

```text
V859 original <-> V859 5x speed
V860 original <-> V860 三合一/共存
804 <-> 810 <-> 859 <-> 860
E62 <-> N73D <-> S700 <-> MotoV8
J2ME <-> Android
```

## 9. 当前客户端线优先级

1. DOSPY E62 373.43KB 实体；
2. 80joy 在线 MIDlet 的真实资源路径；
3. game1319 4500 Java 合集中的 320×240 JAR；
4. DOSPY N73 501.42KB；
5. V859 原版 / 五倍加速版；
6. V860 三合一原速 / 五版加速共存；
7. Moto V8 / K700；
8. 历史 Android APK。
