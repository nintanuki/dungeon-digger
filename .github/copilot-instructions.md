# Copilot Instructions for Dungeon Digger

These rules apply to **every** editor of this codebase, human or AI. They are not suggestions. Read this file before each session.

This game is a **standalone project**. It happens to live inside the Arcade Cabinet repo, but its code is agnostic to the launcher: running `python main.py` from this folder must always work on its own. Do not import launcher modules, do not assume the launcher exists, and do not edit files outside this folder from a Dungeon Digger change.

---

## Required reading order (before any change)

1. [README.md](../README.md) — what the project is and how to run it.
2. [docs/TODO.md](../docs/TODO.md) — current phase and roadmap.
3. [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) — how the code actually works.
4. [docs/CHANGELOG.md](../docs/CHANGELOG.md) — most recent changes, so you know the current state.
5. The source files relevant to your task.

If a question is asked about *why* code was written a certain way, that is a request for an **explanation**, not a request for a code change. Do not modify code unless the user explicitly asks for a change.

---

## Required actions (after any change)

- Append an entry to [docs/CHANGELOG.md](../docs/CHANGELOG.md) following the format defined at the top of that file (ISO 8601 timestamp with timezone, file path, line numbers at time of edit, before/after code, why, and editor name including the AI model used).
- If your change altered how a system works, update the matching section of [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md). Out-of-date architecture docs are worse than none.
- If your change completes or adds a roadmap item, update [docs/TODO.md](../docs/TODO.md) (mark `[x]`, do not delete).
- Run the manual smoke checks in [docs/TESTING.md](../docs/TESTING.md).

---

## Code style

- All Python code must be PEP-8 compliant.
- Less code is better; clean and readable is best.
- Prefer clear names over short ones. New class and function names must clearly describe their purpose.
- Do not change function or variable names unless the role has *completely* changed.
- Keep code free of dead imports, unused variables, unused functions, and legacy code.

## Architecture rules

- `GameManager` ([main.py](../main.py)) must stay thin. Offload responsibilities to dedicated managers (`AudioManager`, `SaveManager`, `ScoreLeaderboardManager`, `IntermissionFlow`, `LevelLoader`, `TutorialManager`, `RenderManager`).
- Classes should communicate through `GameManager` where possible. Avoid systems reaching directly into each other.
- Keep middlemen minimal: if A calls B and B only calls C, have A call C directly.
- All constants live in [settings.py](../settings.py). **No magic numbers anywhere else.** When adding a constant, include a comment explaining its units and effect.
- Prefer adding a new `*Settings` class in `settings.py` over expanding an existing one when the new field is not closely related to its neighbors.
- Asset paths live in `AssetPaths`. Do not hard-code asset filenames in gameplay or rendering code.

## File and function layout

- Inside a class, group functions by role (boot/setup, input, turn resolution, animation, render, lifecycle).
- `update` and `run` go **last** and should only call other functions on the class.
- Separate logical sections inside a file with an all-caps banner comment, exactly this style:

  ```python
      # -------------------------
      # SECTION NAME
      # -------------------------
  ```

  Match the leading indentation of the surrounding class body. Keep the dashes the same length and the name in ALL CAPS.

## Comments and docstrings

- Every class and function must have a docstring with a one-line summary, plus `Args:` / `Returns:` blocks when applicable.
- Do not remove docstrings. Update them in place if behavior changes.
- Do not remove comments unless they are inaccurate; prefer updating them.
- Comments must explain **why**, not just what.
- Do not leave comments noting that a change was made, unless they explain a non-obvious bug fix or unconventional code.

## UI text

- ALL text displayed to the player in-game (HUD labels, message log lines, menu options, end-game screens) must be **ALL CAPS**. The pixel font (`Pixeled`) is designed for caps-style retro display.
- Documentation files stay in normal sentence case.

## Save and persistence rules

- Save writes happen exactly **once per cleared dungeon**, between treasure conversion and the shop. Do not add ad-hoc save calls elsewhere.
- Death does not save. Final-dungeon clear does not save (slot stays pointing at the pre-final-dungeon shop).
- Save file format is JSON under `saves/`. Bumping the schema requires updating `SaveManager` so old saves either migrate or fail gracefully.
- Leaderboard writes happen only on a winning run.

---

## Mental testing checklist (run after major changes)

- The game launches (`python main.py`) without console errors.
- Title screen → NEW GAME → slot select → name entry → tutorial prompt path works end-to-end.
- LOAD GAME from a saved slot drops into the pre-level shop (or level 1 for a fresh save).
- Movement (WASD / arrows / D-pad), Dig (Space / A), Light (F / B), Repellent (R / Y), Detector (X / X), Cloak (C / L2), Light cycle (Q+E / L1+R1) all respond.
- Player sprite faces the last horizontal direction moved; idle "peek" animation plays after standing still.
- Monster turn resolves after each player action; dying ends the run; opening the door with a key clears the level.
- Shop, treasure conversion, and auto-save all run between levels.
- `F11` / `Back` toggles fullscreen; `Esc` and the controller quit combo both exit cleanly.
- No new magic numbers leaked outside `settings.py`.

For the actionable run-through, see [docs/TESTING.md](../docs/TESTING.md).
