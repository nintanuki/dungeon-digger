# PRIORITY ORDER (STRICT)
1. Refactor / Clean Code
2. Documentation
3. Bug Fixes
4. Game Balance
5. New Features

Do NOT add new features until steps 1–4 are complete.

---

# CORE REFACTORING

Most of the architecture cleanup landed during the recent refactor. Remaining
follow-ups are state-ownership cleanups that were deliberately deferred.

- [ ] Move shop / treasure / level-transition state from `GameManager` attributes onto `IntermissionFlow` itself (it currently writes through `self.game.X = ...`).
- [ ] Move game-over / initials state from `GameManager` onto `ScoreLeaderboardManager`.
- [ ] Continue the docstring + comment polish on a per-file basis when something looks rough.

---

# PERFORMANCE

These are the bottlenecks worth attacking if browser (pygbag) framerate, low-end
hardware, or executable startup time becomes a concern. Ordered easiest-first.

- [ ] **Cache rendered HUD font surfaces.** `draw_ui_frames` re-renders `f"SCORE: {score}"`, `f"HIGH SCORE: {high}"`, `f"LEVEL {n}"`, and the dungeon-name line every frame. Cache each by its current text and only re-render on change.
- [ ] **Pre-bake the CRT scanline overlay.** `crt.create_crt_lines` draws scanlines onto the TV image every frame. Bake them once into a static surface; multiply that surface by the random alpha each frame instead of redrawing lines.
- [ ] **Cache `draw_grid_background` to an offscreen surface.** All 140 tiles are repainted every frame. Render once into a cached `Surface` and re-blit; invalidate only when a tile changes (dig, level load).
- [ ] **Cache the fog-of-war light mask by radius.** `draw_fog_of_war` allocates a fresh mask surface and draws ~`radius_px` concentric circles every frame (60 circles when fully lit). Memoize on `(radius_px,)` so it only rebuilds when `light_radius` changes — typically once per turn, not 60×/sec. Likely the biggest single win.
- [ ] **Precompute Bresenham line-of-sight points.** `DungeonLevel.get_line_points` builds a fresh list each call. For a fixed grid this can be cached per (start, end) pair, or replaced with a generator that visits cells without allocating.

---

# BUGS / ISSUES

- [ ] Area revealed by light sources in the minimap looks slightly too large (compare squares).

## Gameplay Bugs
- [ ] Player can pass through monster.
- [ ] Monster gets stuck between walls.
- [ ] Map drawing is incorrect / broken.
- [ ] Play found-gold/treasure sound AFTER dig sound (they currently overlap).
- [x] Check that we don't need `high_score.txt` now that we have `leaderboard.txt`. (Done — high score now derived from the top leaderboard entry; high_score.txt is no longer written.)
- [ ] Enemy line of sight doesn't seem to work diagonally.

## Visual / UX Bugs
- [ ] Text is blurry (font/rendering issue).
- [ ] Monster visibility issue (color blends with environment).
- [ ] CRT effect doesn't work properly when the game is in full screen. For now I disabled CRT when full screen until this gets resolved. Consider increasing the native resolution for when it's windowed, but then everything will have to be re-aligned and re-sized...

---

# GAMEPLAY BALANCE

## Difficulty
- [ ] Game is too hard early on.
- [ ] Some maps are overly punishing.
- [ ] Reduce frustration from "useless" loot.
- [ ] Make key detector more sensitive.
- [ ] Provide clues when monsters are near?

---

# CORE GAMEPLAY IMPROVEMENTS

## Monster Interaction
- [ ] Add temporary banish or other defensive option.

---

# EXISTING SYSTEMS TO COMPLETE

## Feedback Systems
- [ ] Create dedicated sound effect for lighting a lantern.
- [ ] Add sound effects to actions that are missing them.

---

# CONTENT & STRUCTURE

## Maps
- [ ] Adjust unfair layouts.
- [ ] Add more handcrafted maps.

---

# IDEAS (POST-CORE ONLY)

## Mechanics
- [ ] Dynamic monster variety (random sprites).
- [ ] Random obstacles (traps).

## Systems
- [ ] Dynamic music? (Jaws-style proximity system).

---

# DOCUMENTATION MAINTENANCE

Every pass that meaningfully changes a system must:

1. Update [docs/ARCHITECTURE.md](ARCHITECTURE.md) to reflect the new shape.
2. Append entries to [docs/CHANGELOG.md](CHANGELOG.md) per the format in that file.
3. Move completed items here from `[ ]` to `[x]` (do not delete — leave as a record).

---

# NEXT ACTIONABLE TASKS

- [ ] Prevent player movement into occupied monster tiles.
- [ ] Sequence dig → treasure audio so sounds do not overlap.

---

# NOTES

- Current foundation is solid (grid, movement, fog, digging all working).
- Light sources should not just be a radius; they should be blocked by walls (no seeing through walls).
- Create a special area in the UI for unique key items (symbols?) instead of tracking quantity in inventory sidebar.
- Remove the "[SPAWN] debug" message

# Notes & Ideas
- Make shopkeeper and NPCs drop hints.
- [x] Add save game feature. (Done — 10 named slots under saves/, auto-save runs after treasure conversion and before the shop, load drops the player into the pre-level shop so they can re-shop on reload, brand-new saves resume directly into level 1.)
- Maybe have an indicator or highlight on the item in the inventory window with the toggle, and group light sources.
- Figure out how the tutorial will work.
- With the addition of the "tutorial" dungeon and easier levels loaded at start, more dirt tiles = more treasure, meaning the player can buy the $10,000 invisibility cloak by level 2! Make it more expensive? The game is also more boring now that it starts with less "challenging" maps, just lots of digging in open space with low threat of monsters.
- Remove allowing A to start the game; must press START.
- [x] Remove "bulk buy" option. (Done — no more X / 5 keyboard or X-button controller bulk purchase; one press buys one item.)
- Get rid of the "tutorial" dungeon arena — it's boring, and the tutorial can play on any dungeon as long as it's not skipped.
- Add hard limit of 255 to each item for "retro" feel.
- Map name should only be reveal if play picks up map, magic map, or manages to explore every tile
- Repellent should not effect all monsters on the map at once when used, instead it should be an constant area of effect that follows the player, same radius as the lantern, and monsters will be repelled by this radius (consider drawing a purple foggy circle that shrinks over time?)
- coin sound should play for every beat in treasure exchange screen
- add sound effect for monster nearby warning (not the same as the chase sound)
- flip character sprite left and right

# Refactoring notes
- Add reset option for keyboard too (ESC?).
- Remove controls in "welcome message" now that you have a tutorial, add something more dramatic.