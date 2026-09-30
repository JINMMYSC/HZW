# V860 候选 JAR 入库验真流程 — 2026-09-30

## 本轮结果

- 新增机器可读候选清单：`v860_jar_candidates.json`。
- 新增 `jar_intake.py` 与 `tools/intake_jar.py`，用于候选 JAR 到手后的第一轮固定取证。
- 公开论坛页面再次确认 K700、Motorola V8、Nokia QD 三个实体文件名，但下载地址位于登录/回复可见区，本轮没有取得文件。
- Internet Archive CDX 在当前网络环境中无法连接；DOSPY 实时页仍返回数据库错误。

## 证据升级规则

扫描器只在同一个 JAR 自身同时满足以下两项时输出：

`V860_DIRECT_BINARY_MATCH`

条件：

1. Manifest 包含 `MIDlet-Version: 8.60.0`；
2. JAR 条目字节中包含精确内部串 `860.1HZ0000.NON5800.CT`。

只有其中一项时仍保持 `JAR_CANDIDATE`。发现 Manifest 版本冲突或其他内部版本串时标记 `VERSION_DRIFT`。文件名、网页标题、机型相似和体积接近都不能单独升级证据等级。

## 入库命令

```bash
python tools/intake_jar.py HZW_E62.jar \
  --out evidence/HZW_E62.intake.json \
  --source-url "https://来源页" \
  --claimed-device "Nokia E62 320x240"
```

报告固定记录：

- 文件名、绝对路径、字节数和 SHA-256；
- 完整 Manifest 字段；
- 内部版本串候选；
- 明文 HTTP/HTTPS/socket 端点；
- class 与资源数量；
- 来源 URL、声称机型和明确的分类规则。

完成单包验真后，再对两个以上样本运行：

```bash
python tools/diff_jars.py HZW_E62.jar HZW_N73D.jar HZW_S700.jar \
  --out evidence/v860-device-diff.json
```

## 当前候选优先级

1. DOSPY E62：文件名/体积与 QJTYW `HZW_E62 (jar/374)` 最接近，仍需实体字节验证。
2. DOSPY N73：可与 QJTYW `HZW_N73D` 机型线交叉检查。
3. 全机种 K700 与 Motorola V8：分别对应 QJTYW `ZW_K700` 与 `HZW_MOTOV8` 标签，但现代合集可能发生版本漂移。
4. 其余 DOSPY/全机种候选：先保持 `VERSION_DRIFT_JAR_CANDIDATE`。

## 尚未取得

- 原版或候选 JAR 实体；
- 原版 V860 首包；
- marker 124–126 的可定位 payload；
- 风车镇地图原始数据和几何。

因此本轮没有修改协议含义、首包字段或地图实现。
