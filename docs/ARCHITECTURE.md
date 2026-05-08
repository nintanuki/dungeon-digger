# Dungeon Digger — Architecture

This document explains **how the Dungeon Digger code is put together and why**. It is meant for anyone touching the code — human or AI. It deliberately skips things any Pygame project does and focuses on the parts specific to this game.

> **Maintenance rule:** every pass that meaningfully changes a system must update the matching section here. Out-of-date architecture docs are worse than none.

---

## 1. The shape of the program

```
                              +----------------+
                              |   main.py      |
                              |  GameManager   |   (coordinator)
                              +-------+--------+
                                      |
   +----------+-----------+-----------+-----------+-----------+----------+
   |          |           |           |           |           |          |
   v          v           v           v           v           v          v
DungeonLevel  Player    Monsters  AudioManager  SaveManager  Score-    Render
 (core/)     (core/    (core/    (systems/)    (systems/)   Leader-   Manager
              sprites)  sprites)                            board     (ui/)
                                              Intermission  Manager
                                              Flow (systems)
                                              LevelLoader (core/)
                                              TutorialManager (core/)
   +-----------------------------------------------------------------+
   | UI windows: MessageLog, InventoryWindow, MapWindow (ui/windows) |
   | CRT post-process (ui/crt.py)                                    |
   +-----------------------------------------------------------------+
```

Responsibility split:

- **`GameManager`** owns the screen, clock, controllers, the active level, the sprite groups, and the persistent state (score, leaderboard, save slot identity). It dispatches input and orchestrates phase transitions but does not implement them.
- **`DungeonLevel`** owns the tile grid for the current dungeon — what's wall, what's dug, what's loot — and does line-of-sight queries.
- **`Player` / `Monster`** are `pygame.sprite.Sprite`s with their own input/AI, animation, and inventory state.
- **`AudioManager`** owns mixer state and music switching.
- **`SaveManager`** reads/writes JSON save slots under `saves/`.
- **`ScoreLeaderboardManager`** owns score, high score, leaderboard persistence, and the win-screen initials flow.
- **`IntermissionFlow`** orchestrates the between-levels sequence: door unlock → treasure conversion → auto-save → shop → next level.
- **`LevelLoader`** wires up a freshly built `DungeonLevel` (player spawn, monster spawn, NPC placement, loot scattering).
- **`TutorialManager`** drives the optional first-run tutorial cards.

---

## 2. The frame loop

`GameManager.run()`:

1. Check the controller quit combo (top of frame, for held-state quits).
2. `_process_events` drains `pygame.event.get()` and dispatches by event type and current `ui_state` (title, slot select, name entry, gameplay, shop, game over, etc.).
3. `_update` advances per-frame state — sprite animation, idle peek timing, fog-of-war recompute when needed, intermission timing.
4. `_render_frame` paints background → world tiles → sprites → fog of war → HUD (score, level, dungeon name) → log/inventory/map windows → modal overlays (shop, dialog, transition cards) → CRT.
5. `pygame.display.flip()` then `clock.tick(FPS)` cap the framerate.

Gameplay itself is **turn-based** even though the loop is real-time. A turn advances when the player issues a "moving" or "acting" intent that the rules accept; monsters then take their turns; rendering is continuous in between so animation can play out.

---

## 3. The world model

### Dungeon level
A level is a 14 × 10 grid of tiles (`UISettings.COLS × UISettings.ROWS`) sized to fit exactly inside the action window. Each tile is one of: dirt (undug, blocking), dug (passable floor), wall (permanent), door, key, loot, etc. `core/dungeon.py` owns this grid and answers questions like `is_wall`, `is_dug`, `get_line_points` (Bresenham line-of-sight), and what loot/items are at a tile.

### Configurable progression
`core/dungeon_config.py` declares `DUNGEON_CONFIG` and `LEVEL_DUNGEON_ORDER`: which dungeon (themed level) appears in which slot, and the difficulty parameters per level number. `LevelLoader` reads these to build the next `DungeonLevel`.

### Tilemaps
`core/tilemaps.py` holds the static layouts available to each dungeon, plus the rules for stamping random loot.

---

## 4. The player

[`Player`](../core/sprites.py) tracks position, inventory, status effects, light state, and animation.

### Sprite variants
The player has 10 sprite assets keyed by `(helmet_state, facing, peek)`:

| helmet_state | meaning |
| --- | --- |
| `up` | normal |
| `down` | cloak / repelled visual |
| `off` | reserved (currently unused) |

| facing | meaning |
| --- | --- |
| `left` / `right` | last horizontal move direction |

| peek | meaning |
| --- | --- |
| `center` | neutral |
| `left` / `right` | idle "look around" frames (only with helmet `up`) |

All variants are loaded once in `__init__` so per-frame swaps are dict lookups, not disk I/O. Helmet state is derived from active status effects; facing is updated on horizontal movement; peek is driven by the idle animation.

### Idle "peek" animation
While the player stands still with helmet up:
1. After `PlayerSettings.IDLE_ANIMATION_DELAY_MS` of inactivity, the peek cycle starts.
2. Each frame in `IDLE_ANIMATION_SEQUENCE` (`center → left → center → right → center`) is held for `IDLE_ANIMATION_FRAME_MS`.
3. Movement, vertical movement, or any non-`up` helmet state cancels and resets the cycle.

Real-time deltas are computed inside `update_idle_animation` from `pygame.time.get_ticks()` so timing is independent of FPS variance.

### Movement animation
Although gameplay is grid-stepped, the visual is interpolated: when a turn issues a move, the sprite's `target_pos` updates and `animate()` walks the rect toward it `PlayerSettings.ANIMATION_SPEED` pixels per frame, snapping when within one step of the target.

### Inventory and status effects
- Inventory is a dict of item → count, seeded from `ItemSettings.NORMAL_INITIAL_INVENTORY` (or `TEST_INITIAL_INVENTORY` in debug mode).
- Light selection is automatic (best owned source per `LightSettings.SOURCE_PRIORITY`) but can be cycled manually with L1/R1.
- Status effects (cloak invisibility, repellent) tick down per turn.

### Input split
Two distinct paths:
- **Polled** (`read_input_intent`): movement and most actions. Read once per frame from the keyboard state and joystick state; produces a `(dx, dy, action)` tuple.
- **Edge-triggered** (`handle_event`): light cycling. Needs one action per press, so it lives in the per-event handler.

This split is deliberate — putting light cycling on polled input would cycle multiple times per held press.

---

## 5. Monsters

[`Monster`](../core/sprites.py) is also a `pygame.sprite.Sprite` with grid-based AI.

- **Spawn**: `MonsterSettings.COUNT` per level, each placed at least `MIN_PLAYER_DISTANCE` Manhattan tiles from the player.
- **Chase trigger**: keyed off the player's current `light_radius` — light is danger. The legacy fixed-radius `CHASE_RADIUS` is gone; `MonsterSettings.HEARING_RADIUS` is reused for a separate "you hear something" warning when a monster is near in pitch dark.
- **Movement**: greedy-chase toward the player when triggered, otherwise idle (`IDLE_CHANCE` to skip a turn). Uses the same pixel-interpolation animation pattern as the player.
- **Repellent**: while active, monsters cannot enter the player's tile and visually shift to the repelled tint.

---

## 6. The light and fog-of-war system

The action window is dark by default. Light reveals it.

- **Light radius** is set by the active light source (`LightSettings.DEFAULT_RADIUS`, plus per-source bonuses for Match / Torch / Lantern). It ticks down per turn (`light_turns_left`) and reverts to the floor when it expires.
- **Fog of war** is rendered each frame as a black-alpha mask over the action window with concentric circles cleared around the player up to `radius_px`. The current implementation reallocates and redraws this every frame; caching by radius is a known optimization on the TODO list.
- **Line of sight** (`DungeonLevel.get_line_points`) walks a Bresenham line from monster to player to decide whether a monster can see the player through walls.
- **Map memory** (`ui/minimap_memory.py`) records every tile the player has ever seen lit; the minimap renders that memory plus enhanced reveals from Map / Magic Map items.

---

## 7. Turn resolution

A turn advances when:
- The player moves into a passable tile.
- The player digs (Space / A).
- The player lights a source (F / B).
- The player uses Detector / Repellent / Cloak.

Invalid actions (e.g. using an item the player doesn't own) do **not** advance the turn — the message log shows a hint instead.

After every turn-advancing action: monsters take their turns, status-effect counters tick, light counters tick, fog of war redraws.

---

## 8. The intermission flow

`IntermissionFlow` is the between-levels conductor:

1. **Door unlock sequence.** Border flash and "DOOR UNLOCKED" message.
2. **Treasure conversion.** Non-coin treasure is converted to gold one line at a time with a typewriter reveal.
3. **Auto-save.** `SaveManager.save_to_active_slot()` runs once. Message log shows "GAME SAVED."
4. **Shop.** Player spends gold on items for the next level.
5. **Level transition card** with the new dungeon's name, then `LevelLoader.load_level()` builds it.

The intermission state currently lives on `GameManager` attributes (the manager writes through `self.game.X = ...`); migrating that state onto `IntermissionFlow` itself is on the TODO list.

---

## 9. The save system

10 named JSON slots under `saves/`. Identity is held on `GameManager` as `player_name` and `active_save_slot` (1-indexed, or `None` when no save is bound).

- **NEW GAME**: slot select → overwrite confirm if occupied → name entry (1-8 chars, auto-uppercased) → tutorial prompt. The slot is reserved on disk **immediately** after name entry, so a quit before the first level clear still leaves a recoverable level-1 save.
- **LOAD GAME**: slot select. A non-fresh save drops into the pre-level shop (so different decisions can be made each attempt); the next dungeon is then re-rolled when the shop is exited. A brand-new save loads directly into level 1.
- **Auto-save** fires exactly once per cleared dungeon, between treasure conversion and the shop.
- **Death** and **game-over** do not write. **Final-dungeon clear** does not write, so beating the game leaves the slot pointing at the pre-final-dungeon shop.
- **Delete** is on the Load Game screen only, with a confirm prompt.

---

## 10. Score and leaderboard

`ScoreLeaderboardManager` owns:

- The running `score` (driven by treasure pickups).
- The persisted `leaderboard` (top entries; written only on win).
- `high_score` is **derived** from the top leaderboard entry — there is no separate `high_score.txt` anymore.
- The win-screen 3-letter initials entry flow.

A losing run sends the player back to the title screen with the leaderboard untouched.

---

## 11. The CRT post-process

[`CRT`](../ui/crt.py) blits a TV-frame image at a per-frame random alpha (`ScreenSettings.CRT_ALPHA_RANGE`) for flicker, then draws horizontal scanlines (`ScreenSettings.CRT_SCANLINE_HEIGHT`). It is the **last** thing drawn each frame.

**Known issue**: the overlay does not render correctly in fullscreen, so the game disables it when `full_screen` is True. This is documented in TODO under visual bugs.

---

## 12. Settings as the only knob panel

[settings.py](../settings.py) groups every tunable into a `*Settings` class, plus `AssetPaths` and `DebugSettings`. Subsystems import the classes they need (no `from settings import *` outside of `main.py` and `core/sprites.py`, which are the historical entry points and acceptable wildcard sites).

When adding a new tunable, add it to the most appropriate `*Settings` class with a comment explaining its **units**.

---

## 13. Input model

Two input devices, one event loop:

- **Keyboard** events → `KEYDOWN` / `KEYUP`. Movement and most actions are read polled; light cycling (Q/E) is edge-triggered.
- **Controller** events → `JOYBUTTONDOWN` / `JOYAXISMOTION`. Movement reads the D-pad (held), actions read button events.

Globals that intentionally fall through every other handler:
- `F11` / `Back` toggle fullscreen.
- `R2` toggles audio mute (analog trigger; `r2_trigger_is_pressed` is the edge-detection memory so a held trigger doesn't repeat).
- `Start + Back + L1 + R1` quit combo on any controller exits immediately.

Connected controllers are cached once in `setup_controllers` so the per-frame quit-combo check is a flat button-button-button-button read.

The slot-select and confirm dialogs use `previous_left_stick_x/y` for analog edge detection so analog navigation matches D-pad navigation.

---

## 14. Restart and shutdown

`reset_game` is the canonical "start over" path. Rather than manually resetting every subsystem, it constructs a brand-new `GameManager` (preserving fullscreen state) and calls `run()` on it, then `sys.exit()`s. This guarantees the restart path uses exactly the same boot sequence the game uses on first launch.

`close_game` calls `pygame.quit()` then `sys.exit()`. Every quit path eventually funnels into it.

---

## 15. Code conventions worth knowing

Most rules live in [.github/copilot-instructions.md](../.github/copilot-instructions.md). Two that shape how files **look**:

**Section banners.** Inside any file with multiple logical groupings, sections are separated by an all-caps banner:

```python
    # -------------------------
    # SECTION NAME
    # -------------------------
```

**Function order inside a class.** Functions are grouped by role; `update` and `run` go **last** and should only call other functions on the class.

---

## 16. Dev tools

`tools/map_viewer.py` is a standalone dungeon map browser. It imports from the `core/` package, so it must be run from the project root as a module:

```powershell
python -m tools.map_viewer
```

Running `python tools/map_viewer.py` directly will fail to import `core` and is not supported.
