from __future__ import annotations

import server as legacy
from chapter_maps import make_chapter_map
from chapter_server import WindmillMarineServer, WindmillMarineWorld
from hzw_protocol import SessionState


class WindmillMarineWorldV2(WindmillMarineWorld):
    """Flow-completion fixes layered on the large two-chapter server."""

    DOORS = dict(WindmillMarineWorld.DOORS)
    DOORS["mb_registry"] = [("副官试练屋", "mb_trial", 12, 8)]

    def _area_map(self, area_id: str) -> bytes:
        if area_id not in self.map_cache:
            self.map_cache[area_id] = make_chapter_map(
                area_id, self.MAP_WIDTH, self.MAP_HEIGHT
            )
            self.cache_key_to_area[self._map_cache_key(area_id)] = area_id
        return self.map_cache[area_id]

    def _auto_script(self, p, event_source: str):
        messages: list[str] = []
        if event_source == "area":
            pending = list(self.AUTO_AREA_ITEMS.get(p.area, []))
            while pending:
                main = self.chapter.current_main(p)
                if not main:
                    break
                q, idx = main["quest"], main["step_index"]
                if idx >= len(q["steps"]):
                    break
                step = q["steps"][idx]
                if step.get("type") != "collect" or step.get("item") not in pending:
                    break
                item = str(step["item"])
                pending.remove(item)
                messages += self.chapter.record_event(
                    p, {"type": "collect", "item": item, "count": 1}
                )
                messages.append(f"取得：{item}")
            self.chapter.save_player(p)
            return messages
        return super()._auto_script(p, event_source)

    def _item_needed(self, p, item: str) -> bool:
        # Quest-critical drops may be needed by the next step after the kill step.
        for qid, idx in p.active_quests.items():
            q = self.chapter.quests.get(qid)
            if not q:
                continue
            for step in q["steps"][int(idx):]:
                if step.get("type") == "collect" and step.get("item") == item:
                    return True
        return False

    def _sync_collect_steps_from_inventory(self, p) -> list[str]:
        messages: list[str] = []
        changed = True
        while changed:
            changed = False
            for qid in list(p.active_quests):
                q = self.chapter.quests.get(qid)
                if not q:
                    continue
                idx = int(p.active_quests[qid])
                if idx >= len(q["steps"]):
                    continue
                step = q["steps"][idx]
                if step.get("type") != "collect":
                    continue
                item = str(step["item"])
                target = int(step.get("count", 1))
                if int(p.inventory.get(item, 0)) < target:
                    continue
                key = self.chapter._counter_key(qid, idx)
                p.counters[key] = target
                p.active_quests[qid] = idx + 1
                if p.active_quests[qid] >= len(q["steps"]):
                    title = q["title"]
                    self.chapter._complete_quest(p, qid)
                    messages.append(f"任务完成：{title}")
                changed = True
        self.chapter.save_player(p)
        return messages

    def _battle_action(self, p, state: SessionState, action: str):
        battle = state.metadata.get("battle")
        if not battle or action not in {"attack", "skill"}:
            return super()._battle_action(p, state, action)

        monster_id = battle["monster"]
        monster = self.chapter.monsters[monster_id]
        base = 14 + p.level * 4
        damage = base + (8 if action == "skill" and p.skills else 0)
        battle["hp"] = max(0, int(battle["hp"]) - damage)
        if battle["hp"] > 0:
            retaliation = max(1, int(monster["atk"]) - p.level)
            p.hp = max(1, p.hp - retaliation)
            self.chapter.save_player(p)
            return [
                f"<pmg>你造成 {damage} 点伤害。\x1a{monster['name']}剩余 {battle['hp']} 生命。\x1a你受到 {retaliation} 点伤害。",
                "<menu(g:a)>战斗指令|[battle attack]普通攻击|[battle skill]战斗技能|[battle item]使用物品|[battle flee]逃跑",
            ]

        state.metadata.pop("battle", None)
        lines = [f"击败了{monster['name']}。"]
        p.exp += int(monster.get("exp", 0))

        # Advance the kill step first. A following collect step is then visible to
        # the drop resolver (e.g. 特效药、印章、犯人名单、监狱钥匙).
        lines += self.chapter.record_event(
            p, {"type": "kill", "monster": monster_id, "count": 1}
        )
        for item, chance in (monster.get("drops") or {}).items():
            if float(chance) >= 1.0 or self._item_needed(p, item):
                p.give_item(item, 1)
                lines.append(f"获得：{item}")
        lines += self._sync_collect_steps_from_inventory(p)
        self.chapter._recalculate_level(p)
        self.chapter.save_player(p)
        return ["<pmg>" + "\x1a".join(lines)]


class WindmillMarineServerV2(WindmillMarineServer):
    def __init__(self, host: str, tcp_port: int, http_port: int, data_dir):
        super().__init__(host, tcp_port, http_port, data_dir)
        self.world = WindmillMarineWorldV2(data_dir)


legacy.HZWCompatServer = WindmillMarineServerV2

if __name__ == "__main__":
    legacy.main()
