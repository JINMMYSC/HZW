# HZW 考古来源索引

> 所有来源先记录、再分级；转载页只证明其承载的文本/附件线索，不能自动升级为 V860 直接证据。

## A. 客户端 / JAR / 版本页

| 状态 | 来源 | 已恢复信息 | 下一步 |
|---|---|---|---|
| `JAR_CANDIDATE_HIGH` | https://www.dospy.wang/thread-19446-1-1.html | 2023 帖保存多机型《海贼王-秘宝传说》JAR 附件名和大小；E62=373.43KB、N73=501.42KB；作者称 N86 实测联网正常 | 追回附件本体；提取 Manifest/hash/class/strings/resources |
| `ORIGINAL_ARCHIVE_INDEX` | https://qjtyw.cn/wapindex-1000-23.html | 2012-08-01 `海贼王秘宝传说更新版v860`；2012-02-11 `海贼三版804客户端绝版` 266.8KB | 追回具体详情页/下载参数 |
| `ORIGINAL_ARCHIVE_INDEX` | https://qjtyw.cn/wapindex-1000-1.html | `海贼五倍加速版V859`、`海贼王去经验框客户端V8`、凯旋海贼伴侣V3 等 | 精确日期/详情页/文件名 |
| `ORIGINAL_ARCHIVE_INDEX` | https://qjtyw.cn/wapindex.aspx?classid=1&path=null%2Findex.aspx&sid=-2-0-0-393-0&siteid=1000 | `海贼王二版810加速`、`海贼王860三合一原速版`、`海贼五倍加速版V859`、`加强版海贼伴侣和辅助` | 通过搜索缓存/Wayback/参数枚举找详情 ID |
| `JAR_CANDIDATE` | https://www.quanjizhong.top/thread-237-1-1.html | K700 176×220 列表含 `海贼王-秘宝传说_索爱 K700系列(176x220).jar` | 取得压缩包后比对版本字符串 |

### DOSPY 当前已知附件

- E62: `海贼王-秘宝传说_诺基亚 E62系列(320×240)-382392.jar` — 373.43KB
- N73: `海贼王-秘宝传说_诺基亚 N73系列(240×320)-513458.jar` — 501.42KB
- N70: `海贼王-秘宝传说_诺基亚 N70系列(176×208)-496184.jar` — 484.55KB
- N97: `海贼王-秘宝传说_诺基亚 N97系列(360×640)-403336.jar` — 393.88KB
- N8: `海贼王-秘宝传说_诺基亚 N8系列(360×640)-353130.jar` — 344.85KB
- N7370: `海贼王-秘宝传说_诺基亚 N7370系列(240×320)-367200.jar` — 358.59KB
- X3: `海贼王-秘宝传说_诺基亚 X3系列(240×320)-511150.jar` — 499.17KB
- QD: `海贼王-秘宝传说_诺基亚 QD系列(176×208)-353197.jar` — 344.92KB
- 128×128 通用版 — 293.33KB

## B. 同期原始攻略 / 评测

| 状态 | 来源 | 价值 |
|---|---|---|
| `ORIGINAL_DOC_2007` | https://m.ali213.net/gonglue/071119/14525.html | 技术测试时期任务、聊天、好友、瞬移地图、按键/系统线索 |
| `ORIGINAL_DOC_2008` | https://m.ali213.net/gonglue/080521/14056.html | 副官基础值/成长值、桃子等，证明 base 与 growth 必须分开 |
| `ORIGINAL_DOC_2008` | https://m.ali213.net/gonglue/080815/13871.html | 刀魂现实时间技能、群攻/闪避等技能机制 |
| `ORIGINAL_DOC_2008` | https://m.ali213.net/gonglue/080829/13792.html | 医师组队经验加成、70级装备/BOSS 等线索 |
| `ORIGINAL_DOC_2008` | https://games.sina.com.cn/y/n/2008-08-28/1347266119.shtml | 随手互动/无尽宝藏官方宣传；同时证明“帮派/宠物/结婚/师徒”等那段属于《大宋豪侠》，不得误灌 HZW |
| `ORIGINAL_DOC` | https://games.sina.com.cn/info/cmgames/kjava/22.shtml | 新浪游戏资料库：Kjava RPG；组队/聊天/阵营对抗等简介 |

## C. Bilibili 视觉证据

### 2021 老版视觉优先

- https://www.bilibili.com/video/BV1vT4y1P7qF/ — 2021-02-01 风车镇遇草帽小子
- https://www.bilibili.com/video/BV1WX4y1N7HE/ — 2021-02-03 翻倒海军基地
- https://www.bilibili.com/video/BV1Rr4y1K782/ — 2021-02-04 基本操作及任务

`基本操作及任务` 关联列表还暴露：新人保姆级教学解说、单人不带副无神技（我）极限、美杜莎升级/技能等，待继续枚举 BV 号。

### 后期服 / POST_V860

- https://www.bilibili.com/video/BV1NAvveHEPN/ — 2024-08-01 美杜莎海滩前六关
- https://www.bilibili.com/video/BV1rqxqeYEB8/ — 2024-09-28 大小号最强副本
- https://www.bilibili.com/video/BV1bzqJYBEYc/ — 2024-12-08 轮回7 / 龙魂宝箱 / 神铸装备
- https://www.bilibili.com/video/BV1nZLqzAEfu/ — 2025-04-27 美杜莎最强海滩 / 219w

## D. 贴吧

目标：`随手互动海贼吧`。

目前直接帖子抓取经常 403，执行策略：

1. 搜索引擎 `site:tieba.baidu.com` + 专有词；
2. 吧友个人主页；
3. 枚举用户名/帖子标题/发布时间/正文摘要；
4. 精确标题反搜；
5. 以副官/装备/地图/服务器/版本号继续横向扩散。

已知后期索引词：89级、全身神铸+20、35服、收副官、三无神技、幺蛾子、贝壳、职业属性加点、怀念海贼王。

本轮直接搜索 `黄金军神 / 刀魂战士 / 追猎者 / 雷象 / 剑齿兽 / 法宝融合` 没有获得足够可靠的新正文命中，暂不写成事实。

## E. 图片指针

### 搜狐旧图

- `Img253086137.jpg`
- `Img253086138.jpg`

来源文章：2007《海贼王》动画剧情 vs 副官系统(图)。当前 `IMAGE_POINTER`。

### 洛克岛旧攻略图片 UUID

- `71c5d890-c762-855f-d7a6-315dc22ba8a7.jpg`
- `9132f34f-76af-ae8c-b877-17597ef1cccd.jpg`
- `7ab316c4-a6ae-049e-8fdf-a036ca94cf26.jpg`
- `4ba6e4cc-2be3-d7c2-fffc-13b95a57f81b.jpg`
- `ff386e35-973b-2469-9cd6-5c6892bba642.jpg`
- `92f2dad3-d57b-47b5-b5bb-d98fb70841cd.jpg`

## F. 过滤规则

检索命中以下现代作品时默认排除：

- 《航海王热血航线》
- 《航海王燃烧意志》
- 《热血海贼王》
- 现代 3D/触屏 One Piece 手游

《大宋豪侠》资料只允许用于识别“随手互动共用平台/跨游戏社交”等明确跨产品事实；其独有帮派/宠物/婚姻/师徒/战场系统不得移植到 HZW 证据库。
