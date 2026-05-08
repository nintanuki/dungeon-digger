# Change Log

This file is an append-only record of every code change made to Dungeon Digger
by a human, AI assistant, or copilot tool. Read it before making changes so you
know the current state of the codebase.

## Format

Each entry covers one logical change (which may touch multiple files). Use the
template below, with one `**File:** ... **Why:** ...` block per file touched.

    ## YYYY-MM-DD HH:MM — short summary

    **File:** path/to/file.py
    **Lines (at time of edit):** 38-52 (modified)
    **Before:**
        [old code]
    **After:**
        [new code]
    **Why:** explanation

## Conventions

* Line numbers reflect the file as it existed at the moment of the edit. Edits
  above shift line numbers below, so older entries will not match the current
  file. Never go back and "fix" old line numbers.
* Entries are append-only. Never delete history. If a later edit reverts an
  earlier one, write a new entry that references the original.
* For new files, write `(new file)` instead of a line range. The "Before"
  block can be omitted or marked `(file did not exist)`.
* For deletes, write `(deleted)` and put the removed code in "Before" with no
  "After" block.
* Keep "Before" / "After" blocks short. If a change is huge, summarize with a
  diff-style excerpt of the most important lines plus a sentence describing the
  rest, instead of pasting the entire file.

---

## 2026-04-27 11:41 — Initialize change log and add CHANGELOG rule

**File:** TESTING.md
**Lines (at time of edit):** 18-19 (added)
**Before:**
    # Refactoring Rules
    * All classes and functions must have a docstring
**After:**
    # Refactoring Rules
    * Update CHANGELOG.md for every code change (timestamp, file, line numbers, before/after, why). Read it first before making changes so you know the current state.
    * All classes and functions must have a docstring
**Why:** Establishes a permanent rule that every code change must be logged in
CHANGELOG.md, so the project owner can audit AI/copilot edits later.

**File:** CHANGELOG.md
**Lines (at time of edit):** (new file)
**Before:** (file did not exist)
**After:** (new file with format header, conventions, and this initial entry)
**Why:** Creates the audit log itself. Format header documents how future
entries should be written.

---

## 2026-04-27 11:42 — Simplify shop: drop bulk buy, prune limited stock to cloak only

**File:** settings.py
**Lines (at time of edit):** 204 (deleted)
**Before:**
    SHOP_DISPLAY_DELAY_MS = 200
    SHOP_BULK_PURCHASE_QUANTITY = 5
    STATUS_EFFECT_TURN_BUFFER = 1
**After:**
    SHOP_DISPLAY_DELAY_MS = 200
    STATUS_EFFECT_TURN_BUFFER = 1
**Why:** Bulk-buy feature removed at owner's request — was never wanted in the
first place. Constant has no remaining references.

**File:** settings.py
**Lines (at time of edit):** 343-348 (modified)
**Before:**
    SHOP_LIMITED_STOCK_TEMPLATE = {
        'LANTERN': 3,
        'INVISIBILITY CLOAK': 1,
        'MAP': 1,
        'KEY DETECTOR': 1,
    }
**After:**
    # Only the invisibility cloak is limited stock (one per shop visit, and
    # zero if the player already owns one). Every other item is unlimited.
    SHOP_LIMITED_STOCK_TEMPLATE = {
        'INVISIBILITY CLOAK': 1,
    }
**Why:** Owner wants the cloak to be the only limited-stock shop item so the
"x N" indicators next to other items can disappear. LANTERN, MAP, and KEY
DETECTOR are now unlimited.

**File:** managers.py
**Lines (at time of edit):** 603-638 (modified)
**Before:**
    if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z, pygame.K_x, pygame.K_5):
        ...
        quantity = (
            GameSettings.SHOP_BULK_PURCHASE_QUANTITY
            if event.key in (pygame.K_x, pygame.K_5)
            else 1
        )
        self.buy_shop_item(selected_option, quantity=quantity)
        ...
    if event.button == InputSettings.JOY_BUTTON_X:
        ...
        self.buy_shop_item(selected_option, quantity=GameSettings.SHOP_BULK_PURCHASE_QUANTITY)
**After:**
    if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
        ...
        self.buy_shop_item(selected_option)
        ...
    (JOY_BUTTON_X branch removed entirely)
**Why:** Removes bulk-buy keyboard (K_x, K_5) and controller (X button) paths.
A press now always purchases one of the selected item.

**File:** render.py
**Lines (at time of edit):** 392-401 (modified)
**Before:**
    else:
        count_suffix = '' if stock is None else f" x{stock}"
        line_text = f"{option}{count_suffix} - {price}G"
        color = ColorSettings.TEXT_DEFAULT
**After:**
    else:
        line_text = f"{option} - {price}G"
        color = ColorSettings.TEXT_DEFAULT
**Why:** With cloak as the only limited-stock item, the only meaningful
"stock" message is OUT OF STOCK once the cloak is owned. The "x1" indicator
that the cloak otherwise rendered is misleading and visually noisy.

---

## 2026-04-27 11:43 — Consolidate high score: drop high_score.txt, derive from leaderboard

**File:** settings.py
**Lines (at time of edit):** 190 (deleted)
**Before:**
    LEVEL_TRANSITION_MS = 2000
    HIGH_SCORE_FILE = 'high_score.txt'
    LEADERBOARD_FILE = 'leaderboard.txt'
**After:**
    LEVEL_TRANSITION_MS = 2000
    LEADERBOARD_FILE = 'leaderboard.txt'
**Why:** Removes the dedicated high-score filename. The leaderboard's top
entry is now the sole source of truth.

**File:** managers.py
**Lines (at time of edit):** 22-62 (modified — get_high_score_path deleted, load_high_score and save_high_score reworked)
**Before:**
    def get_high_score_path(self) -> str:
        return os.path.join(os.path.dirname(__file__), GameSettings.HIGH_SCORE_FILE)
    ...
    def load_high_score(self) -> int:
        # read high_score.txt, parse int, return 0 on missing/error
    def save_high_score(self) -> None:
        # write current high score to high_score.txt
**After:**
    (get_high_score_path removed)
    def load_high_score(self) -> int:
        entries = self.load_leaderboard()
        if not entries:
            return 0
        return entries[0][1]
    def save_high_score(self) -> None:
        self.game.high_score = max(self.game.high_score, self.game.score)
**Why:** load_high_score now derives the value from leaderboard.txt's top
entry instead of reading a separate file. save_high_score becomes a no-write
sync of the in-memory value (kept under its existing name per TESTING.md
rule against renaming functions; docstring documents the new behavior).
get_high_score_path is removed as dead code now that nothing reads or
writes a separate high score file.

**File:** .gitignore
**Lines (at time of edit):** 203 (modified)
**Before:**
    # Dungeon Digger runtime data
    high_score.txt
    leaderboard.txt
**After:**
    # Dungeon Digger runtime data
    leaderboard.txt
    saves/
**Why:** high_score.txt is no longer written. saves/ is added in advance of
the save-slot directory created by the upcoming SaveManager.

---

## 2026-04-27 11:45 — Death now returns to title (no leaderboard on loss)

**File:** managers.py
**Lines (at time of edit):** 199-219 (modified)
**Before:**
    def continue_from_game_over(self) -> None:
        """Advance into initials entry or directly to leaderboard."""
        if self.is_top_ten_score(self.game.pending_leaderboard_score):
            self.game.ui_state = "enter_initials"
            self.game.initials_entry = "AAA"
            self.game.initials_index = 0
            return
        self.game.ui_state = "leaderboard"
**After:**
    def continue_from_game_over(self) -> None:
        """Route from the game-over screen based on the run outcome.
        ...
        """
        if self.game.game_result == "loss":
            self.game.reset_game()
            return
        if self.is_top_ten_score(self.game.pending_leaderboard_score):
            self.game.ui_state = "enter_initials"
            self.game.initials_entry = "AAA"
            self.game.initials_index = 0
            return
        self.game.ui_state = "leaderboard"
**Why:** Owner wants the leaderboard to be a hall-of-fame for completed runs
only. On loss the run is over and the player is dropped back to a fresh title
screen via reset_game(); their save file (once that system lands) persists
untouched. On win the existing initials entry / leaderboard flow stays in
place.

**File:** main.py
**Lines (at time of edit):** 247-263 (modified)
**Before:**
    def finish_game(self, result: str) -> None:
        """End the current run, freeze world updates, and persist the high score.
        ...
        """
        ...
        self.audio.stop_music()
        self.score_manager.save_high_score()
**After:**
    def finish_game(self, result: str) -> None:
        """End the current run and freeze world updates.
        High-score persistence is no longer triggered here. ...
        """
        ...
        self.audio.stop_music()
        (save_high_score call removed)
**Why:** save_high_score's previous role (write high_score.txt) no longer
applies, and bumping the in-memory high_score on loss would cause the GAME
OVER screen to briefly display a promoted high score even though the run
will not be recorded. Wins still promote the score via add_leaderboard_entry
when the player submits initials.

---

## 2026-04-27 11:48 — Add SaveManager + save settings, wire identity onto GameManager

**File:** settings.py
**Lines (at time of edit):** 192-200 (added)
**Before:** (only LEADERBOARD_FILE / LEADERBOARD_LIMIT in this region)
**After:**
    SAVES_DIR = 'saves'
    SAVE_VERSION = 1
    MAX_SAVE_SLOTS = 10
    MAX_PLAYER_NAME_LENGTH = 8
**Why:** Configuration constants for the new save system. SAVE_VERSION lets
us detect schema drift on future changes.

**File:** save_manager.py
**Lines (at time of edit):** (new file)
**Before:** (file did not exist)
**After:** (new file with SaveManager class — list_slots, load_slot,
save_slot, delete_slot, sanitize_name, plus path helpers and the
ALLOWED_NAME_CHARS whitelist)
**Why:** Self-contained module so persistence logic does not bloat
managers.py. Saves are JSON, one file per slot, with corrupted files
surfaced via a flag instead of crashing the load screen.

**File:** main.py
**Lines (at time of edit):** 11 (added import), 38 (added save_manager
instance), 44-49 (added player_name and active_save_slot)
**Before:** (no save_manager wiring; no player identity fields)
**After:**
    from save_manager import SaveManager
    ...
    self.save_manager = SaveManager(self)
    ...
    self.player_name = ""
    self.active_save_slot: int | None = None
**Why:** GameManager needs an instance of the persistence manager and two
identity fields the auto-save writer reads. Set to empty / None until the
title flow resolves into either NEW GAME (assigns both) or LOAD GAME
(restores both from the chosen slot).

---

## 2026-04-27 11:50 — Auto-save trigger between treasure conversion and shop

**File:** managers.py
**Lines (at time of edit):** 449-481 (added — write_auto_save method and
its call site inside complete_treasure_conversion)
**Before:**
    self.game.in_treasure_conversion = False
    self.game.treasure_conversion_data = {}
    self.start_shop_phase()
**After:**
    self.game.in_treasure_conversion = False
    self.game.treasure_conversion_data = {}
    self.write_auto_save()
    self.start_shop_phase()
    ...
    def write_auto_save(self) -> None:
        if self.game.active_save_slot is None:
            return
        self.game.save_manager.save_slot(
            slot_id=self.game.active_save_slot,
            player_name=self.game.player_name,
            next_level_index=self.game.pending_level_index,
            inventory=self.game.player.inventory,
            discovered_items=self.game.player.discovered_items,
            score=self.game.score,
        )
**Why:** Auto-save fires once per cleared dungeon, after gold conversion
and inventory cleanup but before the shop opens, so a death-then-reload
keeps the player's gold and lets them re-roll the next dungeon's
randomized monster and loot placement. Guard on active_save_slot keeps
the function safe even if a future code path enters this flow without a
bound slot.

---

## 2026-04-27 15:37 — Save flow UI: states, handlers, render methods, NEW/LOAD wiring

**File:** settings.py
**Lines (at time of edit):** ~263-265 (added JOY_AXIS_LEFT_X, JOY_AXIS_LEFT_Y), ~187-200 (added save constants in earlier entry, see above)
**After:**
    JOY_AXIS_LEFT_X = 0
    JOY_AXIS_LEFT_Y = 1
**Why:** Constants for left analog stick navigation in menus, mirroring the
existing R2 mute axis pattern.

**File:** settings.py
**Lines (at time of edit):** ~187-205 (added)
**After:**
    SLOT_SELECT_TITLE_Y = 50
    SLOT_SELECT_START_Y = 110
    SLOT_SELECT_ROW_HEIGHT = 36
    SLOT_SELECT_ROW_X = 120
    SLOT_SELECT_CURSOR_OFFSET_X = -20
    SLOT_SELECT_PROMPT_Y_OFFSET = 35
    SAVE_DIALOG_TITLE_Y = 150
    SAVE_DIALOG_BODY_Y = 230
    SAVE_DIALOG_FOCAL_Y = 320
    SAVE_DIALOG_PROMPT_Y_OFFSET = 50
    SAVE_DIALOG_OPTION_GAP = 100
**Why:** Layout constants for the four new save-flow screens, matching the
naming style of the existing leaderboard/initials layouts.

**File:** main.py
**Lines (at time of edit):** ~67-83 (added GameManager state for slot
select, name entry, confirm dialogs, analog stick edge memory)
**After:**
    self.slot_select_index = 0
    self.name_entry_buffer = ""
    self.confirm_index = 0
    self.confirm_target_slot = 0
    self.previous_left_stick_x = 0.0
    self.previous_left_stick_y = 0.0
**Why:** Backing fields for the new ui_states. confirm_index defaults to 0
(NO) so a button mash can't accidentally overwrite or delete a save.

**File:** main.py
**Lines (at time of edit):** ~216-264 (added start_gameplay_from_save),
~266-409 (added handle_confirm_move, handle_back_press, handle_delete_press,
commit_name_entry, handle_name_entry_keypress, plus extended
handle_title_menu_move and handle_start_press for the new states)
**After:** New methods route the save flow:
- start_gameplay_from_save: sets state, calls level_loader.load_level for
  the just-completed level as backdrop, then start_shop_phase. Brand-new
  saves (next_level == first level number) skip the shop.
- handle_confirm_move / handle_back_press / handle_delete_press / commit_name_entry / handle_name_entry_keypress: small focused helpers driving the new ui_states.
- handle_title_menu_move extended to drive slot select.
- handle_start_press extended with branches for slot_select_new,
  slot_select_load, overwrite_confirm, delete_confirm, name_entry.
**Why:** The full save UI flow plus the load-resume helper. Extends rather
than replaces the existing menu helpers so 'title' / 'newgame_prompt' /
'game_over' / 'enter_initials' / 'leaderboard' all behave as before.

**File:** main.py
**Lines (at time of edit):** ~681-720 (added _dispatch_menu_navigate),
~723-797 (extended _handle_keydown, _handle_joybuttondown,
_handle_joyhatmotion, _handle_joyaxismotion)
**Why:** Routes keyboard, D-pad, and left analog stick events into the new
nav helpers. Name entry consumes all keyboard input via
handle_name_entry_keypress so typing a letter never doubles as a gameplay
shortcut. Analog stick uses the same edge-trigger pattern as R2.

**File:** main.py
**Lines (at time of edit):** ~895-905 (extended _render_frame dispatch)
**Before:**
    if self.ui_state in {'title', 'newgame_prompt'}:
        self.render.draw_title_screen()
    elif self.ui_state == 'game_over':
        ...
**After:**
    if self.ui_state in {'title', 'newgame_prompt'}:
        self.render.draw_title_screen()
    elif self.ui_state in {'slot_select_new', 'slot_select_load'}:
        self.render.draw_slot_select_screen()
    elif self.ui_state == 'name_entry':
        self.render.draw_name_entry_screen()
    elif self.ui_state == 'overwrite_confirm':
        self.render.draw_overwrite_confirm_screen()
    elif self.ui_state == 'delete_confirm':
        self.render.draw_delete_confirm_screen()
    elif self.ui_state == 'game_over':
        ...
**Why:** Wires the new render methods into the per-frame dispatch.

**File:** render.py
**Lines (at time of edit):** ~622-820 (added)
**After:** Five new methods:
- draw_slot_select_screen
- draw_name_entry_screen
- draw_overwrite_confirm_screen
- draw_delete_confirm_screen
- _draw_confirm_dialog (private helper shared by the two confirm screens)
**Why:** Renders the four new save-flow screens. _draw_confirm_dialog
keeps the YES/NO confirm layout consistent across overwrite and delete.

---

## 2026-04-27 15:37 — Bug fixes: starting level, save indicator, slot reservation

**File:** main.py
**Lines (at time of edit):** ~196-214 (start_gameplay_from_title)
**Before:**
    self.current_level_index = 1
    self.pending_level_index = 1
**After:**
    self.current_level_index = 0
    self.pending_level_index = 0
**Why:** current_level_index is a 0-indexed position into level_numbers
(which starts at level 1). The previous value of 1 silently skipped level
1 and dropped the player into level 2 on a fresh run, which is what made
"after level 1 it jumps straight to level 3" — they were actually on
level 2 the whole time.

**File:** save_manager.py
**Lines (at time of edit):** ~158-167 (list_slots), ~190-225 (save_slot)
**Before:** Save schema used `next_level_index` (0-indexed) and
list_slots returned that as `level`.
**After:** Save schema uses `next_level` (1-indexed dungeon number).
list_slots returns it directly so the slot list shows "LV  1" for a
brand-new save instead of "LV  0".
**Why:** Human-readable level numbers in the save file and on the slot
list. Brand-new saves now read as level 1, after-level-1 saves as level
2, etc.

**File:** managers.py
**Lines (at time of edit):** ~462-486 (write_auto_save)
**Before:** Passed `next_level_index=self.game.pending_level_index` and
emitted no log message.
**After:** Computes 1-indexed `next_level = level_numbers[pending_level_index]`,
passes that, and on a successful write logs "GAME SAVED." through the
message log.
**Why:** Matches the save schema rename and gives the player visible
confirmation that the auto-save fired (was previously silent).

**File:** main.py
**Lines (at time of edit):** ~358-401 (commit_name_entry)
**After:** After committing the name, immediately calls
save_manager.save_slot with next_level set to level_numbers[0] (1),
the player's current inventory and discovered_items (initial state at
title), and score 0.
**Why:** Reserves the slot on disk the moment the player confirms a name,
so quitting before the first level clear leaves a recoverable level-1 save
rather than an empty slot. Mirrors the spec's "creating a new save file
should reserve a slot for save files".

**File:** main.py
**Lines (at time of edit):** ~216-281 (start_gameplay_from_save)
**Before:** Always called intermission.start_shop_phase() after loading.
**After:** Reads the new 1-indexed `next_level` field. When equal to the
first level number, skips the shop and starts gameplay directly (no shop
exists before level 1). Otherwise drops into the pre-level shop as
before.
**Why:** Lets a brand-new reserved save resume into level 1 gameplay
rather than the meaningless "shop before level 1" path.

---

## 2026-04-27 15:39 — Documentation: README and TODO updates

**File:** README.md
**Lines (at time of edit):** ~58-90 (Shop / Save Menus / Name Entry /
Initials Entry sections), ~109-141 (Score and Leaderboard, Save System,
Game Flow)
**Why:** Drops the X / 5 bulk-buy keyboard binding and the X-button
controller bulk-buy binding from the Shop sections; adds new Save Menus
and Name Entry sections covering keyboard and controller controls;
clarifies that initials entry only happens on a winning run; adds a Save
System section describing slots, where saves live, when auto-save fires,
and what death/quit/win do to the slot; updates the Game Flow numbered
list to include the slot-select / name-entry / pre-level-shop steps and
the auto-save point.

**File:** TODO.md
**Lines (at time of edit):** 45 (high_score.txt entry), 115 (save game
idea), 120 (bulk buy entry), 131-134 (Save Game Project section)
**Why:** Marks the high_score.txt consolidation, save game feature,
bulk buy removal, and the three "Save Game Project" bugs the owner
flagged in this conversation as done. Each marked entry preserves the
original text and appends a parenthetical with what was actually
shipped.

---

## 2026-04-27 15:42 — Strip trailing null bytes from render.py

**File:** render.py
**Lines (at time of edit):** EOF (12 trailing null bytes removed)
**Why:** A previous Edit call left twelve `\x00` bytes at the very end of
the file, which made `ast.parse` reject it ("source code string cannot
contain null bytes") even though Python's import machinery still tolerated
the file. Stripping the nulls and normalizing to a single trailing newline
restores parseability without changing any code.

---

## 2026-04-27 15:55 — Highlight "GAME SAVED" message in green

**File:** windows.py
**Lines (at time of edit):** 38 (added)
**Before:**
    term_colors = {
        "YOU WERE CAUGHT BY THE MONSTER": ColorSettings.TEXT_LOSS,
        "KEY": ColorSettings.BORDER_KEY_ACTIVE,
        ...
    }
**After:**
    term_colors = {
        "YOU WERE CAUGHT BY THE MONSTER": ColorSettings.TEXT_LOSS,
        "GAME SAVED": ColorSettings.TEXT_WIN,
        "KEY": ColorSettings.BORDER_KEY_ACTIVE,
        ...
    }
**Why:** Adds "GAME SAVED" to the message-log highlight table so the
auto-save confirmation reads in green (TEXT_WIN), making it visually
distinct from neutral status lines. Trailing period is left in the
default message color thanks to the existing word-boundary check in
_has_word_boundaries.

---

## 2026-04-28 17:50 — Reorganize project into packages; bundle assets/ and docs/ (Claude Opus 4.7)

**File:** assets/font/, assets/graphics/, assets/music/, assets/sound/
**Lines (at time of edit):** (relocated)
**Before:** Each media folder lived directly at the project root
(`font/`, `graphics/`, `music/`, `sound/`).
**After:** All four moved under a single `assets/` umbrella so the
project root only carries code, docs, saves, README, and `.gitignore`.
**Why:** Owner request: tidy the root by collecting bundled media into
one folder. Internal subfolders (graphics/monsters, graphics/npcs,
graphics/player) were preserved.

**File:** docs/CHANGELOG.md, docs/TESTING.md, docs/TODO.md
**Lines (at time of edit):** (relocated)
**Before:** CHANGELOG.md, TESTING.md, TODO.md lived at the project root.
**After:** Moved under `docs/`. README.md stays at the root so GitHub
still renders it on the main repo page.
**Why:** Owner request: separate ancillary documentation from the README
without breaking GitHub's front-page README rendering.

**File:** core/__init__.py, ui/__init__.py, systems/__init__.py,
util/__init__.py, tools/__init__.py
**Lines (at time of edit):** (new files)
**Before:** (files did not exist)
**After:** Empty package marker files.
**Why:** Required so `from core.dungeon import ...`, `from ui.windows
import ...`, etc. resolve.

**File:** core/dungeon.py, core/dungeon_config.py, core/level_loader.py,
core/loot.py, core/sprites.py, core/tilemaps.py, core/tutorial.py
**Lines (at time of edit):** (relocated; imports updated)
**Before:** Each lived at the project root with bare imports
(`from tilemaps import DUNGEONS`, `import coords`, `import loot`,
`from sprites import ...`, etc.).
**After:** Moved into `core/`. Cross-package imports rewritten:
`from core.tilemaps import DUNGEONS`,
`from core.dungeon_config import get_monster_count_for_dungeon`,
`from core.sprites import Door, Monster, NPC, Player`,
`from core import loot`,
`from util import coords`,
`from ui.minimap_memory import MinimapMemory`,
`from ui.render import RenderManager`,
`from ui.render_utils import color_with_alpha`.
**Why:** World/gameplay modules grouped together. `tutorial.py` lives in
core because it owns gameplay event hooks (notify, on_turn_end) even
though it also draws an overlay. Bare-name `coords` and `loot` imports
became package-qualified but still bind the same local name (`from util
import coords` → call sites `coords.tile_to_screen(...)` keep working).

**File:** ui/render.py, ui/render_utils.py, ui/crt.py, ui/windows.py,
ui/minimap_memory.py
**Lines (at time of edit):** (relocated; imports updated)
**Before:** Each lived at the project root with bare imports
(`import coords`, `from render_utils import ...`).
**After:** Moved into `ui/`. Cross-package imports rewritten to
`from util import coords` and (within ui/render.py) `from ui.render_utils
import color_with_alpha`.
**Why:** Anything that owns drawing or window state is now under one
package.

**File:** systems/audio.py, systems/managers.py, systems/save_manager.py
**Lines (at time of edit):** (relocated)
**Before:** audio.py, managers.py, save_manager.py at the project root.
**After:** Moved into `systems/`. None of the three had cross-module
imports beyond settings, so no further import edits were needed (other
than save_manager.py picking up AssetPaths — see next entry).
**Why:** Cross-cutting services that aren't gameplay or rendering live
together.

**File:** util/coords.py
**Lines (at time of edit):** (relocated)
**Before:** coords.py at the project root.
**After:** Moved into `util/`. No internal edits.
**Why:** Pure coordinate helper — neither core nor UI specifically. Lives
in its own small util/ package so callers from any layer import it
without a layering smell.

**File:** tools/map_viewer.py
**Lines (at time of edit):** 1-12 (docstring + imports updated)
**Before:**
    """Standalone dungeon map viewer for quick layout inspection.

    This tool is intentionally separate from game runtime code.
    Run this file directly to browse all dungeons.
    """
    ...
    from dungeon_config import DUNGEON_DIFFICULTY, DUNGEON_MONSTER_COUNTS
    from tilemaps import DUNGEONS
**After:**
    """Standalone dungeon map viewer for quick layout inspection.

    This tool is intentionally separate from game runtime code.
    Run from the project root with `python -m tools.map_viewer` so the
    core/ package is importable; running the file directly will fail
    because the script directory becomes tools/ instead of the repo root.
    """
    ...
    from core.dungeon_config import DUNGEON_DIFFICULTY, DUNGEON_MONSTER_COUNTS
    from core.tilemaps import DUNGEONS
**Why:** Moved into `tools/` to separate dev utilities from the runtime
package. Docstring documents the new run command because invoking the
file directly stops working once the package import is required.

**File:** main.py
**Lines (at time of edit):** 4-15 (modified), 965 (modified)
**Before:**
    from settings import *
    from audio import AudioManager
    from windows import MessageLog, InventoryWindow, MapWindow
    from dungeon import DungeonLevel
    from dungeon_config import DUNGEON_CONFIG, LEVEL_DUNGEON_ORDER
    from crt import CRT
    from managers import ScoreLeaderboardManager, IntermissionFlow
    from save_manager import SaveManager
    from tutorial import TutorialManager
    import coords
    import loot
    from level_loader import LevelLoader
    ...
    if __name__ == '__main__':
**After:**
    from settings import *
    from systems.audio import AudioManager
    from ui.windows import MessageLog, InventoryWindow, MapWindow
    from core.dungeon import DungeonLevel
    from core.dungeon_config import DUNGEON_CONFIG, LEVEL_DUNGEON_ORDER
    from ui.crt import CRT
    from systems.managers import ScoreLeaderboardManager, IntermissionFlow
    from systems.save_manager import SaveManager
    from core.tutorial import TutorialManager
    from util import coords
    from core import loot
    from core.level_loader import LevelLoader
    ...
    if __name__ == "__main__":
**Why:** Updates the entry point's imports for the new package layout.
The `if __name__` quote-style swap was a touch-edit to force the bash
sandbox mount to refresh its stale view of the file during verification;
behavior is identical.

**File:** settings.py
**Lines (at time of edit):** 427-436 (FontSettings.FONT), 454-473
(AssetPaths preamble), 496 (SOUND_DIR), 516 (MUSIC_DIR)
**Before:**
    FONT = 'font/Pixeled.ttf'
    ...
    BASE_DIR = os.path.dirname(__file__)
    GRAPHICS_DIR = os.path.join(BASE_DIR, 'graphics')
    ...
    SOUND_DIR = os.path.join(BASE_DIR, 'sound')
    ...
    MUSIC_DIR = os.path.join(BASE_DIR, 'music')
**After:**
    FONT = os.path.join(
        os.path.dirname(__file__), 'assets', 'font', 'Pixeled.ttf'
    )
    ...
    BASE_DIR = os.path.dirname(__file__)
    ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
    GRAPHICS_DIR = os.path.join(ASSETS_DIR, 'graphics')
    ...
    SOUND_DIR = os.path.join(ASSETS_DIR, 'sound')
    ...
    MUSIC_DIR = os.path.join(ASSETS_DIR, 'music')
**Why:** Repoints every bundled-media path under the new `assets/`
folder. The `FontSettings.FONT` value also becomes an absolute path so
`pygame.font.Font(...)` no longer depends on the caller's working
directory.

**File:** systems/save_manager.py
**Lines (at time of edit):** 18 (modified), 29-30 (comment updated),
45-54 (get_saves_dir reworked)
**Before:**
    from settings import GameSettings
    ...
    # The whitelist for player names is everything the pixel font in
    # font/Pixeled.ttf displays cleanly.
    ...
    def get_saves_dir(self) -> str:
        ...
        return os.path.join(os.path.dirname(__file__), GameSettings.SAVES_DIR)
**After:**
    from settings import AssetPaths, GameSettings
    ...
    # The whitelist for player names is everything the pixel font in
    # assets/font/Pixeled.ttf displays cleanly.
    ...
    def get_saves_dir(self) -> str:
        ...
        # Anchor on the project root (AssetPaths.BASE_DIR) rather than
        # this file's directory; otherwise saves would land in
        # systems/saves/ after this module moved into the systems/
        # package.
        return os.path.join(AssetPaths.BASE_DIR, GameSettings.SAVES_DIR)
**Why:** save_manager moved into systems/, so `os.path.dirname(__file__)`
no longer points at the project root. Anchoring on `AssetPaths.BASE_DIR`
keeps `saves/` at the repo root where it has always lived. Comment
update follows the renamed font path.

**File:** README.md
**Lines (at time of edit):** ~156-200 (Running the Game extended; new
Documentation and Project Layout sections appended)
**After:** Adds a "Map Viewer (Dev Tool)" subsection describing
`python -m tools.map_viewer` and warning that running the file directly
no longer works. Adds a "Documentation" section linking
`docs/CHANGELOG.md`, `docs/TESTING.md`, and `docs/TODO.md`. Adds a
"Project Layout" section that documents the new top-level folder split.
**Why:** README needs to describe the new run command for the moved
map viewer, and the moved CHANGELOG/TESTING/TODO docs are no longer
findable from the repo root unless something in the README points at
them. README.md itself stays at the repo root so GitHub still renders
it on the main project page.

---

## 2026-04-28 18:05 — Monster AI: Bresenham LOS + darkness hearing warning (Claude Opus 4.7)

**File:** settings.py
**Lines (at time of edit):** 280-289 (renamed CHASE_RADIUS → HEARING_RADIUS, added comment)
**Before:**
    COUNT = 3
    CHASE_RADIUS = 3  # Manhattan distance
    IDLE_CHANCE = 0.3
**After:**
    COUNT = 3
    # HEARING_RADIUS replaces the legacy CHASE_RADIUS. The chase trigger
    # now keys off the player's light_radius (light = danger), so this
    # value is reused for a different role: the Manhattan bubble inside
    # which a monster can sense the player even in pitch darkness and
    # emit a one-shot "you hear something" warning. ...
    HEARING_RADIUS = 3  # Manhattan distance
    IDLE_CHANCE = 0.3
**Why:** Owner confirmed CHASE_RADIUS was legacy from a pre-light-mechanic
proximity-only chase model. The constant had zero references after the
chase trigger moved to player.light_radius. Repurposing the same value as
a hearing/warning radius gives it a new, real role rather than deleting
it; the comment documents the history so the next reader doesn't have to
re-derive it.

**File:** core/sprites.py
**Lines (at time of edit):** 644-649 (Monster.__init__ added flag)
**Before:**
    self.is_chasing = False
**After:**
    self.is_chasing = False
    # Edge-trigger flag for the darkness hearing warning so the
    # log doesn't spam every turn the monster sits inside the
    # hearing bubble. Resets when the monster leaves the bubble
    # so a fresh approach can re-arm the warning.
    self.has_warned_player_of_proximity = False
**Why:** Backing field for the new darkness-warning helper. Comment
explains the edge-trigger semantics so the reset path in
`_maybe_warn_proximity_in_dark` doesn't look accidental.

**File:** core/sprites.py
**Lines (at time of edit):** 704-709 (Monster.resolve_turn no-light branch)
**Before:**
    if not player_has_light:
        self._stop_chasing()
**After:**
    if not player_has_light:
        self._stop_chasing()
        # Darkness still hides the player from active pursuit, but
        # the player gets an audible cue so a wandering monster
        # ending its turn on their tile isn't a blind coin flip.
        self._maybe_warn_proximity_in_dark(manhattan_distance)
**Why:** Reported gameplay issue — players were dying in the dark to what
felt like RNG, with no warning. Wiring the helper into the existing
no-light branch preserves "darkness hides you" but tells the player when
something is creeping close enough to matter.

**File:** core/sprites.py
**Lines (at time of edit):** 771-788 (Monster.has_clear_line_of_sight_to_player rewritten)
**Before:**
    # Check if they are in the same column
    if m_col == p_col:
        ...
    # Check if they are in the same row
    if m_row == p_row:
        ...
    return False
**After:**
    return self.dungeon.has_line_of_sight((m_col, m_row), (p_col, p_row))
**Why:** Reported gameplay issue — monsters rarely noticed the player
even with a lantern. The previous LOS only succeeded when monster and
player shared a row or column, so any diagonal offset returned False.
DungeonLevel.has_line_of_sight already implements proper grid raytracing
via Bresenham's line algorithm; delegating to it picks up diagonal sight
for free. Docstring names the algorithm so the math isn't a mystery to
future readers (per TESTING.md's "comments must explain why" rule).
Also closes docs/TODO.md line 46 ("Enemy line of sight doesn't seem to
work diagonally").

**File:** core/sprites.py
**Lines (at time of edit):** 835-854 (added Monster._maybe_warn_proximity_in_dark)
**After:** New helper that fires a one-shot "YOU HEAR SOMETHING SHUFFLING
NEARBY..." log message when the monster crosses into HEARING_RADIUS
while the player has no light, and resets when it leaves.
**Why:** Pairs with the no-light branch wiring above. Edge-triggered so
the log stays readable; uses the renamed HEARING_RADIUS constant.

---

## 2026-04-28 18:18 — Color hearing warning purple (Claude Opus 4.7)

**File:** ui/windows.py
**Lines (at time of edit):** 58-66 (rewritten as 58-80)
**Before:**
    def _default_color_for_message(self, text: str, fallback_color: str) -> str:
        """Return default line color, with custom overrides for warning lines."""
        warning_messages = {
            "YOU HEAR A MONSTER NEARBY!",
            "YOU'VE BEEN SPOTTED BY A MONSTER!",
        }
        if text.upper() in warning_messages:
            return ColorSettings.TEXT_LOSS
        return fallback_color
**After:**
    def _default_color_for_message(self, text: str, fallback_color: str) -> str:
        """... summary, Args, Returns ..."""
        warning_message_colors = {
            "YOU HEAR A MONSTER NEARBY!": ColorSettings.TEXT_LOSS,
            "YOU'VE BEEN SPOTTED BY A MONSTER!": ColorSettings.TEXT_LOSS,
            "YOU HEAR SOMETHING NEARBY, YOU AREN'T ALONE...": ColorSettings.PURPLE,
        }
        return warning_message_colors.get(text.upper(), fallback_color)
**Why:** Owner edited the darkness hearing warning text and wants it
rendered in purple so the new "passive presence detected" cue is
visually distinct from the red active-chase warnings. Set-of-strings
swapped for a dict so each warning can carry its own color without
adding more branches; existing two warnings stay TEXT_LOSS, new one
maps to PURPLE. Docstring expanded to satisfy the TESTING.md rule that
docstrings include summary, Args, Returns.

---

## 2026-04-28 18:30 — Monster AI: investigate last-known position after losing sight (Claude Opus 4.7)

**File:** core/sprites.py
**Lines (at time of edit):** 644-655 (Monster.__init__ added field)
**Before:**
    self.has_warned_player_of_proximity = False
**After:**
    self.has_warned_player_of_proximity = False
    # Grid (col, row) of the player at the moment they were last
    # spotted. While set and is_chasing is True, the monster keeps
    # advancing toward this tile after losing sight ...
    self.last_known_player_grid_pos: tuple[int, int] | None = None
**Why:** Backing field for the new "investigate last seen tile"
behavior. Documented invariant ("not chasing => no remembered tile")
explains why the clear in _stop_chasing is sufficient.

**File:** core/sprites.py
**Lines (at time of edit):** 708-762 (resolve_turn chase decision rewritten)
**Before:** Three-branch if/elif/else on (no light / spotted / else)
that called `_stop_chasing()` immediately the moment the player went
unlit or LOS was broken. Chase-step always used the live player delta.
**After:** Computes a `spotted_player` boolean once. Spotted refreshes
last_known_player_grid_pos every turn. When sight is lost mid-chase
and last_known is set, the monster keeps chasing and the chase-step
routes through `_chase_target_delta` to head for the remembered tile.
Reaching that tile triggers `_stop_chasing()` (which clears the
memory). Hearing warning still fires only in unlit play, but is now
positioned after the chase decision so it can fire mid-investigation
when the player kills their light to break LOS.
**Why:** Owner spec: "if the player is spotted by a monster, but then
the monster loses the player in the darkness, the monster should still
continue chasing but only until the player's last known position."
This is the standard roguelike "search/investigate" state. Player can
now use walls + light timing tactically to break a chase rather than
just outrun it. Spotted_player extracted as a local so the same
condition drives both the chase trigger and the chase-step routing.

**File:** core/sprites.py
**Lines (at time of edit):** 856-867 (_stop_chasing extended)
**Before:**
    self.is_chasing = False
    self.game.audio.play_normal_music()
**After:**
    self.is_chasing = False
    self.last_known_player_grid_pos = None
    self.game.audio.play_normal_music()
**Why:** Centralizes the last-known clear so every cancel path
(repellent, invisibility, give-up after reaching last-known, monster
loses interest) drops the memory automatically. Maintains the
invariant "not chasing => no remembered tile" without sprinkling clear
lines across resolve_turn.

**File:** core/sprites.py
**Lines (at time of edit):** ~792-822 (added Monster._chase_target_delta)
**After:** New helper that returns either the live player pixel delta
(when the monster currently sees the player) or the delta to the grid
cell stored in last_known_player_grid_pos (when investigating). The
None guard is defensive — by invariant the field is set whenever the
caller invokes this from a chasing state, but the fallback keeps the
monster moving instead of freezing if that invariant ever breaks.
**Why:** Lets the existing `_choose_primary_chase_step` stay unchanged
— it still picks one cardinal toward whatever delta you give it, so
all the new behavior lives in this small target-selection helper.

---

## 2026-04-28 18:42 — Bugfix: chase music clobbered by non-chasing monsters (Claude Opus 4.7)

**File:** core/sprites.py
**Lines (at time of edit):** 921-947 (Monster._stop_chasing)
**Before:**
    self.is_chasing = False
    self.last_known_player_grid_pos = None
    self.game.audio.play_normal_music()
**After:**
    self.is_chasing = False
    self.last_known_player_grid_pos = None
    any_other_monster_still_chasing = any(
        other is not self and other.is_chasing
        for other in self.game.monsters
    )
    if not any_other_monster_still_chasing:
        self.game.audio.play_normal_music()
**Why:** Owner reported the chase SFX firing but the chase music never
playing after the Bresenham LOS change. Root cause was a pre-existing
mismatch: is_chasing is per-monster, but play_chase_music /
play_normal_music are global. Each player turn iterates every monster
and calls resolve_turn on it. Before Bresenham, the orthogonal-only
LOS made it rare for any monster to spot the player, so the bug never
surfaced. Now that monsters spot the player at angles, monster A's
spotted-branch starts chase music, then monster B's "I don't see
them" branch immediately calls _stop_chasing → play_normal_music,
flipping music back. Guarding the play_normal_music call on "no other
monster is still chasing" leaves chase music playing as long as any
single monster is in pursuit.


---

## 2026-05-07 08:49 -04:00 � Add idle "look around" peek animation for the player

**File:** settings.py
**Lines (at time of edit):** 282-296 (added in PlayerSettings)
**Before:**
    class PlayerSettings:
        ANIMATION_SPEED = 1
        FLASH_CYCLE_FRAMES = 30
        FLASH_HALF_CYCLE = FLASH_CYCLE_FRAMES // 2
**After:**
    class PlayerSettings:
        ANIMATION_SPEED = 1
        FLASH_CYCLE_FRAMES = 30
        FLASH_HALF_CYCLE = FLASH_CYCLE_FRAMES // 2
        IDLE_ANIMATION_DELAY_MS = 4000
        IDLE_ANIMATION_FRAME_MS = 220
        IDLE_ANIMATION_SEQUENCE = (
            'center', 'left', 'center', 'right',
            'center', 'left', 'center', 'right', 'center',
        )
**Why:** Centralized tuning knobs for the new idle peek animation (delay before
it triggers, frame hold duration, and the peek pattern itself) so the values
are easy to tweak without touching gameplay code.

**File:** settings.py
**Lines (at time of edit):** 488-515 (modified PLAYER_SPRITES dict in AssetPaths)
**Before:**
    PLAYER_SPRITES keyed by (helmet_state, facing) with 6 entries.
**After:**
    PLAYER_SPRITES keyed by (helmet_state, facing, peek) with 10 entries; adds
    the four new player_helmet_up_{left,right}_looking_{left,right}.png frames
    used by the idle peek cycle. PLAYER alias updated to the new 3-tuple key.
**Why:** A third "peek" axis is needed so the renderer can swap to the
looking-left / looking-right variants during the idle animation.

**File:** core/sprites.py
**Lines (at time of edit):** 34-50 (modified Player.__init__)
**Before:**
    self.sprites typed as dict[tuple[str, str], ...]; base_image lookup used
    a 2-tuple (helmet_state, facing).
**After:**
    self.sprites typed as dict[tuple[str, str, str], ...]; new fields peek,
    idle_elapsed_ms, idle_frame_index, idle_frame_elapsed_ms, _idle_last_tick_ms.
    base_image lookup uses the new 3-tuple key.
**Why:** Adds the per-instance state required to track when the peek cycle
should start, which frame is active, and how long the current frame has held.

**File:** core/sprites.py
**Lines (at time of edit):** 562-573 (modified update_invisibility_visual)
**Before:**
    self.base_image = self.sprites[(self.helmet_state, self.facing)]
**After:**
    peek = self.peek if self.helmet_state == 'up' else 'center'
    self.base_image = self.sprites[(self.helmet_state, self.facing, peek)]
**Why:** Routes the active peek frame into the rendered sprite. Non-up helmet
states (cloak/repelled) only have center variants, so peek is forced to
'center' for them.

**File:** core/sprites.py
**Lines (at time of edit):** 600-647 (added reset_idle_animation, update_idle_animation; modified animate)
**Before:**
    animate() called only update_invisibility_visual at the end.
**After:**
    Adds reset_idle_animation() and update_idle_animation(). animate() now
    calls update_idle_animation() before update_invisibility_visual() so the
    new peek state feeds straight into sprite selection on the same frame.
**Why:** Implements the timed idle peek behavior using real-time pygame ticks
so the animation is FPS-independent; resets cleanly whenever the player moves
or a status effect changes the helmet.

**File:** main.py
**Lines (at time of edit):** 614-617 (added in advance_turn)
**Before:**
    self.map_memory.remember_visible_map_info()
    self.player.tick_status_effects()
**After:**
    self.map_memory.remember_visible_map_info()
    self.player.reset_idle_animation()
    self.player.tick_status_effects()
**Why:** Non-move actions (dig, light, repellent, etc.) still commit a turn but
don't set is_moving, so the idle timer needs an explicit reset here to keep
the peek animation from firing in the middle of rapid action sequences.


---

## 2026-05-07 09:05 -04:00 � Shorten idle peek animation to one left/right cycle

**File:** settings.py
**Lines (at time of edit):** 293-296 (modified PlayerSettings.IDLE_ANIMATION_SEQUENCE)
**Before:**
    IDLE_ANIMATION_SEQUENCE = (
        'center', 'left', 'center', 'right',
        'center', 'left', 'center', 'right', 'center',
    )
**After:**
    IDLE_ANIMATION_SEQUENCE = (
        'center', 'left', 'center', 'right', 'center',
    )
**Why:** User requested a shorter idle animation: one peek left and one peek
right per cycle instead of two of each.
