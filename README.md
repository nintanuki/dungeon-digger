# Dungeon Digger

Dungeon Digger is a turn-based dungeon crawler where each action you take advances the world.
You dig for treasure, survive monsters, unlock doors, and descend through every level.

## Status

**Phase: Playable, polishing.** Full multi-level run, named save slots, leaderboard, shop, and tutorial all work end-to-end. Active work is performance caching, balance tuning, and visual polish. See [docs/TODO.md](docs/TODO.md) for the live backlog.

## Requirements

- Python 3.10+
- Pygame 2.5+

## Objective

Clear all dungeon levels in order by finding a key and unlocking the door on each level.

To win a run:
1. Explore the level.
2. Find the key.
3. Reach the door.
4. Use Dig at the door while carrying a key.
5. Repeat until you clear the final dungeon.

## Core Rules

- The game is turn-based: most player actions advance the turn.
- Monsters move/respond after your turn actions.
- If a monster reaches your tile and you are not invisible, you lose (this can happen even in darkness).
- You cannot move through walls.
- Digging can reveal loot, tools, treasure, or nothing.
- Keys, maps, and key detectors are level-scoped and do not carry between levels.
- Treasure is exchanged for gold between levels.
- Gold is used in the shop between levels.

## How Turns Work

The following actions generally consume a turn:
- Moving
- Digging
- Lighting a source (Match, Torch, Lantern)
- Using Key Detector
- Using Monster Repellent
- Using Invisibility Cloak

Some invalid actions do not advance a turn (for example, trying to use an item you do not have).

## Controls (Keyboard)

### Global
- Enter: Start game / continue on end screens
- F11: Toggle fullscreen

### Movement
- W A S D
- Arrow keys

### Actions
- Space: Dig (or attempt to unlock door if standing on it with a key)
- F: Use selected light source
- R: Use Monster Repellent
- X: Use Key Detector
- C: Use Invisibility Cloak
- Q / E: Cycle light source

### Shop
- Up/Down or W/S: Move selection
- Enter / Space / Z: Buy selected item (or Continue)

### Save Menus (Slot Select / Confirm Dialogs)
- Up/Down or W/S: Move slot cursor
- Left/Right: Move NO/YES selection in confirm dialogs
- Enter: Select / confirm
- Esc: Back one screen
- X or Delete: Delete the highlighted save (Load Game screen only)

### Name Entry (New Game)
- Type 1-8 letters, numbers, or spaces (auto-uppercased)
- Backspace: Delete last character
- Enter: Confirm name
- Esc: Cancel and return to slot select

### Initials Entry (Leaderboard, Win Only)
- Type letters A-Z
- Backspace: Delete last letter
- Enter: Submit initials (once 3 letters are entered)

## Controls (Controller)

### Global
- Start: Start / continue / confirm end-screen flow
- Back/Select: Toggle fullscreen
- R2: Toggle audio mute

### Movement
- D-pad

### Actions
- A: Dig
- B: Light
- X: Key Detector
- Y: Monster Repellent
- L1 / R1: Cycle light source
- L2: Invisibility Cloak

### Shop
- D-pad Up/Down: Move selection
- A: Buy selected item
- Start: Continue to next level

### Save Menus (Slot Select / Confirm Dialogs)
- D-pad / Left analog stick Up/Down: Move slot cursor
- D-pad / Left analog stick Left/Right: Move NO/YES selection in confirm dialogs
- A or Start: Select / confirm
- B: Back one screen
- X: Delete the highlighted save (Load Game screen only)

## Items and Effects

### Utility and Progression
- Key: Required to unlock the level door.
- Map: Reveals terrain memory on minimap.
- Magic Map: Stronger map behavior, including enhanced minimap utility.
- Key Detector: Gives proximity hints to the key.

### Survival Tools
- Match, Torch, Lantern: Provide temporary light radius for visibility.
- Monster Repellent: Temporarily repels monsters.
- Invisibility Cloak: Temporarily prevents monsters from detecting you.

### Treasure and Currency
- Gold Coins, Ruby, Sapphire, Emerald, Diamond: Treasure used for score and/or conversion.
- Between levels, non-coin treasure is exchanged into gold for shopping.

## Score and Leaderboard

- Treasure increases score.
- High score is the top entry on the leaderboard.
- Only completed runs (clearing the final dungeon) prompt for initials and write to the leaderboard. Death sends the player back to the title screen with the leaderboard untouched.
- Leaderboard stores top entries and is shown at the end of a winning run.

## Save System

- Up to 10 named save slots, each stored as JSON in the `saves/` directory.
- Choose **NEW GAME** to pick a slot and enter a name (8 chars max). The slot is reserved on disk immediately so a quit before the first level clear still leaves a recoverable level-1 save.
- Choose **LOAD GAME** to resume any occupied slot. A non-fresh save drops the player into the pre-level shop so different shopping decisions can be made each attempt; the next dungeon is then re-rolled when the shop is exited. A brand-new save loads directly into level 1.
- Auto-save fires once per cleared dungeon, between treasure conversion and the shop. The message log shows "GAME SAVED." when it completes.
- Death and quit do not write a save. Final-dungeon clear also does not write a save, so beating the game leaves the slot pointing at the shop before the final dungeon.
- The Load Game screen has a delete affordance (X button on controller, X or Delete key on keyboard, with a confirm prompt).

## Game Flow

1. Title Screen
2. (NEW GAME) Slot Select → Overwrite Confirm (if occupied) → Name Entry → Tutorial Prompt
3. (LOAD GAME) Slot Select → Pre-Level Shop (or Level 1 directly for a fresh save)
4. Level gameplay
5. Door unlock sequence
6. Treasure conversion
7. Auto-save
8. Shop
9. Next level transition
10. Final win screen + leaderboard, or game-over screen back to title

## Running the Game

From the project directory:

```bash
python main.py
```

If your environment uses a different Python command, use that equivalent.

### Map Viewer (Dev Tool)

A standalone dungeon map browser lives at `tools/map_viewer.py`. Because it
imports from the `core/` package, run it from the project root as a module so
Python resolves the package path correctly:

```bash
python -m tools.map_viewer
```

Running `python tools/map_viewer.py` directly will fail to import `core` and
is not supported.

## Documentation

Read these in order before contributing:

1. **[README.md](README.md)** — *(this file)* what the project is and how to run it.
2. **[docs/TODO.md](docs/TODO.md)** — phased roadmap, known bugs, ideas.
3. **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — how the code actually works.
4. **[docs/CHANGELOG.md](docs/CHANGELOG.md)** — append-only history of every change.
5. **[docs/TESTING.md](docs/TESTING.md)** — manual smoke-test checklist after changes.
6. **[.github/copilot-instructions.md](.github/copilot-instructions.md)** — required reading for every editor, human or AI.

## Project Layout

```
dungeon-digger/
├── main.py              entry point
├── settings.py          tunables and resolved asset paths
├── README.md
├── assets/              font/ graphics/ music/ sound/
├── docs/                CHANGELOG.md, TESTING.md, TODO.md
├── saves/               runtime-generated JSON save slots
├── core/                world & gameplay (dungeon, sprites, loot, tutorial, …)
├── ui/                  rendering, windows, CRT, minimap
├── systems/             audio, score/intermission managers, save manager
├── util/                shared helpers (coords)
└── tools/               dev/debug scripts (map_viewer)
```
