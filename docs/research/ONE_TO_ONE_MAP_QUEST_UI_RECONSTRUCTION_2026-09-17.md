# 《海贼王 / 秘宝传说》地图、任务进度跳转、操作界面一比一恢复证据（2026-09-17）

## 目标

本文件把恢复标准从“地图名/任务名存在”提高到可实现的一比一状态机：

1. 每张地图的入口/出口、相邻地图、室内外层级、关键物件、NPC、怪物区；
2. 任务接取、进行中、交付、等级门槛、等待门槛、世界物件、自动剧情、强制战斗、自动跳图；
3. 游戏操作界面：任务查看、地图查看、飞行、NPC交互、对话、菜单、战斗、背包/任务道具等；
4. 所有未知坐标/像素/UI尺寸继续标 NEEDS_VIDEO_FRAME 或 NEEDS_JAR，不凭文字攻略脑补。

---

## 1. 海军基地：任务状态机 + 地图交互链

同期攻略（2008-01-16）给出了极强的连续流程证据。

### 进入触发

`风车岛 --军舰航行--> 海军基地`

进入海军基地立即自动剧情：玩家看到无耻之徒抢药剂师的小刀和钱财。

继续“向上”进入基地中心区，进入酒吧再次自动剧情：无耻之徒抢酒保，刀客进入并将其杀死。

这说明地图引擎至少需要：

- MapEnterTrigger
- DirectionalExit / north transition
- InteriorEntrance
- CutsceneTrigger
- NPC scripted movement/dialogue/death-state

### 支线/主流程状态

#### 奇怪的酒保
酒保 → 挑战海军哨岗员 → 击败 → 返回酒保 → 获得基地内幕 → 指向副官登记处马克。

#### 海军的考验
马克连续发出三段考验：

1. 力量：去“出门向上的一副地图”击败亨利 → 返回马克；
2. 智慧：取得信 → 酒吧 → 加西亚 → 对话；
3. 忠诚：返回马克 → 获得设计图 → 药剂师 → 返回马克 → 转向餐馆老板娘。

必须支持同一 QuestChain 内多 stage，而不是把三项考验实现成互不相关任务。

#### 愤怒的人民
老板娘 → 监狱 → 战斗海军两次 → 找到老板 → 返回老板娘 → 基地中心城索伦斯。

#### 索伦斯的烦恼
索伦斯不信任玩家 → 返回老板娘取得“帽子”信物 → 交索伦斯 → 索伦斯因女儿事件不能立即协助 → 返回老板娘。

#### 水落石出
老板娘 → 海军操练场 → 杀海军取得特效药 → 索伦斯 → 救刀客索络 → 返回索伦斯 → 得知摩根通信 → 下一阶段。

#### 不为人知的信
海军总部柜子（世界物件）→ 偷信 → 教堂莱瑞 → 伪造信 → 缺印章 → 废滩区击杀汤姆 → 印章 → 伪造信盖章 → 废滩区信使 → 返回酒吧老板娘。

这里要求完整的：
`WorldObject(Cabinet) -> Item(letter) -> NPC -> Item(fake_letter) -> KillDrop(seal) -> ItemCombine/QuestTransform -> NPC messenger`

#### 里应外合
老板娘 → 获取犯人名单目标 → 击杀监狱长取得名单 → 监狱老板 → 获取钥匙目标 → 广场海军宿舍击杀剑圣巡逻官 → 钥匙 → 交老板 → 放出村民 → 自动剧情 → 监狱爆炸/老板牺牲 → 触发下一岛主线。

这是非常重要的 `QuestCompletion -> WorldStateMutation -> Cutscene -> NextRegionUnlock` 证据。

地图节点至少包括：
- 海军基地入口
- 基地中心区
- 酒吧
- 副官登记处
- 餐馆
- 监狱
- 基地中心城
- 海军操练场
- 海军总部
- 教堂
- 废滩区
- 广场
- 海军宿舍

精确几何/Tile/坐标：NEEDS_VIDEO_FRAME / NEEDS_JAR。

来源：https://m.ali213.net/gonglue/080116/14340.html

---

## 2. 橘子岛：完整16阶段主线与地图物件操作

同期攻略保留了极细的任务跳转。

地图节点至少包括：
- 沙滩
- 橘子村
- 村长家
- 灯塔
- 村诊所/诊所房间
- 宠物店/宠物店房间
- 酒窖
- 村北路
- 仓库
- 山湖
- 乱石岗
- 橘子山
- 贸易港口
- 民房
- 杂货店
- 兽王石后面山洞
- 山泉
- 空宅
- 山顶
- 储物室

关键状态门槛：
- 藏宝图的下落：Lv11；
- 海贼真相一：前置后等待1小时；
- 血债二完成后：达到Lv12才转宠物店；
- 山顶最终宝箱：Lv15才能打开。

关键世界物件：
- 贸易港口柴堆 → 柴刀；
- 民房针线包 → 绣花针；
- 杂货店购买放大镜；
- 橘子山乱石堆 → 特大石头；
- 橘子村箱子 → 绳子；
- 贸易港口柴堆 → 木根 → 橘子山火堆 → 火把；
- 储物室墙角 → 铁铲；
- 山顶 → 尸骨；
- 山泉墓碑 → 埋葬；
- 山顶宝箱 Lv15 → 5000银 + 兽王剑。

尤其“蜘蛛巢穴”出现玩家选择：选择进入后才得到后续奖励，说明任务对话/交互存在 branch choice。

恢复时需实现：
`QuestStage + LevelGate + TimeGate + WorldObjectSearch + ShopItem + ItemUse + ItemTransform + ChoiceBranch + TreasureLevelGate`。

来源：https://m.ali213.net/gonglue/071224/14387.html

---

## 3. 星月岛/新月岛：任务界面→地图界面→飞行跳图的直接证据

2008-09-10攻略原意明确：

- 到小花园中心找“星月岛导游”接任务；
- 提示使用飞行卡前往“新月岛码头”；
- 玩家执行“查看任务”；
- 再“察看地图”；
- 从地图执行飞行；
- 到达后沿路找到人皇；
- 初始交付奖励 2700经验 / 700银；
- 随后进入15步主线。

这对一比一恢复UI非常关键，因为它证明飞行不是简单快捷键瞬移，而至少存在：

`Quest UI -> Map UI -> destination selection -> consume/require flight card -> map transition`

需要从琴酒录像/JAR继续确认：
- “查看任务”入口位置；
- 任务列表布局；
- 当前任务详情字段；
- “察看地图”按钮/菜单层级；
- 地图节点的图形样式；
- 可飞/不可飞状态表现；
- 飞行卡数量显示；
- 确认框；
- 加载/跳图画面。

来源：https://m.ali213.net/gonglue/080910/13748.html

---

## 4. 幽忘岛：等级与地图链补证

2008-09-27索引保存：
- Lv68+；
- 从冬之岛海路进入幽忘岛；
- 登陆东海岸找波特林接主线；
- 鲜果林击杀/采集妖花（Lv70）相关果子10个；
- 下一阶段去北面瀑布温泉找乔治；
- 到达瀑布温泉会“出现剧情”后再与乔治对话。

这再次证明：
`SeaRoute -> RegionEntry -> NPCQuest -> Kill/Collect -> DestinationHint -> MapEnterCutscene -> NPCInteract`

来源：https://m.ali213.net/gonglue/index_1777.html

---

## 5. 巨兽岛：跨岛解锁、进入剧情、强制战斗

已确认：
- 接取条件 Lv70 + 完成幽忘岛主线；
- 幽忘岛东海岸波特林 → 送信；
- 巨兽岛海域 → 巨兽岛外海 → 巨兽岛码头；
- 摩斯交信 → 指向中心广场乔特；
- 进入“小镇通路”自动出现剧情并击杀Lv71巨兽；
- 然后才进入广场继续主线。

实现上应是：
`PrerequisiteQuest + LevelGate -> SeaMap transitions -> Dock -> NPC -> EnterMapTrigger -> ForcedBattle -> UnlockExit/ContinueQuest`

来源：https://m.ali213.net/gonglue/081027/13616.html

---

## 6. 任务完成会影响“能否飞行”

2007玩家攻略明确提到：主线没做可能“不可以飞去”；果汁岛方面又提到做主线后可以飞去，并有玩家讨论是否只要进入过地图就能飞。

因此 FlightPoint 解锁规则必须独立建模，不能默认所有地图从开始即可瞬移。

候选状态字段：

```text
MapDiscoveryState
- neverVisited
- visited
- flightUnlocked
- questUnlocked

FlightPoint
- mapId
- unlockQuestId?
- unlockOnVisit?
- requiredItem = flightCard
```

“进入即解锁”与“完成主线才解锁”的版本差异继续 NEEDS_JAR / NEEDS_VIDEO 验证。

来源：https://m.ali213.net/gonglue/071207/14442.html

---

## 7. 琴酒录像：UI一比一恢复的主要视觉证据

2021-02-04《海贼王之秘宝传说：基本操作及任务》公开页面同时关联：
- 《风车镇遇草帽小子》12:23；
- 《翻倒海军基地》24:12；
- 《新人保姆级教学解说》09:28；
- 以及其他同游戏录像。

这组三段应作为 UI/地图帧恢复的第一视觉母本，逐帧建立：

### HUD
- 地图场景可视区域
- 玩家状态区域
- EXP区域（注意历史“去经验框客户端”污染）
- 软键标签
- 当前提示/系统信息

### 对话
- 对话框外框
- NPC名字位置
- 文本字号/行距/换行
- 确认/下一页方式
- 选项列表高亮样式

### 任务
- NPC任务标识（同期资料已知感叹号）
- 任务列表
- 任务详情
- 完成/未完成视觉状态
- 目标数量更新
- 交付后的奖励提示
- 下一目标提示

### 地图
- 地图选择页
- 当前地图名称
- 飞行点
- 可达/锁定状态
- 地图间加载/跳转

### 战斗
- 玩家/副官/敌方站位
- HP/MP
- 技能选择
- 目标选择
- 回合提示
- 伤害数字
- 状态效果
- 战斗结算

### 系统菜单
- 人物信息
- 周围玩家
- 周围NPC
- 聊天
- 系统指令/设置
- 名字显示切换
- 聊天记录

页面：https://www.bilibili.com/video/BV1Rr4y1K782/

所有像素尺寸、颜色、sprite坐标仍需真实视频帧/JAR，不从文字猜。

---

## 8. 一比一恢复数据模型

每张地图建议最终产出一个独立 `MapSpec`：

```text
MapSpec
  id
  canonicalName
  aliases[]
  versionEvidence
  visualEvidenceFrames[]
  dimensions
  tileSize
  tileLayers[]
  collisionMask
  entrances[]
  exits[]
  interiors[]
  npcs[]
  monsters[]
  worldObjects[]
  treasure[]
  cutsceneTriggers[]
  battleTriggers[]
  flightPoint
  music/sfx (if recovered)
```

任务必须用真正状态机：

```text
Quest
  prerequisites
  minLevel
  cooldown/wait
  stages[]

QuestStage
  trigger
  objective
  targetMap
  targetNpc
  targetMonster
  targetWorldObject
  requiredItems
  consumeItems
  grantItems
  dialogue
  cutscene
  forcedBattle
  mapTransition
  reward
  nextStage
```

UI另外建立 `UIScreenSpec`，不要把逻辑写死在地图里。

---

## 9. 恢复纪律

达到“一比一”必须把证据层级锁死：

1. V860 JAR资源/代码字符串：最高；
2. 确认V860实录：最高视觉证据；
3. 同游戏同期攻略：任务/拓扑高价值；
4. 同游戏未知版本录像：用于候选视觉，不直接定版；
5. 后期复活服：只做交叉参考；
6. 其他《海贼王》游戏：禁止作为视觉恢复依据。

任何地图没有真实画面时，只恢复“已证实拓扑和逻辑”，不臆造地砖、坐标、建筑样式。

## 下一阶段

- 逐岛建立 `MapSpec`：风车镇 → 海军基地 → 洛克岛 → 橘子岛 → 果汁村 → 小花园 → 星/月岛 → 蝙蝠岛 → 冬之岛 → 幽忘岛 → 巨兽岛。
- 对琴酒早期录像逐秒建立 `Frame Evidence Index`。
- JAR一旦获得，枚举 PNG/GIF、sprite sheet、地图块、字体、菜单皮肤、图标和字符串，反向映射到 MapSpec/UIScreenSpec。
- 对每个任务建立 `Quest Transition Table`，记录 stage、触发方式、地图、NPC/物件、奖励、下一跳。
