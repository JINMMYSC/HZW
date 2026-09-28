# V860 payload 124–127 与首包状态表 — 2026-09-27

> 本文记录仓库中此前保存的 V860 逆向结论、协议测试夹具和本轮环境检查。当前工作区缺少对应 JAR、hash、反编译偏移和原始抓包，因此既有逆向结论统一保留为待原始工件复核，不能在本轮升级为 `V860_DIRECT`。

## 本轮结论

- `0..123`：仓库既有实现把它们作为普通二进制记录范围；记录头为 2 字节大端 body 长度，body 首字节为类型。
- `124..127`：位于既有实现的普通记录类型范围之外。仓库只保存了 127 的地图下载实现；124–126 必须整体保持未知。
- `127`：此前逆向实现将其作为地图下载块，格式见下表；本轮缺少原始客户端工件复核。
- `124`、`125`、`126`：当前仓库没有足以裁决长度、字段或语义的 V860 原始字节样本，保持 `UNKNOWN / NEEDS_CAPTURE`。
- 新增 `payload_stream.py`：可解析文本、普通记录和 marker 127；遇到 124–126 时保留全部原始余量并停止，避免伪造边界。
- 本机没有原始 V860 JAR、JAD、PCAP/HAR，也没有可运行的 J2ME 模拟器或 Java 运行时。因此本轮没有生成新的原版客户端首包。

## 解码后混合 payload 语法

| 形式 | 字节结构 | 状态 | 证据等级 |
|---|---|---|---|
| 文本命令 | `<...> 0A` | 现有兼容服务器与测试夹具使用 | `PREVIOUS_REVERSE_ENGINEERING_CLAIM / NEEDS_ARTIFACT` |
| 普通记录 | `len_be16 type payload`，`type <= 123`，`len` 包含 type | 已实现并有自洽测试 | `PREVIOUS_REVERSE_ENGINEERING_CLAIM / NEEDS_ARTIFACT` |
| candidate 124 | 分析器可识别 `00 00 7C ...`，但该前缀本身尚未由原始样本确认 | framing/语义未知；命中后保留余量并停止 | `UNKNOWN / ANALYZER_SENTINEL` |
| candidate 125 | 分析器可识别 `00 00 7D ...`，但该前缀本身尚未由原始样本确认 | framing/语义未知；命中后保留余量并停止 | `UNKNOWN / ANALYZER_SENTINEL` |
| candidate 126 | 分析器可识别 `00 00 7E ...`，但该前缀本身尚未由原始样本确认 | framing/语义未知；命中后保留余量并停止 | `UNKNOWN / ANALYZER_SENTINEL` |
| marker 127 | `00 00 7F key 00 map_len_le16 map_bytes` | 仓库此前实现为地图下载块；key 为 UTF-8/NUL 结尾 | `PREVIOUS_REVERSE_ENGINEERING_CLAIM / NEEDS_ARTIFACT` |

`world_protocol.make_map_download_block()` 是 marker 127 的当前仓库参考编码器。新增解析器只接受这个既有形状。124–126 不套用 marker 127 的长度规则；`00 00 7C` 到 `00 00 7E` 只是防误解析哨兵，不是协议结论。

## 首包与登录序列：证据边界

仓库现有 `tools/smoke_client.py` 使用以下序列驱动兼容服务器：

1. 明文 `CONNECT 1hzg0\n`；
2. 10 字节 bootstrap：`80 5e 78 78 80 6b 61 77 61 0a`，尾部为 `kawa\n`；
3. 首个编码 socket frame 的明文夹具：`new\n860.1HZ0000.NON5800.CT\n`；
4. 服务端返回 `<cid...`、`<newacc>...` 等；
5. 登录凭据帧；
6. 服务端 `<log_suc>`，随后世界/地图记录。

这个顺序来自已知 V860 客户端逆向与既有兼容测试，但仓库没有保存原始客户端侧 PCAP、时间戳、完整十六进制流或模拟器日志。当前分类为：

- 字段/算法：`PREVIOUS_REVERSE_ENGINEERING_CLAIM / NEEDS_ARTIFACT`（见 `hzw_protocol.py`、`server.py`，但本轮缺 JAR hash、类/方法偏移和原始字节）；
- `tools/smoke_client.py` 产生的字节：`REBUILD / TEST_FIXTURE`；
- “已完成真实原版首包抓取”：`NOT_YET_EVIDENCED`。

## Socket 与 HTTP 帧

| 方向 | 已恢复字段 | 状态 |
|---|---|---|
| server → client socket | 4 字节 ACK token + `LE16(payload_len XOR 0xA5A5)` + chained-XOR payload | 兼容实现测试通过；`NEEDS_ARTIFACT` |
| client → server socket | 回显 ACK4 + 经 LCG/ACK0 决定旋转的 16 位长度 + chained-XOR payload | 兼容实现测试通过；`NEEDS_ARTIFACT` |
| server → client HTTP | `LE16(payload_len XOR cid_sum)` + chained-XOR payload | 兼容实现测试通过；`NEEDS_ARTIFACT` |
| client → server HTTP | `LE16(payload_len XOR (cid_sum + sn))` + chained-XOR payload | 兼容实现测试通过；`NEEDS_ARTIFACT` |

## 抓包时必须保存的最小材料

下一次拿到原始 JAR 后，每个机型构建分别保存：

1. JAR SHA-256、Manifest、内部版本串和屏幕尺寸；
2. 模拟器名称/版本、网络代理设置、系统时间；
3. 原始 PCAP/PCAPNG 或代理原始字节日志；
4. 客户端首次启动到登录成功的逐帧方向、时间戳、socket/HTTP 分流；
5. transport 解码后的 payload；
6. `tools/analyze_payload.py` 的 JSON 输出；
7. 124–126 标记前后至少 64 字节，以及该 payload 的完整长度；
8. 对应屏幕录像，建立包事件与 UI 事件的时间对齐。

任何 124–126 的字段命名必须同时有“原始字节 + 客户端解析分支”或两组可控差分样本支持。

## 工具用法

```powershell
python tools/analyze_payload.py decoded-payload.bin --out payload.json
python tools/diff_jars.py E62.jar N73.jar S700.jar --out jar-diff.json
```

这里的 `decoded-payload.bin` 指 transport 层 chained-XOR 解码后的单个服务端 payload；不能直接把 PCAP 全文件交给分析器。

## 待解问题

- 124–126 各自是否带长度、NUL 字符串、压缩数据或跨 payload 状态；
- 这些 marker 是否只出现在地图流，还是也承载战斗/资源/任务数据；
- 不同机型 JAR 是否共用相同 marker 分支；
- HTTP 与 socket 是否共享完全相同的混合 payload 解析器。

在这些问题取得直接样本前，禁止把 124–126 映射为 NPC、任务、战斗或装备记录。
