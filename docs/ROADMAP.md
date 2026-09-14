# HZW V860 compatibility roadmap

## Milestone A — original client login

- [x] identify V860 / internal version
- [x] recover TCP and HTTP framing
- [x] recover CID/SN/ACK/LCG/XOR state
- [x] implement account creation/login handshake
- [x] implement post-login compatibility menu
- [x] add JAR redirect patcher
- [x] add smoke client and CI
- [ ] verify the real V860 MIDlet renders the post-login menu in an emulator

## Milestone B — enter starting world

- [x] locate main world parser class (`O0OO0O0`)
- [x] locate world commands/tags (`walk`, `npc`, `monster`, `combat`, `intros`)
- [x] recover client map request prefix `#map 60`
- [ ] recover switch-map packet semantics
- [ ] identify Windmill Village starting map key
- [ ] recover player spawn/state payload
- [ ] recover NPC list payload
- [ ] recover movement/position updates
- [ ] persist reconnect position

Definition of done: original V860 logs in, enters its original starting map, shows player/NPC entities and can move.

## Milestone C — playable loop

- NPC dialogue
- quest state
- combat start/end
- skills/items
- monster rewards
- persistence
