# Map / quest / reward data archaeology — 2026-09-17

Scope: contemporary 2007–2008 materials for 随手互动《海贼王/无尽宝藏》. This batch focuses on map topology, quest chain, quest prerequisites and exact progression/reward values. These are contemporary-era data, not automatically V860-direct; preserve separately until V860/JAR corroboration.

## 1. 风车镇 / 遗忘之船 early progression

Source: https://m.ali213.net/gonglue/080418/14125.html (2008-04-18)

Confirmed sequence and rewards:

- 遗忘之船 tutorial dialogue: +20 实战经验.
- Leave ship / road entrance story trigger: +50 实战经验; guide states this raises player to Lv2.
- 西尔 magic experiment: +20 银币.
- deliver love letter to 雅雅 at 广场: +10 实战经验 and receive a hammer.
- house NPC asks player to buy ink from southwest shop: +15 实战经验, +10 银币, +1 短裤. Nearby chest: 35 银币.
- 路飞 story: +80 实战经验.
- 村长 -> 后山 -> 自画王 obtain 航海图 -> return: +60 实战经验.
- next 路飞 story: +100 实战经验; guide states Lv4.
- 后山山洞 upper-right treasure requires the previously obtained hammer; reward: 航海日记 +100 银币 +15 实战经验.
- hand money to 木匠: +150 实战经验.
- recover two axes from 斧头帮 area: +80 实战经验 +10 银币 +2捆木头 +草鞋.
- return wood to 路飞: +200 实战经验; 神庙/神帆 story for sail: +300 实战经验 and automatic map teleport out of temple.
- 悬崖 / 海特团长: free ship + 新手炮; learn level-1 gunnery from captain; nearby quest reward +30 银币 +70 实战经验; guide states Lv6.
- 东港口 / 路飞: obtain 通缉手册 +300 实战经验, then talk to NPC below to sail out.

Engineering implications:

- early quest EXP is explicitly `实战经验`; later guides use `陆战经验`, so preserve reward type as a field rather than normalizing blindly.
- quest system needs `ENTER_MAP_STORY`, `DIALOGUE`, `FETCH_ITEM`, `KILL_DROP`, `INTERACT_OBJECT`, `AUTO_TELEPORT`.
- hammer is a persistent quest/tool item reused to unlock a cave treasure.
- ship acquisition and gunnery skill are part of the early main progression.

## 2. 橘子岛 main chain / timed gate / tool interactions

Source: https://m.ali213.net/gonglue/071224/14387.html (2007-12-24)

Confirmed maps/places include 沙滩, 橘子村, 村长家, 灯塔, 村西北诊所, 宠物店, 酒窖, 村北路, 仓库, 山湖, 乱石岗, 橘子山, 贸易港口, 民房.

Main progression excerpt:

1. `藏宝图的下落`: requires Lv11; village chief dialogue; 160 EXP / 150 silver / 5 reputation.
2. `人质之小岛末日`: go toward southeast lighthouse for goat; 180 EXP / 190 silver / 5 rep.
3. `人质之海贼真相一`: explicit **1-hour wait gate** before acceptance; clinic -> lighthouse -> pirate leader; 210 EXP / 200 silver / 5 rep.
4. `人质之海贼真相二`: 200 EXP / 210 silver / 5 rep.
5. `人质之血债一`: lighthouse south, kill pirate/drop objective; 430 EXP / 300 silver / 5 rep.
6. `人质之血债二`: kill pirate leader, obtain head, return to clinic; 450 EXP / 490 silver / **20 rep**; then Lv12 gate to pet shop.
7. `宠物情之休休`: 酒窖, fight 驯兽师魔吉; 480 EXP / 500 silver / 5 rep.
8. `宠物情之求医一`: 村北路兽医 -> 仓库, collect medical equipment; 340 EXP / 350 silver / 5 rep.
9. `宠物情之求医二`: 山湖, collect 3 青水苗; 350 EXP / 440 silver / 5 rep.
10. `宠物情之宝藏`: 270 EXP / 260 silver / 5 rep.
11. `宠物情之谎言`: 270 EXP / 260 silver / **20 rep** + 字条.
12. `宝藏之解密`: 字条 -> 化石 -> 村长; 170 EXP / 200 silver / 5 rep.
13. `宝藏之寻找兽王`: requires 柴刀 from 贸易港口柴堆 and 绣花针 from 民房针线包; 400 EXP / 220 silver / 5 rep.
14. `宝藏之入口`: requires 放大镜 purchased at 杂货店 and 特大石头 from 橘子山乱石堆; 200 EXP / 220 silver / 5 rep.

Engineering: quest prerequisite schema must support `minLevel`, `waitAfterPreviousSeconds`, `requiredItems`, `worldObjectItemSource`, and nonuniform reputation rewards.

## 3. 洛克岛 main chain

Source: https://m.ali213.net/gonglue/080123/14318.html (2008-01-23)

Maps/NPC nodes include 导游小姐, 洛克西南海军驻地, 旧屋, 道具屋, 广场/刑台, 烟馆, 洛克南镇赌场, 灯塔, 迷人酒吧, 老式仓库, 长官室, 峰人医院/特护病房.

Exact chain data:

- main 1 dialogue: 300 EXP / 300 silver / 4 rep.
- main 2 kill gate guard, obtain key, enter base/find 哈多: 400 / 480 / 5.
- main 3 kill garrison, obtain 2 uniforms, then **wait 5 minutes** before old-house meeting: 320 / 520 / 5.
- main 4 buy telescope: 500 / 500 / 5.
- main 5 stand on execution platform then return: source text contains likely typo `300经验400经验5声望`; preserve raw value pending cross-check.
- main 6 casino 塔丝琪 -> lighthouse kill marine for glass plate: 370 / 540 / 5.
- main 7 letter round trip 塔丝琪 <-> 斯摩格: 250 / 300 / 5.
- main 8 climb tree beside 迷人酒吧 -> rescue 塔丝琪 in old warehouse -> masked enemy: 320 / 370 / 4.
- main 9 长官室 卡特 -> 烟馆: 230 / 250 / 5.
- main 10 hospital special ward / black-clothed enemy: 380 / 420 / 5.
- main 11 **requires Lv26**, old warehouse smugglers, collect 5 weapon crates: **30 飞行符 +600 EXP +900 silver +5 rep**.

## 4. 冬之岛 complete nine-step mainline and map graph

Source: https://m.ali213.net/gonglue/080909/13753.html (2008-09-09)

Entry: from 蝙蝠岛外海 travel left; requires Lv62+.

Map/NPC/object graph recovered:

`蝙蝠岛外海 -> 冬之岛 -> 大号角 -> 冬岛小镇 -> 杰克斯家 -> 小雪山 -> 库蕾哈家 -> 寒极山 -> 小酒馆 -> 服装店 -> 幽灵滩 -> 大雪山 -> 山顶豪宅/豪宅卧室 -> 千冰湖 -> 雪峰`

Mainline rewards:

1. 保罗 / 小美露 / 烧兔子: 3536 陆战EXP / 1367 silver / 5 rep.
2. 杰克斯/波力 dialogue: 3536 / 1367 / 5.
3. 多尔顿: 5 偷猎者帽子 then 10 猎枪: 12476 / 9339 / 5.
4. 库蕾哈: 5 fresh rabbit meat + buy 八角盘: 8444 / 4783 / 5.
5. black pill -> 波力 -> 米杰: 3536 / 1367 / 5.
6. 幽灵滩娃娃花 10 petals + 大雪山 5 mushrooms: 11588 / 8200 / 5.
7. deliver medicine: 2537 / 911 / 5.
8. 豪宅卧室 drawer object -> box; 千冰湖蛤蟆怪 -> key: 8492 / 4783 / 5.
9. 雪峰 bottle: 3536 / 1367 / 5.

This is unusually strong restoration data: map path + NPC + item counts + exact rewards for every numbered main quest.

## 5. 星月岛 / 新月岛 full 15-step reward chain

Source: https://m.ali213.net/gonglue/080910/13748.html (2008-09-10)

Entry: 小花园中心 `星月岛导游` -> use flight card to `新月岛码头` -> 人皇. Entry handoff reward 2700 EXP / 700 silver.

Recovered nodes: 人皇, 莲华屋, 档案室, 镇东骑士营地, 炼金屋, 四季迷宫(春石/夏石/秋石/冬石), 地下城, 东方洞窟, 勇者地狱, 西方区域, 镇东战桥.

Rewards/objectives:

1. kill 10 giant bats: 3439 EXP / 2785 silver.
2. find 莲华: 785 / 371.
3. kill 仲裁者 for 生死报告: 1761 / 941.
4. collect 5 maps at knight camp: 4499 / 3762.
5. obtain secret medicine from 神权言者: 2063 / 941.
6. Four Seasons Maze checkpoints: 夏 900/376, 秋 900/376, 冬 900/376; hidden chest in underground city 2000/750.
7. underground-city resident / city lord: 840/376.
8. `拯救行动`: kill 10 knights in eastern cave: source records **38953 EXP / 2585 silver**. This unusually high EXP should be preserved raw and flagged for typo/version verification.
9. `勇者的天空`: use 成人杂志 on hero: 1798 / 762.
10. `阻止战争`: kill 10 warriors: 4238 / 2895.
11. `事实背后`: kill chief of staff: 2986 / 1351.
12. `痛苦时间`: 人皇 -> 莲华: 2059 / 885.
13. `独挡大军`: kill 10 marines at battle bridge: 4544 / 3671.
14. `莲华羽化`: battle-bridge story then return: 3930 / 1798.
15. `再见莲华`: obtain 银色星月 -> 人王: 5000 / 2000.

## 6. 幽忘岛 recovered entry/topology fragment

Source index: https://m.ali213.net/gonglue/index_1777.html (article dated 2008-09-27)

- requires Lv68+.
- enter by sea from 冬之岛.
- land at 幽忘岛东海岸, find 波特林.
- first objective: 鲜果林, collect 10 fruits from Lv70 妖花; reward indexed as 6428 silver +5 rep (EXP not visible in index excerpt).
- next: 北面瀑布温泉 -> 乔治; reward 2472 silver +5 rep.
- index indicates main quest 3 continues west to herb collection; full article still needs direct recovery.

## 7. 巨兽岛 detailed topology / quest gates / mixed battle EXP

Source: https://m.ali213.net/gonglue/081027/13616.html (2008-10-27)

Prerequisites: Lv70 + completion of 幽忘岛 mainline.

Recovered map graph:

`幽忘岛东海岸 -> 巨兽岛海域 -> 巨兽岛外海 -> 巨兽岛码头 -> 小镇通路 -> 中心广场 -> 平衡高地 -> 镇长家 -> 绝望高原 -> 长老家 -> 杂货店 -> 奇迹森林 -> 月光岩 -> 药草涧 -> 薰衣草原 -> 地下泉眼 -> 秘钥洞穴 -> 巨兽宝藏/里间`

Enemy levels explicitly present: 小镇通路 forced 巨兽 Lv71; 奇迹森林 大野猪 Lv72; 药草涧 萝卜怪 Lv73; 平衡高地 大巨兽 Lv74; 吞噬者 Lv77.

Important progression facts:

- entering 小镇通路 triggers story + forced Lv71 battle.
- main 2: kill 10 巨兽 at 绝望高原; 2000 silver +5 rep.
- collect 10 野猪肉 -> obtain 《贤者之书》.
- recover missing page 99 via 雷伊/梅丽雅 apple delivery.
- 月光岩 -> 月光石.
- use 月光镜 in 药草涧, story trigger + kill Lv77 吞噬者 -> 友善之草.
- collect 5 carrots from Lv73 萝卜怪.
- 薰衣草原 collect 1 lavender; reward includes 香袋.
- 地下泉眼 `勇气宝箱`: **10000 陆战EXP +1000 海战EXP**, direct proof of a single world object awarding both separate EXP pools.
- 秘钥洞穴: use 机关石 -> half treasure key.
- **Lv73 gate**: only then obtain full treasure key from 法尔 and enter 巨兽宝藏.
- final treasure inner room triggers story and battle with 小丑船长 + two others; final listed reward 5000 silver +5 rep.
- guide explicitly states some quest EXP was invisible because the player was at level cap; missing EXP must therefore remain null, not reconstructed as zero.

## 8. Repeatable quest / leveling progression data

Source: https://m.ali213.net/gonglue/071207/14442.html (2007-12-07)

Contemporary player leveling route records:

- 橘子岛 `浪子` and 黑色沼泽外 tasks: 24-hour repeatable.
- Lv20: join marine or pirate faction; faction-area tasks also 24-hour repeatable.
- Lv19: 橘子山泉 `孤墓` task yields 2929 money (currency wording in source; exact unit needs verification).
- Lv26+: 果汁岛 has 3-hour repeatable quest.
- leveling route: Lv7–15 大望; Lv15–20 Lv13 海军宿舍; Lv20–24 悬崖; Lv25+ 风铃湖 solo; Lv30+ party with doctor.
- guide notes unfinished mainline can block flight access to areas.

Source: https://m.ali213.net/gonglue/080123/14319.html

果汁村 exact repeatables include:

- `做果汁`: 2 bananas +2 coconuts; 250 EXP /450 silver; every 3 hours.
- `胡萝卜汁`: kill 10 铁爪鼠; 300 EXP /540 silver; every 3 hours.
- `整顿治安`: kill 5 布贩子 then 5 皮革贩子; 500 silver; guide says can be repeated indefinitely.

## Restoration schema recommendation

Do not encode these as narrative-only scripts. Suggested records:

```text
MapNode(id, displayName, parentRegion, minLevel, entrances[], exits[])
Quest(id, name, type, giverNpc, turnInNpc, minLevel, prerequisiteQuestIds[], cooldownSeconds, waitAfterPreviousSeconds)
QuestObjective(type, mapId, npcId, monsterId, itemId, count, objectId, triggerId)
QuestReward(landExp, seaExp, practicalExp, silver, reputation, items[])
WorldObject(id, mapId, requiredItemId, consumeItem, rewardItems[], rewardExp[], trigger)
StoryTrigger(mapId, condition, forcedBattleId, teleportTarget)
```

Critical distinction: preserve `实战经验`, `陆战经验`, `海战经验` separately until binary/server evidence proves equivalence or conversion rules.

## Data-quality flags

- `CONTEMPORARY_CONFIRMED`: 2007–2008 pages are direct contemporary descriptions, but not yet proven unchanged in V860.
- `RAW_TYPO_SUSPECT`: 洛克 main 5 reward; 星月 main 8 38953 EXP; do not silently correct.
- `MISSING_DUE_LEVEL_CAP`: 巨兽岛 omitted EXP values are unknown, not zero.
- `NAME_CONFLICT`: 星月岛 / 新月岛 remains unresolved hierarchy/naming evidence.
