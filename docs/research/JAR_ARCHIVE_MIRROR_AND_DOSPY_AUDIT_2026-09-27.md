# V860 客户端候选归档镜像与 DOSPY 附件审计 — 2026-09-27

> 本文记录本轮新增的客户端候选入口与附件元数据。现代归档中的同名 JAR 未经 Manifest、内部版本串和 hash 验证，不得认定为 V860。

## 结论

1. 一个现代 J2ME 大型合集的公开目录明确列出 `海贼王-秘宝传说`，并公开移动云盘、夸克和目录表入口。状态从“论坛列表线索”升级为 `JAR_CANDIDATE / PUBLIC_SHARE_PARAMETERS_EXPOSED`。
2. 多个论坛转载使用完全相同的分享 ID 和文案，属于同一镜像链，不能当作多个独立 JAR 来源。
3. DOSPY 索引新增 Nokia N6230i、N6101、N5500 三个候选包及精确文件名、页面大小和上传时间。
4. 本轮没有取得任何 JAR，没有 Manifest、版本串、hash 或服务器地址证据。全部现代归档继续标记 `VERSION_DRIFT / JAR_CANDIDATE`。

## 大型 J2ME 合集入口

主核对页：

- 标题：`[下载]Java游戏资源整合包 下载即玩 6000个游戏列表内附安卓电脑java游戏模拟器`
- URL：https://ac.stage3rd.com/forumTopicRead.asp?id=1820
- 发帖时间：`2025-11-09 11:57:37`
- 发帖用户：`jiuxian5552`
- 目录条目：`海贼王-秘宝传说`

公开参数：

- 移动云盘：https://yun.139.com/shareweb/#/w/i/2qidERSvNGKk4
- 分享 ID：`2qidERSvNGKk4`
- 提取码：`ipdd`
- 夸克：https://pan.quark.cn/s/04eedb47c426
- 夸克分享 ID：`04eedb47c426`
- 目录/备用查询：https://www.kdocs.cn/l/chNjYZiEeoKS

证据等级：`VERSION_DRIFT`。

亲验状态：Stage3rd 正文可读；移动云盘只到通用分享页；夸克和 KDocs 当前抓取不可达。未验证云盘文件树、压缩包或目标 JAR。

### 同一镜像链

以下页面复用相同的移动云盘 ID、提取码与夸克 ID：

- https://www.91switch.com/posts/details/886
- https://bbs.a9vg.com/thread-9056012-1-1.html
- https://bbs.liuxingw.com/t/63697.html
- https://gmerago.com/forum.php?mod=viewthread&tid=7298
- https://acgwolf.com/discuz/viewthread.php?page=1&tid=53226
- https://bbs.girigirilove.com/circle/87623/
- https://ac.stage3rd.com/forumTopicRead.asp?id=1820

这些转载只能交叉确认公开分享参数被多页保存，不能增加独立样本数量。

页面标题称“6000 个游戏”，正文又称“4000 多个未分类游戏”和“一千多个已分类游戏”。精确文件数属于 `ARCHIVE_METADATA_CONFLICT`。

## DOSPY 新增机型附件

原帖：

- 标题：`〖Java游戏〗海贼王-秘宝传说2023年4月还在运营的网络游戏`
- URL：https://www.dospy.wang/thread-19446-1-1.html
- 作者：`史阿文`
- 发帖时间：`2023-04-23 16:12`

实时页面当前返回 Discuz 数据库错误；搜索缓存仍保存附件元数据。

| 机型 | 原帖精确文件名 | 页面大小 | 上传时间 | 等级 |
|---|---|---:|---|---|
| Nokia N6230i / 208×208 | `海贼王-秘宝传说_诺基亚 N6230i系列(208×208)-281185.jar` | 274.59 KB | 2023-04-23 16:10 | `VERSION_DRIFT` |
| Nokia N6101 / 128×160 | `海贼王-秘宝传说_诺基亚 N6101系列(128×160)-303803.jar` | 296.68 KB | 2023-04-23 16:10 | `VERSION_DRIFT` |
| Nokia N5500 / 208×208 | `海贼王-秘宝传说_诺基亚 N5500系列(208×208)-373329.jar` | 364.58 KB | 2023-04-23 16:09 | `VERSION_DRIFT` |

统一状态：`JAR_CANDIDATE / VERSION_UNKNOWN / NEEDS_BINARY_VERIFICATION`。

搜索缓存共列出 12 个附件：小屏通用、X3、QD、N7370、N6230i、N6101、N5500、N97、N73、N70、N8、E62。它还保存五个未恢复截图文件名：

- `IMG_20230423_154345.jpg`
- `IMG_20230423_154224.jpg`
- `IMG_20230423_154159.jpg`
- `Screenshot_20230423_155201_ru.playsoftware.j2melo.jpg`
- `IMG_20230423_155851.jpg`

截图分类为 `IMAGE_POINTER`。文件名中的 `ru.playsoftware.j2melo` 只能作为模拟器候选线索，不能据此推导版本或配置。

## 2023 联网报告的边界

原帖声称 Android 模拟器可运行，N86 经作者测试可联网。分类：`LATE_SERVER / POST_V860_PLAYER_REPORT_2023`。

该文字没有抓包、域名、IP、端口、opcode 或服务端身份，不能作为 V860 首包结构证据。

## 与 V860 直接机型矩阵的关系

QJTYW 2012-08-01 页面仍是当前 V860 机型标签的直接来源：

- https://qjtyw.cn/download/book_view.aspx?classid=23&id=419&lpage=1&sid=-2-0-0-0-320&siteid=1000&sp=0
- https://qjtyw.cn/download-419.html?lpage=1&sp=0

该页列出 `HZW_E62`、`HZW_N73D`、`HZW_MOTOV8`、`HZW_S700` 等。现代同名 JAR 必须取得实体并核对 `MIDlet-Version: 8.60.0`、内部版本串 `860.1HZ0000.NON5800.CT`、资源和协议后，才能升级为 `V860_DIRECT`。

N6230i、N6101、N5500 尚未出现在已恢复的 QJTYW V860 标签中，必须保持版本隔离。

## 获取后的固定检查

1. 记录归档文件名、归档 SHA-256、JAR 相对路径和 JAR SHA-256；
2. 读取 Manifest 的 Name、Version、Vendor、Profile、Configuration；
3. 搜索 `860.1HZ0000.NON5800.CT`、`860`、`859`、`随手互动`、`92le`；
4. 提取 URL/IP/端口、首包常量、opcode 候选和 RMS 名称；
5. 使用 `tools/diff_jars.py` 对 E62/N73D/MOTOV8/S700 与候选包做差分；
6. 没有直接版本证据或与 V860 冲突时继续保持 `VERSION_DRIFT`。

## 本轮未取得

- 未下载大型合集；
- 未取得 JAR/Manifest/hash；
- 未恢复新的 Bilibili BV 号；
- 未恢复贴吧图片正文；
- 未执行原版客户端首包抓取。
