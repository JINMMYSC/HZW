# V860 地图图案与全游戏图形资产考古 — 2026-09-17

## 目标
从“文字任务/地图拓扑恢复”升级到“像素级视觉资产恢复”。目标不是拿其他《海贼王》游戏素材代替，而是尽可能恢复《海贼王 / 无尽宝藏 / 七海寻缘 / 秘宝传说》自身的历史图形资产。

## 当前可验证视觉源

### A. 琴酒的秘宝传说 — 2021 早期录像
- 2021-02-01 《海贼王之秘宝传说/七海寻缘：风车镇遇草帽小子》 BV1vT4y1P7qF
- 2021-02-03 《海贼王之秘宝传说：翻倒海军基地》 BV1WX4y1N7HE
- 2021-02-04 《海贼王之秘宝传说：基本操作及任务》 BV1Rr4y1K782

分类：VISUAL_REFERENCE。录像明确属于本游戏相关内容，但具体客户端版本仍需与 V860 JAR / V860 UI 特征交叉验证。

这三段应优先逐帧建立：
1. map frame atlas：地图地砖、道路、草地、水面、墙、屋顶、门、洞口、悬崖、港口等；
2. NPC/player atlas：角色四方向/动作帧；
3. monster atlas；
4. UI atlas：HUD、菜单、按钮、选择框、对话框、任务框、状态框；
5. icon atlas：物品、装备、技能、副官、货币、任务图标；
6. effect atlas：战斗、技能、状态、升级等特效；
7. typography：字体、描边、阴影、颜色、字号/像素高度。

### B. 2022 魔窟开箱录像
- BV1J841157Z2 《海贼王之秘宝传说 魔窟礼包5开箱实录》
分类：POST_V860 / VERSION_UNKNOWN。
用途：背包/礼包/物品图标、结果界面、字体和窗口框架参考。不能未经比对直接作为 V860 图形真值。

### C. 现代 JAR 保存库
索爱 K700 176×220 保存目录明确存在：
`海贼王-秘宝传说_索爱 K700系列(176x220).jar`

这与已发现的 QD 176×208、Motorola V8 240×320、128×128、小屏/大屏线索一起，构成多分辨率客户端资产恢复路径。

## 图形资产恢复分类

### 1. 世界地图/场景
对每个已知区域建立：
- background tiles
- collision-looking terrain
- road/path tiles
- water/shore tiles
- building exterior/interior
- doors / portals / stairs
- docks / ships
- cave / dungeon tiles
- snow / forest / grass / cliff / desert-like biome tiles
- interactive world objects：箱子、抽屉、乱石堆、柴堆、飞行箱、宝箱等

优先地图：
遗忘之船、风车镇、海军基地、橘子岛、果汁村、洛克岛、小花园、蝙蝠岛、冬之岛、幽忘岛、巨兽岛、星月/新月岛、鲸鱼岛。

### 2. 角色/NPC
建立 `sprite_id / character / map / direction / frame / dimensions / source_timestamp / confidence`。
不要把动漫或其他海贼王游戏立绘混入本游戏资产。

### 3. 怪物
按地图和任务绑定 sprite：例如巨兽岛 Lv71 巨兽、Lv72 大野猪、Lv73 萝卜怪、Lv74 大巨兽、Lv77 吞噬者等。先建立视觉槽位，具体 sprite 需视频/JAR证据。

### 4. UI
恢复：
- 主 HUD
- 角色状态
- 任务列表/任务提示
- 对话框
- 系统菜单
- 背包
- 装备
- 副官
- 技能
- 商店
- 战斗 HUD
- 海战 HUD
- 聊天
- 地图/传送
- 抽奖/礼包
- 锻造/附魔
- 法宝/坐骑（V860）

注意历史 mod：`去经验框客户端` 证明存在 HUD 修改版，因此截图中缺失经验框不能自动视为官方 V860 UI。

### 5. 全游戏图标
目标图鉴：
- weapons
- armor: head/body/pants/shoes
- ring/necklace
- consumables
- quest items
- gems / enchant items
- crafting materials
- keys
- treasure/chests
- flight cards
- currencies
- deputy portraits/icons
- skills
- status effects
- mounts
- 法宝
- menu/system icons

## 视觉证据等级
- V860_ASSET_DIRECT：从已验证 V860 JAR 解出的原始资源。
- V860_VIDEO_DIRECT：能确认 V860 的录像帧。
- SAME_GAME_VISUAL_REFERENCE：同游戏但版本未确认。
- POST_V860_REFERENCE：后期服视觉，只用于交叉比较。
- TEXT_ONLY：只有文字描述，禁止据此臆造图案。

## 下一阶段：JAR 一旦取得后的自动资产提取
1. unzip JAR；
2. 枚举 PNG/GIF/JPG及无扩展资源；
3. 记录宽高、色深、透明通道、SHA256；
4. 自动生成 contact sheet；
5. 检测 sprite sheet 切片边界；
6. 将重复 SHA 去重；
7. 比较 128×128 / 176×208 / 176×220 / 240×320 各构建资源；
8. 区分共用原图与分辨率专用 UI；
9. 将录像帧与 JAR sprite 做视觉匹配；
10. 输出 `asset_manifest.json` 和地图 tile atlas。

## 当前最重要结论
地图文字拓扑已经可以恢复不少，但“地图长什么样”不能由文字攻略推测。最可靠路线是：早期本游戏录像逐帧 + 历史 JAR 原始 PNG 双线合并。搜索引擎图片结果存在大量《航海王热血航线》等其他游戏污染，必须排除。
