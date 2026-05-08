import os
import pygame
import sys

# Resolve relative asset paths from this game's folder so standalone runs
# (python main.py) and launcher runs behave the same regardless of cwd.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

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

class GameManager:
    """Coordinate game state, flow, rendering phases, and input orchestration."""

    def __init__(self, start_fullscreen: bool = False):
        """Initialize runtime systems, persistent state, and the first dungeon level.

        Args:
            start_fullscreen: Whether to launch directly in fullscreen mode.
        """
        pygame.init()
        self.screen = pygame.display.set_mode((ScreenSettings.RESOLUTION), pygame.SCALED)
        pygame.display.set_caption(ScreenSettings.TITLE)
        if start_fullscreen:
            pygame.display.toggle_fullscreen()
        self.clock = pygame.time.Clock()

        self.setup_controllers()
        self.load_assets()
        self.dungeon = DungeonLevel(self.scaled_dirt_tiles)
        self.all_sprites = pygame.sprite.Group()
        self.audio = AudioManager()
        self.score_manager = ScoreLeaderboardManager(self)
        self.intermission = IntermissionFlow(self)
        self.save_manager = SaveManager(self)
        self.game_active = False
        self.game_result = None
        self.score = 0
        self.high_score = self.score_manager.load_high_score()
        self.leaderboard = self.score_manager.load_leaderboard()
        # Identity of the active save: name shown to the player and the
        # 1-indexed slot the auto-save will write into. Both are populated
        # when the player picks NEW GAME or LOAD GAME and remain set for
        # the rest of the run. None means no save is bound (e.g. before the
        # title flow has resolved).
        self.player_name = ""
        self.active_save_slot: int | None = None
        self.level_order = list(LEVEL_DUNGEON_ORDER)
        self.level_numbers = sorted(DUNGEON_CONFIG.level_difficulty_by_number.keys())
        self.current_level_index = 0
        self.pending_level_index = 0
        self.transition_label = ""
        self.transition_end_time = 0
        self.pending_level_load = False
        self.message_success_border_until = 0
        self.r2_trigger_is_pressed = False

        # Tutorial system. Constructed lazily in start_gameplay_from_title when
        # the player chooses PLAY. Stays None for SKIP TUTORIAL runs.
        self.tutorial: TutorialManager | None = None

        self.ui_state = 'title'
        self.title_menu_index = 0
        self.newgame_prompt_active = False
        self.newgame_prompt_index = 0
        # State for the slot-select / overwrite-confirm / name-entry / delete
        # confirm screens introduced with the save system. slot_select_index
        # is the highlighted row on either of the slot-select screens (0..9).
        # confirm_index drives NO=0 / YES=1 selections in both confirm
        # dialogs, defaulting to NO so an accidental confirm is harmless.
        # confirm_target_slot remembers which slot a confirm dialog is
        # acting on, so the dialogs themselves are stateless. The two
        # previous_left_stick_* fields are edge-detection memory for analog
        # navigation, modeled on the existing r2_trigger_is_pressed pattern.
        self.slot_select_index = 0
        self.name_entry_buffer = ""
        self.confirm_index = 0
        self.confirm_target_slot = 0
        self.previous_left_stick_x = 0.0
        self.previous_left_stick_y = 0.0
        self.npcs: list = []

        # State for game over flow and leaderboard entry.
        self.game_over_message_complete_time = 0
        self.game_over_prompt_start_time = 0
        self.pending_leaderboard_score = 0
        self.initials_entry = "AAA"
        self.initials_index = 0
        self.intermission.initialize_state()

        # Pre-create the fog surface to avoid doing it every frame during rendering.
        self.fog_surface = pygame.Surface((UISettings.ACTION_WINDOW_WIDTH, UISettings.ACTION_WINDOW_HEIGHT), pygame.SRCALPHA)

        # -------- UI windows --------
        self.message_log = MessageLog(self)
        self.inventory_window = InventoryWindow(self)
        self.map_window = MapWindow(self)
        self.map_memory = None

        # -------- Post-processing --------
        self.full_screen = False
        self.crt = CRT(self.screen)

        # -------- Rendering facade --------
        self.render = None

        # LevelLoader needs dungeon + all_sprites alive — both built above.
        self.level_loader = LevelLoader(self)
        self.level_loader.load_level()
        self.audio.stop_music()

    # -------------------------
    # BOOT / SETUP
    # -------------------------

    def setup_controllers(self) -> None:
        """Cache currently-connected controllers so quit-combo and event polling are cheap."""
        pygame.joystick.init()
        self.connected_joysticks = [
            pygame.joystick.Joystick(index)
            for index in range(pygame.joystick.get_count())
        ]

    def load_assets(self) -> None:
        """Load and pre-scale the dirt, dug, and wall tile surfaces used by every level."""
        self.scaled_dirt_tiles = []
        for dirt_path in AssetPaths.DIRT_TILES:
            dirt_surf = pygame.image.load(dirt_path).convert_alpha()
            self.scaled_dirt_tiles.append(
                pygame.transform.scale(dirt_surf, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))
            )

        dug_surf = pygame.image.load(AssetPaths.DUG_TILE).convert_alpha()
        self.scaled_dug_tile = pygame.transform.scale(
            dug_surf, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE)
        )

        wall_surf = pygame.image.load(AssetPaths.WALL_TILE).convert_alpha()
        self.scaled_wall_tile = pygame.transform.scale(
            wall_surf, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE)
        )

    def reset_game(self):
        """
        Restart the game by replacing the current GameManager instance
        with a brand new one.

        This is safer than trying to manually reset every subsystem,
        because it reuses the same startup path the game already uses
        when it first launches.
        """
        current_surface = pygame.display.get_surface()
        was_fullscreen = bool(current_surface and (current_surface.get_flags() & pygame.FULLSCREEN))

        new_game_manager = GameManager(start_fullscreen=was_fullscreen)
        new_game_manager.run()
        sys.exit()

    def close_game(self) -> None:
        """Close the game process cleanly."""
        pygame.quit()
        sys.exit()

    def quit_combo_pressed(self) -> bool:
        """Return True if START + SELECT + L1 + R1 are held on any controller."""
        required_buttons = InputSettings.JOY_BUTTON_QUIT_COMBO
        for joystick in self.connected_joysticks:
            if all(joystick.get_button(button) for button in required_buttons):
                return True
        return False

    @property
    def current_level_number(self) -> int:
        """Return the configured level number for the current level index.

        Returns:
            Current configured level number.
        """
        if not self.level_numbers:
            return self.current_level_index
        return self.level_numbers[self.current_level_index]

    @property
    def is_transitioning(self) -> bool:
        """Report whether a level transition card is currently active.

        Returns:
            True while transition timing is in progress.
        """
        return pygame.time.get_ticks() < self.transition_end_time

    def start_gameplay_from_title(self, skip_tutorial: bool = False) -> None:
        """
        Leave title screen and begin active gameplay at level 1.

        current_level_index is a 0-indexed position into level_numbers, so
        index 0 corresponds to level 1. Earlier code used 1 here, which
        silently skipped level 1 entirely and dropped the player into
        level 2 on a fresh run.

        Args:
            skip_tutorial: When True, skip the tutorial and start at level 1.
        """
        self.audio.play('menu_select')
        self.current_level_index = 0
        self.pending_level_index = 0
        player_progress = self.level_loader.capture_player_progress()
        self.level_loader.load_level(player_progress)
        if not skip_tutorial:
            self.tutorial = TutorialManager(self)
        else:
            self.tutorial = None
        self.ui_state = 'playing'
        self.game_active = True
        self.audio.play_random_bgm()

    def start_gameplay_from_save(self, save_data: dict) -> None:
        """Resume an existing save.

        Two cases:

        - Brand-new save (next_level == first level number): the slot was
          reserved by NEW GAME but the player has not cleared anything
          yet. Drop them into level 1 gameplay directly — there is no
          pre-level shop because no treasure has been converted.

        - Post-progress save (next_level > first level number): the
          player has cleared at least one dungeon. Drop them into the
          shop that precedes the saved level. The just-completed
          dungeon is loaded behind the shop overlay only so the player
          object has the saved inventory; the player never sees it.

        Args:
            save_data: Dict returned by save_manager.load_slot. Must
                contain player_name, next_level, inventory,
                discovered_items, score, and slot_id.
        """
        self.audio.play('menu_select')

        valid_levels = self.level_numbers or [1]
        first_level = valid_levels[0]
        last_level = valid_levels[-1]

        # Clamp into the valid range. A save written before the level
        # schedule was extended (or somehow with an out-of-range value)
        # should still load: treat it as the nearest valid level.
        next_level = int(save_data.get('next_level', first_level))
        next_level = max(first_level, min(next_level, last_level))
        # level_numbers is contiguous and starts at first_level, so the
        # 0-indexed position is just (level - first_level).
        next_level_index = next_level - first_level

        self.player_name = save_data.get('player_name', '')
        self.active_save_slot = save_data.get('slot_id')
        self.score = int(save_data.get('score', 0))
        self.pending_level_index = next_level_index

        is_brand_new_save = next_level == first_level
        # On a brand-new save the player will play next_level directly,
        # so current_level_index points at it. On a post-progress save
        # current_level_index points at the just-completed level so the
        # HUD shows that number while the shop is up; complete_shop_phase
        # will then advance current_level_index to pending_level_index.
        if is_brand_new_save:
            self.current_level_index = next_level_index
        else:
            self.current_level_index = max(0, next_level_index - 1)

        player_progress = {
            'inventory': dict(save_data.get('inventory', {})),
            'discovered_items': set(save_data.get('discovered_items', set())),
        }
        self.level_loader.load_level(player_progress)

        # Tutorial is intentionally skipped on load. Tracking which cards
        # the player has already seen would add bookkeeping to every save;
        # for now a reloaded run is treated as past the tutorial.
        self.tutorial = None
        self.ui_state = 'playing'
        self.game_active = True
        self.audio.play_random_bgm()

        if is_brand_new_save:
            # No shop precedes level 1, so go straight to gameplay.
            return

        self.intermission.start_shop_phase()

    def handle_title_menu_move(self, direction: int) -> None:
        """Move the cursor up (-1) or down (+1) in vertical menu states.

        Covers title, newgame_prompt, and the two slot-select screens. The
        confirm dialogs (overwrite, delete) navigate horizontally instead
        and are handled by handle_confirm_move.

        Args:
            direction: -1 for up, +1 for down.
        """
        if self.ui_state == 'title':
            options_count = 3  # LOAD GAME, NEW GAME, OPTIONS
            new_index = (self.title_menu_index + direction) % options_count
            if new_index != self.title_menu_index:
                self.title_menu_index = new_index
                self.audio.play('menu_move')
        elif self.ui_state == 'newgame_prompt':
            options_count = 2  # NO (START TUTORIAL), YES
            new_index = (self.newgame_prompt_index + direction) % options_count
            if new_index != self.newgame_prompt_index:
                self.newgame_prompt_index = new_index
                self.audio.play('menu_move')
        elif self.ui_state in ('slot_select_new', 'slot_select_load'):
            options_count = GameSettings.MAX_SAVE_SLOTS
            new_index = (self.slot_select_index + direction) % options_count
            if new_index != self.slot_select_index:
                self.slot_select_index = new_index
                self.audio.play('menu_move')

    def handle_confirm_move(self, direction: int) -> None:
        """Move the NO/YES cursor in the overwrite or delete confirm dialog.

        Args:
            direction: -1 for left (toward NO), +1 for right (toward YES).
        """
        if self.ui_state not in ('overwrite_confirm', 'delete_confirm'):
            return
        new_index = (self.confirm_index + direction) % 2
        if new_index != self.confirm_index:
            self.confirm_index = new_index
            self.audio.play('menu_move')

    def handle_back_press(self) -> None:
        """Step one screen back in the menu hierarchy.

        Maps each save-flow ui_state to its parent. No-op on screens with
        no defined back step (title, gameplay, etc.).
        """
        if self.ui_state in ('slot_select_new', 'slot_select_load'):
            self.ui_state = 'title'
            self.audio.play('menu_select')
            return
        if self.ui_state == 'overwrite_confirm':
            self.ui_state = 'slot_select_new'
            self.audio.play('menu_select')
            return
        if self.ui_state == 'name_entry':
            # Send the player back to the slot picker rather than all the
            # way to title; if they decide not to start a new save, B
            # again pops them back to title.
            self.ui_state = 'slot_select_new'
            self.name_entry_buffer = ""
            self.audio.play('menu_select')
            return
        if self.ui_state == 'delete_confirm':
            self.ui_state = 'slot_select_load'
            self.audio.play('menu_select')
            return

    def handle_delete_press(self) -> None:
        """Open the delete-confirm dialog for the highlighted load slot.

        Only meaningful on slot_select_load with the cursor on an occupied
        slot. Empty slots produce a boundary sound to signal the action
        was rejected.
        """
        if self.ui_state != 'slot_select_load':
            return
        slot_id = self.slot_select_index + 1
        if not self.save_manager.is_slot_occupied(slot_id):
            self.audio.play('boundary')
            return
        self.confirm_target_slot = slot_id
        self.confirm_index = 0  # default to NO so an accidental confirm is harmless
        self.ui_state = 'delete_confirm'
        self.audio.play('menu_select')

    def commit_name_entry(self) -> None:
        """Finalize a typed name and advance to the tutorial prompt.

        The buffer is sanitized (uppercase, whitelist, max length). An
        empty result keeps the player on name_entry with a boundary
        sound — there's nothing meaningful to commit. On success we bind
        the active save slot and player name on the GameManager, write
        the slot's save file immediately so the slot is reserved at
        level 1 even if the player quits before clearing a level, then
        route to newgame_prompt to ask the tutorial question.
        """
        if self.ui_state != 'name_entry':
            return
        sanitized = self.save_manager.sanitize_name(self.name_entry_buffer)
        if not sanitized:
            self.audio.play('boundary')
            return
        self.player_name = sanitized
        self.active_save_slot = self.confirm_target_slot

        # Reserve the slot on disk now. Without this, the save file would
        # only appear after the first level clear and a player who quit
        # mid-level-1 would find their slot empty on return.
        first_level = self.level_numbers[0] if self.level_numbers else 1
        self.save_manager.save_slot(
            slot_id=self.active_save_slot,
            player_name=self.player_name,
            next_level=first_level,
            inventory=self.player.inventory,
            discovered_items=self.player.discovered_items,
            score=0,
        )

        self.name_entry_buffer = ""
        self.ui_state = 'newgame_prompt'
        self.newgame_prompt_index = 0
        self.audio.play('menu_select')

    def handle_name_entry_keypress(self, event) -> None:
        """Update the name entry buffer in response to one keyboard event.

        Accepts A-Z, 0-9, and space (auto-uppercased), backspace to delete
        the trailing character (or step back when the buffer is empty),
        Enter to commit, and Escape to exit the game. Everything else is
        ignored.

        Args:
            event: pygame.KEYDOWN event for the name entry screen.
        """
        if self.ui_state != 'name_entry':
            return
        if event.key == pygame.K_BACKSPACE:
            if self.name_entry_buffer:
                self.name_entry_buffer = self.name_entry_buffer[:-1]
                self.audio.play('menu_move')
            else:
                # Empty buffer + Backspace steps back to the slot picker.
                # Without this, the keyboard had no "back" affordance now that
                # ESC always exits the game.
                self.handle_back_press()
            return
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.commit_name_entry()
            return
        if event.key == pygame.K_ESCAPE:
            # ESC during name entry still exits to the launcher to keep the
            # exit shortcut consistent with every other game state.
            self.close_game()
            return
        # event.unicode is the keystroke's typed character with shift /
        # caps applied. Filter against the SaveManager whitelist and cap
        # at the configured length.
        char = (event.unicode or '').upper()
        if not char or char not in self.save_manager.ALLOWED_NAME_CHARS:
            return
        if len(self.name_entry_buffer) >= GameSettings.MAX_PLAYER_NAME_LENGTH:
            self.audio.play('boundary')
            return
        self.name_entry_buffer += char
        self.audio.play('menu_move')

    def handle_start_press(self) -> None:
        """Handle Start/Enter based on top-level UI state."""
        if self.ui_state == 'title':
            if self.title_menu_index == 0:
                # LOAD GAME — open the load-slot picker. Default the
                # cursor to the first occupied slot so the player isn't
                # scrolling past empties on a fresh title return.
                self.ui_state = 'slot_select_load'
                summaries = self.save_manager.list_slots()
                first_occupied = next(
                    (s['slot_id'] for s in summaries if s['occupied']),
                    1,
                )
                self.slot_select_index = first_occupied - 1
                self.audio.play('menu_select')
                return
            elif self.title_menu_index == 1:
                # NEW GAME — open the new-game slot picker. Default the
                # cursor to slot 1 so the player sees the slot list from
                # the top.
                self.ui_state = 'slot_select_new'
                self.slot_select_index = 0
                self.audio.play('menu_select')
                return
            elif self.title_menu_index == 2:
                # OPTIONS (not implemented)
                self.audio.play('menu_select')
                # Placeholder: do nothing
                return

        if self.ui_state == 'slot_select_new':
            slot_id = self.slot_select_index + 1
            self.confirm_target_slot = slot_id
            if self.save_manager.is_slot_occupied(slot_id):
                # Occupied slot — make the player explicitly confirm the
                # overwrite so a misclick doesn't blow away an old save.
                self.ui_state = 'overwrite_confirm'
                self.confirm_index = 0
            else:
                self.ui_state = 'name_entry'
                self.name_entry_buffer = ""
            self.audio.play('menu_select')
            return

        if self.ui_state == 'slot_select_load':
            slot_id = self.slot_select_index + 1
            save = self.save_manager.load_slot(slot_id)
            if save is None:
                # Either empty or corrupt — neither is loadable. Boundary
                # sound signals the rejection without changing state.
                self.audio.play('boundary')
                return
            save['slot_id'] = slot_id
            self.start_gameplay_from_save(save)
            return

        if self.ui_state == 'overwrite_confirm':
            if self.confirm_index == 1:  # YES
                self.ui_state = 'name_entry'
                self.name_entry_buffer = ""
                self.audio.play('menu_select')
            else:  # NO
                self.ui_state = 'slot_select_new'
                self.audio.play('menu_select')
            return

        if self.ui_state == 'delete_confirm':
            if self.confirm_index == 1:  # YES
                self.save_manager.delete_slot(self.confirm_target_slot)
                self.audio.play('menu_select')
            else:
                self.audio.play('menu_select')
            self.ui_state = 'slot_select_load'
            return

        if self.ui_state == 'name_entry':
            # Enter committing the name is also handled in
            # handle_name_entry_keypress for the keyboard path; this
            # branch covers Start on a controller (kept aspirational —
            # full controller-side text entry is a future task).
            self.commit_name_entry()
            return

        if self.ui_state == 'newgame_prompt':
            if self.newgame_prompt_index == 0:
                # NO (START TUTORIAL)
                self.start_gameplay_from_title(skip_tutorial=False)
            else:
                # YES
                self.start_gameplay_from_title(skip_tutorial=True)
            return

        if self.ui_state == 'game_over' and self.score_manager.can_continue_from_game_over():
            self.score_manager.continue_from_game_over()
            return

        if self.ui_state == 'enter_initials':
            self.score_manager.submit_initials_entry()
            return

        if self.ui_state == 'leaderboard':
            self.reset_game()

    def finish_game(self, result: str) -> None:
        """End the current run and freeze world updates.

        High-score persistence is no longer triggered here. Wins promote the
        score through ScoreLeaderboardManager.add_leaderboard_entry once the
        player submits their initials; losses leave the leaderboard
        untouched, so the displayed high score stays correct when the GAME
        OVER overlay appears.

        Args:
            result: Either "win" (final door cleared) or "loss" (caught by a monster).
        """
        self.game_active = False
        self.game_result = result
        self.ui_state = 'game_over'
        if self.map_memory is not None:
            # Reveal the entire map so the death/victory screen is informative.
            self.map_memory.reveal_full_terrain_memory()
        self.pending_leaderboard_score = self.score
        self.game_over_message_complete_time = 0
        self.game_over_prompt_start_time = 0
        self.audio.stop_music()

    # -------------------------
    # TURN RESOLUTION
    # -------------------------

    def _trigger_npc_interaction(self, npc) -> None:
        """Give the player a random loot drop from an NPC and fade the NPC out."""
        self.log_message("IT\'S DANGEROUS TO GO ALONE! TAKE THIS!")
        found_item, amount = self.dungeon.roll_random_loot()
        loot.resolve_pickup(self, found_item, amount)
        npc.fade_pending = True
        self.npcs.remove(npc)

    def advance_turn(self):
        """
        Resolve one world step after the player commits to an action.

        This is where time passes in the dungeon: temporary effects tick down,
        monsters respond, and loss conditions are checked. Keeping that logic
        together helps the game stay consistently turn-based.
        """

        if not self.game_active:
            return

        self.map_memory.remember_visible_map_info()

        # Any committed action restarts the idle peek timer so the look-around
        # animation only plays after a real lull, not between rapid actions.
        self.player.reset_idle_animation()

        # All temporary status timers (light radius, repellent, invisibility,
        # cloak cooldown) belong to the player and tick themselves.
        self.player.tick_status_effects()

        # Check NPC adjacency: trigger interaction when player moves to a tile adjacent to an NPC.
        if self.player.is_moving:
            dest_col, dest_row = coords.screen_to_grid(
                self.player.target_pos.x, self.player.target_pos.y)
            for npc in list(self.npcs):
                npc_col, npc_row = coords.screen_to_grid(npc.position.x, npc.position.y)
                if abs(dest_col - npc_col) + abs(dest_row - npc_row) == 1:
                    self._trigger_npc_interaction(npc)

        for monster in self.monsters:
            monster.resolve_turn()

        # Remove any NPC that a monster has landed on.
        for monster in self.monsters:
            dest = monster.target_pos if monster.is_moving else monster.position
            m_col, m_row = coords.screen_to_grid(dest.x, dest.y)
            for npc in list(self.npcs):
                npc_col, npc_row = coords.screen_to_grid(npc.position.x, npc.position.y)
                if m_col == npc_col and m_row == npc_row:
                    npc.kill()
                    self.npcs.remove(npc)

        self.check_player_caught_by_monster()

        # Let the tutorial decide whether to surface its next card now that
        # the world has settled for this turn.
        if self.tutorial is not None:
            self.tutorial.on_turn_end()

    def check_player_caught_by_monster(self) -> bool:
        """Return True and end the game if any monster occupies the player's tile."""
        if not self.game_active:
            return False

        if self.player.is_invisible():
            return False

        for monster in self.monsters:
            if self.player.position == monster.position:
                self.log_message("YOU WERE CAUGHT BY THE MONSTER!")
                self.audio.play('scream')
                self.finish_game("loss")
                return True

        return False

    @property
    def is_busy(self):
        """Centralized check to see if the game is currently animating."""
        return (self.player.is_moving or
                any(monster.is_moving for monster in self.monsters) or
                self.message_log.is_typing)

    # -------------------------
    # UI PASS-THROUGHS
    # -------------------------

    def log_message(self, text, type_speed=None):
        """The central hub for all game objects to send text to the UI."""
        self.message_log.add_message(text, type_speed=type_speed)

    def notify_tutorial(self, event: str, **kwargs) -> None:
        """Forward a game-side event to the tutorial system if it exists.

        No-op when the tutorial isn't active (SKIP TUTORIAL run, or already
        torn down). Game-side call sites can call this unconditionally.
        """
        if self.tutorial is not None:
            self.tutorial.notify(event, **kwargs)

    # -------------------------
    # MAIN LOOP
    # -------------------------

    def _tick_between_level_flow(self) -> None:
        """Advance level-transition, door-unlock, treasure-conversion, and game-over timers."""
        if self.ui_state == 'playing':
            self.intermission.update_level_transition()
            self.intermission.update_door_unlock_sequence()
            self.intermission.update_treasure_conversion()
        self.score_manager.update_game_over_flow()

    def _process_events(self) -> None:
        """Drain pygame's event queue and dispatch by event type."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close_game()
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            elif event.type == pygame.JOYBUTTONDOWN:
                self._handle_joybuttondown(event)
            elif event.type == pygame.JOYHATMOTION:
                self._handle_joyhatmotion(event)
            elif event.type == pygame.JOYAXISMOTION:
                self._handle_joyaxismotion(event)

    def _dispatch_menu_navigate(self, dx: int, dy: int) -> None:
        """Centralized menu nav dispatch shared by D-pad and analog stick.

        handle_title_menu_move and handle_confirm_move both gate on
        ui_state internally, so this dispatcher is a thin "vertical or
        horizontal" router. Either coordinate may be zero; both being
        zero is a no-op.

        Args:
            dx: -1 for left, +1 for right, 0 for none.
            dy: -1 for up, +1 for down, 0 for none.
        """
        if dy != 0:
            self.handle_title_menu_move(dy)
        if dx != 0:
            self.handle_confirm_move(dx)

    def _handle_keydown(self, event) -> None:
        """Route one keyboard press to the appropriate UI/gameplay handler."""
        # F11 fullscreen toggle is global and intentionally falls through so
        # other handlers still see the press.
        if event.key == pygame.K_F11:
            pygame.display.toggle_fullscreen()
            self.full_screen = not self.full_screen

        # While a tutorial card is up it consumes ALL keyboard input so the
        # player can't accidentally play through the overlay.
        if (self.tutorial is not None and self.tutorial.is_blocking):
            self.tutorial.handle_event(event)
            return

        # Name entry consumes all keyboard input so typed letters never
        # also act as gameplay shortcuts. handle_name_entry_keypress
        # routes Enter / Esc / Backspace / character input itself.
        if self.ui_state == 'name_entry':
            self.handle_name_entry_keypress(event)
            return

        if self.ui_state in ('title', 'newgame_prompt', 'slot_select_new', 'slot_select_load'):
            if event.key in (pygame.K_UP, pygame.K_w):
                self.handle_title_menu_move(-1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.handle_title_menu_move(1)

        # Confirm dialogs use horizontal nav for NO/YES selection.
        if self.ui_state in ('overwrite_confirm', 'delete_confirm'):
            if event.key == pygame.K_LEFT:
                self.handle_confirm_move(-1)
            elif event.key == pygame.K_RIGHT:
                self.handle_confirm_move(1)

        # ESC always exits the game and returns to the arcade launcher,
        # matching the L1+R1+START+SELECT controller combo. Save-flow menus
        # still step backward via the controller B button (handled in
        # _handle_joybuttondown) and via the BACKSPACE key below.
        if event.key == pygame.K_ESCAPE:
            self.close_game()

        # BACKSPACE preserves the previous "step back through save-flow menus"
        # behavior on the keyboard now that ESC exits the game outright.
        if event.key == pygame.K_BACKSPACE:
            self.handle_back_press()

        # Delete (or X) on the load picker opens the delete-confirm dialog.
        if event.key in (pygame.K_DELETE, pygame.K_x) and self.ui_state == 'slot_select_load':
            self.handle_delete_press()

        if self.in_shop_phase:
            self.intermission.handle_shop_event(event)

        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.handle_start_press()

        self.score_manager.handle_initials_event(event)
        # Light-source cycling lives on the player; gameplay-state gating is
        # handled inside Player.handle_event itself.
        self.player.handle_event(event)

    def _handle_joybuttondown(self, event) -> None:
        """Route one controller button press."""
        # Catch the multi-button quit chord on press for instant response;
        # the outer per-frame check covers held-state quits.
        if self.quit_combo_pressed():
            self.close_game()

        # BACK is the global fullscreen toggle and falls through.
        if event.button == InputSettings.JOY_BUTTON_BACK:
            pygame.display.toggle_fullscreen()
            self.full_screen = not self.full_screen

        if (self.tutorial is not None and self.tutorial.is_blocking):
            self.tutorial.handle_event(event)
            return

        if self.in_shop_phase:
            self.intermission.handle_shop_event(event)

        if event.button in (InputSettings.JOY_BUTTON_START, InputSettings.JOY_BUTTON_A):
            self.handle_start_press()

        # B steps back through save-flow menus; no-op outside those states
        # so the in-game LIGHT binding on B is unaffected.
        if event.button == InputSettings.JOY_BUTTON_B:
            self.handle_back_press()

        # X opens the delete-confirm dialog from the load picker; no-op
        # otherwise, leaving the in-game KEY DETECTOR binding intact.
        if event.button == InputSettings.JOY_BUTTON_X:
            self.handle_delete_press()

        self.player.handle_event(event)
        self.score_manager.handle_initials_event(event)

    def _handle_joyhatmotion(self, event) -> None:
        """Route a D-pad direction event for menus."""
        if self.ui_state in ('title', 'newgame_prompt', 'slot_select_new', 'slot_select_load'):
            _, hat_y = event.value
            if hat_y == 1:
                self.handle_title_menu_move(-1)
            elif hat_y == -1:
                self.handle_title_menu_move(1)

        if self.ui_state in ('overwrite_confirm', 'delete_confirm'):
            hat_x, _ = event.value
            if hat_x == -1:
                self.handle_confirm_move(-1)
            elif hat_x == 1:
                self.handle_confirm_move(1)

        if self.in_shop_phase:
            self.intermission.handle_shop_event(event)

        self.score_manager.handle_initials_event(event)

    def _handle_joyaxismotion(self, event) -> None:
        """Route axis events: R2 mute toggle and left-stick menu navigation.

        The left analog stick mirrors the D-pad for menu navigation. We
        edge-trigger on threshold crossings (modeled on the existing R2
        pattern) so a single push registers a single nav step rather
        than continuous repeats while the stick is held.
        """
        if event.axis == InputSettings.JOY_AXIS_R2:
            trigger_pressed = event.value > InputSettings.JOY_TRIGGER_THRESHOLD
            if trigger_pressed and not self.r2_trigger_is_pressed:
                self.audio.toggle_mute(
                    resume_music=self.game_active and not self.is_transitioning
                )
            self.r2_trigger_is_pressed = trigger_pressed
            return

        threshold = InputSettings.JOY_TRIGGER_THRESHOLD

        if event.axis == InputSettings.JOY_AXIS_LEFT_Y:
            prev = self.previous_left_stick_y
            curr = event.value
            if curr <= -threshold and prev > -threshold:
                self._dispatch_menu_navigate(0, -1)
            elif curr >= threshold and prev < threshold:
                self._dispatch_menu_navigate(0, 1)
            self.previous_left_stick_y = curr
            return

        if event.axis == InputSettings.JOY_AXIS_LEFT_X:
            prev = self.previous_left_stick_x
            curr = event.value
            if curr <= -threshold and prev > -threshold:
                self._dispatch_menu_navigate(-1, 0)
            elif curr >= threshold and prev < threshold:
                self._dispatch_menu_navigate(1, 0)
            self.previous_left_stick_x = curr
            return

    def _update_world(self) -> None:
        """Per-frame logic: message log typewriter, tutorial drain, sprite step + animate, collision."""
        self.message_log.update()
        if self.tutorial is not None:
            self.tutorial.update()

        if self.ui_state != 'playing' or not self.game_active:
            return

        # No sprite work at all while a modal overlay is up.
        if (
            self.is_transitioning
            or self.in_treasure_conversion
            or self.in_shop_phase
            or (self.tutorial is not None and self.tutorial.is_blocking)
        ):
            return

        # Sprite update reads fresh input — skip it while animations are
        # still in flight or the player would queue inputs mid-step.
        if not self.is_busy:
            self.all_sprites.update()

        # Animation completes in-flight motion regardless of is_busy so
        # sprites always finish their current step smoothly.
        for sprite in self.all_sprites:
            if hasattr(sprite, 'animate'):
                sprite.animate()
        self.check_player_caught_by_monster()

    def _render_frame(self) -> None:
        """Compose one frame: world, HUD panels, modal overlays, then CRT."""
        self.screen.fill(ColorSettings.SCREEN_BACKGROUND)

        if self.ui_state in {'playing', 'game_over'}:
            self.render.draw_grid_background()
            self.all_sprites.draw(self.screen)
            if self.ui_state == 'playing' and not DebugSettings.NO_FOG:
                self.render.draw_fog_of_war()
            self.render.draw_ui_frames()
            self.message_log.draw(self.screen)
            self.inventory_window.draw(self.screen)
            self.map_window.draw(self.screen)
            self.render.draw_level_transition()
            self.render.draw_treasure_conversion()
            self.render.draw_shop_menu()
            if self.tutorial is not None:
                self.tutorial.draw(self.screen)

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
            self.render.draw_end_game_screens()
        elif self.ui_state == 'enter_initials':
            self.render.draw_initials_entry_screen()
        elif self.ui_state == 'leaderboard':
            self.render.draw_leaderboard_screen()

        # Apply CRT pass after world/UI rendering.
        if not self.full_screen:
            self.crt.draw()

    def run(self):
        """Run the main game loop until the player quits."""
        while True:
            if self.quit_combo_pressed():
                self.close_game()
            self._tick_between_level_flow()
            self._process_events()
            self._update_world()
            self._render_frame()
            pygame.display.flip()
            self.clock.tick(ScreenSettings.FPS)

if __name__ == "__main__":
    game_manager = GameManager()
    game_manager.run()
