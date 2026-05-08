# Dungeon Digger — Manual Testing Checklist

Run this after a non-trivial change. Mental rules live in [.github/copilot-instructions.md](../.github/copilot-instructions.md); this file lists what to *do*. The strict refactoring rules that used to live here are now consolidated in copilot-instructions.

---

## Smoke test (every change)

```powershell
cd games/sponsor/original/dungeon-digger
python main.py
```

Or via the cabinet launcher: repo root → `python main.py` → **Mr. Navarro's Games → Original Games → Dungeon Digger**. Both entry paths must work.

1. **Boot.** Window opens at 800 × 600, titled "Dungeon Digger". No console errors.
2. **Title screen.** Menu options render. Selector cycles with arrows / D-pad / left analog stick.
3. **CRT overlay** is visible in windowed mode (intentionally disabled in fullscreen — known issue).

---

## NEW GAME flow

4. Pick **NEW GAME** → slot select screen shows 10 slots.
5. On an occupied slot, the **OVERWRITE** confirm dialog appears with `NO` highlighted (safe default).
6. On an empty slot or after confirm, the name-entry screen accepts 1–8 characters and auto-uppercases.
7. Confirming a name advances to the **TUTORIAL** prompt.
8. Choosing **PLAY** runs the tutorial cards; each card dismisses cleanly without the dismiss key also counting as a dig.
9. Choosing **SKIP TUTORIAL** drops directly into level 1.

## LOAD GAME flow

10. Pick **LOAD GAME**. Empty slots are non-selectable.
11. Selecting a slot with a non-fresh save drops into the **pre-level shop**. Exiting the shop re-rolls the next dungeon.
12. Selecting a brand-new (level-1, no progress) save drops directly into level 1.
13. **Delete**: on the Load Game screen, pressing X (or Delete) on an occupied slot opens a confirm dialog with `NO` highlighted. Confirming clears the slot.

---

## Gameplay turn coverage

14. **Movement.** WASD, arrows, and D-pad all move the player one tile per press.
15. **Wall block.** Player cannot walk into wall tiles; bumping a wall does not advance a turn.
16. **Dig empty tile** (Space / A). Turn advances; a dig sound plays.
17. **Dig loot tile.** Loot is collected; appropriate sound plays. (Known issue: gold/treasure sound currently overlaps with dig sound.)
18. **Light source** (F / B). Visibility radius increases for `light_turns_left` turns.
19. **Cycle light source** (Q/E or L1/R1). Selection moves through owned sources only.
20. **Detector** (X / X). Hint appears in message log.
21. **Repellent** (R / Y). Monsters within range cannot enter the player tile while active.
22. **Cloak** (C / L2). Player becomes invisible to monsters; helmet sprite changes to `down`.
23. **Player facing.** Walking left flips the sprite to `left`; walking right flips it to `right`. Vertical movement does not change facing.
24. **Idle peek animation.** Stand still with helmet up for ~10 seconds — the peek cycle plays (`center → left → center → right → center`). Any movement cancels it; the cycle repeats after another delay.

---

## Level completion

25. Find the key on the level. Picking it up updates the inventory and changes the door's border style.
26. Standing on the door and digging with the key in inventory triggers the **door-unlock sequence**.
27. **Treasure conversion** plays line-by-line.
28. **Auto-save** fires; message log shows "GAME SAVED."
29. **Shop** opens. Buying items reduces gold; Continue advances to the next dungeon transition card.
30. The new dungeon's name appears on the transition card before the next level loads.

## Monsters and death

31. Trigger a monster chase by lighting up. The monster pathfinds toward the player.
32. Standing on the monster's tile (without invisibility/repellent active) triggers a game over.
33. Game over screen appears; pressing Enter / Start returns to the title. **No save** is written.

## Final-dungeon win

34. Clearing the final dungeon shows the win screen, prompts for **3-letter initials**, and writes a leaderboard entry.
35. The save slot is **not overwritten** on win — it still points at the pre-final-dungeon shop.

---

## Global controls

36. `F11` / `Back` toggles fullscreen. CRT overlay disappears in fullscreen (intentional).
37. `R2` mute on controller toggles audio without flickering on a held trigger.
38. `Esc` quits cleanly.
39. Holding `Start + Back + L1 + R1` on a controller exits cleanly.
40. Closing the OS window quits cleanly.

---

## Failure-mode tests (when error-handling code is touched)

- Rename `assets/font/Pixeled.ttf`. Boot. The game should fail with a clear error.
- Move a player sprite asset out of `assets/graphics/player/`. Boot. The game should fail explicitly with the missing-file path.
- Corrupt a JSON save file under `saves/`. Open Load Game. The slot should display as occupied or be skipped — no crash.

---

## Settings-change tests

When [settings.py](../settings.py) is edited:

- Visually confirm the changed section reflects the new values (tile scale, light radius, animation timings, colors).
- Confirm no other section regressed.
- `grep` for the literal value to confirm no constants leaked back into `core/`, `systems/`, `ui/`, or `util/` files.

---

## Sign-off

- [ ] Smoke test passed.
- [ ] NEW GAME and LOAD GAME flows passed.
- [ ] Gameplay turn coverage passed.
- [ ] Monsters / death / win flows passed.
- [ ] Global controls passed.
- [ ] [docs/CHANGELOG.md](CHANGELOG.md) updated.
- [ ] [docs/ARCHITECTURE.md](ARCHITECTURE.md) updated if structure changed.
- [ ] [docs/TODO.md](TODO.md) updated if a roadmap item was completed.
