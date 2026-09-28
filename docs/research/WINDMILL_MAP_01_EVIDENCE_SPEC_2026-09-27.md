# 风车镇第一张证据驱动地图规格 — 2026-09-27

> 范围：只固化“遗忘之船 → 路口”这一开场地图节点。当前没有 V860 地图二进制或可量测视频帧，因此本文是可实现的证据规格，不是原版像素地图。

## 证据等级

- 主要来源：游侠手游 2008-04-18《网游海贼王风车镇任务攻略》：https://m.ali213.net/gonglue/080418/14125.html
- 来源直接写明：新手从“遗忘之船”开始，与首个 NPC 对话并选择“明白”；离开遗忘之船到“路口”会触发剧情。
- 分类：`ORIGINAL_DOC + VERSION_DRIFT`。这是同游戏同期资料，但尚未由 V860 JAR、V860 录像或 V860 服务端数据确认布局完全相同。

## 已证实的最小拓扑

```text
遗忘之船
  ├─ 首个教学 NPC：交互 → 对话选择“明白” → 任务完成
  └─ 出口 → 路口
             └─ MAP_ENTER/ZONE_ENTER 自动剧情 → 奖励实战经验
```

## 可进入实现的数据

| 字段 | 当前值 | 等级 |
|---|---|---|
| map id | `windmill_forgotten_ship`（恢复工程内部 ID） | `REBUILD_IDENTIFIER` |
| 原资料地图名 | `遗忘之船` | `ORIGINAL_DOC` |
| 下一节点 | `windmill_crossroad` | `ORIGINAL_DOC`（名称“路口”） |
| 玩家初始位置 | 未知 | `NEEDS_JAR / NEEDS_VIDEO_FRAME` |
| 地图宽高 | 未知 | `NEEDS_JAR` |
| tileset/地砖 | 未知 | `NEEDS_JAR` |
| 碰撞掩码 | 未知 | `NEEDS_JAR` |
| 出口坐标/方向 | 未知 | `NEEDS_JAR / NEEDS_VIDEO_FRAME` |
| 教学 NPC 姓名/造型/坐标 | 未知 | `NEEDS_JAR / NEEDS_VIDEO_FRAME` |
| NPC 交互 | 对话并选择“明白” | `ORIGINAL_DOC` |
| 奖励 | 2008 攻略为 20 实战经验；2007 资料存在 10 点冲突 | `VERSION_DRIFT` |
| 路口触发 | 离船后自动剧情 | `ORIGINAL_DOC` |
| 路口奖励 | 2008 攻略为 50 实战经验 | `ORIGINAL_DOC / VERSION_DRIFT` |

## 禁止填充的内容

以下内容在取得 V860 直接证据前必须保持空值：

- 船体轮廓、甲板材质、海面动画、镜头尺寸；
- 玩家/NPC sprite 编号；
- tile 尺寸、地图格数、出口矩形和碰撞字节；
- 对话逐字文本、字体、颜色、按钮位置；
- 任务 ID、NPC ID、地图 ID 的原服数值；
- 音乐、音效与过图动画。

用现有 `make_tiled_map()` 生成的 24×24 场景只能标为 `REBUILD / PROTOCOL_FIXTURE`，不得命名为“原版遗忘之船”。

## 下一次直接证据的验收条件

只有满足以下任一条件，才能开始还原地图几何：

1. V860 JAR 中找到对应地图资源，并能从客户端解析器证明宽高、tile、层和碰撞字段；
2. 确认 V860 的连续录像足以量测完整边界、入口、NPC 与遮挡；
3. 恢复原服地图 payload 或缓存/RMS，并能用 V860 客户端重放。

取得证据后先把原始 hash、帧号或 payload offset 写入本文件，再修改服务器地图数据。
