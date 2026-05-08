import pygame
import random
import os
from typing import Literal
from settings import *
from ui.render_utils import color_with_alpha
from util import coords
from core import loot

PlayerAction = Literal['move', 'dig', 'detector', 'light', 'repellent', 'cloak']
PlayerIntent = tuple[int, int, PlayerAction | None]

class Player(pygame.sprite.Sprite):
    """Represent the player entity, inventory state, and turn actions."""

    def __init__(self, game, position: tuple[int, int], groups) -> None:
        """
        Initialize the player sprite and its gameplay state.

        This sets up the player's visual sprite, movement state, inventory,
        temporary status effects, and animation data.

        Args:
            game: The active GameManager instance that coordinates the game.
            position: The player's starting screen position.
            groups: Sprite groups this player should be added to.
        """
        super().__init__(groups)
        # -------- Sprite visuals --------
        # Load every (helmet_state, facing) variant up front so swapping
        # frames per-turn is a dict lookup, not disk I/O. Helmet state is
        # driven by status effects (cloak/repellent → 'down'); facing is
        # driven by the last horizontal movement.
        tile_size = (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE)
        self.sprites: dict[tuple[str, str, str], pygame.Surface] = {}
        for key, path in AssetPaths.PLAYER_SPRITES.items():
            surf = pygame.image.load(path).convert_alpha()
            self.sprites[key] = pygame.transform.scale(surf, tile_size)
        self.facing = 'right'
        self.helmet_state = 'up'
        # Idle "look around" peek direction; 'center' is the neutral sprite.
        self.peek = 'center'
        # Real-time accumulators (ms) that drive the idle animation; reset on activity.
        self.idle_elapsed_ms = 0
        # -1 means the peek cycle hasn't started yet; 0..len-1 indexes IDLE_ANIMATION_SEQUENCE.
        self.idle_frame_index = -1
        self.idle_frame_elapsed_ms = 0
        # Tracks pygame ticks between frames so update_idle_animation can compute its own dt.
        self._idle_last_tick_ms = pygame.time.get_ticks()
        self.base_image = self.sprites[(self.helmet_state, self.facing, self.peek)]
        self.image = self.base_image.copy()

        # -------- Position and movement state --------
        self.rect = self.image.get_rect(topleft = position)
        self.position = pygame.math.Vector2(self.rect.topleft)

        initial_inventory = (
            ItemSettings.TEST_INITIAL_INVENTORY
            if DebugSettings.USE_TEST_INITIAL_INVENTORY
            else ItemSettings.NORMAL_INITIAL_INVENTORY
        )
        self.inventory = initial_inventory.copy()
        self.discovered_items = set(self.inventory.keys())
        
        self.repellent_turns = 0
        self.invisibility_turns = 0
        self.invisibility_cooldown_turns = 0
        self.invisibility_from_cloak = False
        self.flash_frame = 0

        self.light_radius = LightSettings.DEFAULT_RADIUS
        self.light_turns_left = 0
        self.active_light_max_radius = 0
        self.active_light_max_duration = 0

        # Light source the B button will activate. None until the player picks
        # one up; auto-selects the best owned source on inventory changes, and
        # can be cycled manually with L1/R1.
        self.selected_light_source: str | None = None
        self.refresh_light_selection()

        # -------- Animation state --------
        self.target_pos = pygame.math.Vector2(position)
        self.is_moving = False
        self.anim_speed = PlayerSettings.ANIMATION_SPEED

        # -------- Shared system references --------
        self.game = game
        self.dungeon = self.game.dungeon

    # -------------------------
    # LIGHT SOURCE MANAGEMENT
    # -------------------------

    def refresh_light_selection(self) -> None:
        """Ensure selected_light_source points to an owned source.

        Called after any inventory change that could affect light sources.
        - If the player owns no light sources, selection becomes None.
        - If the current selection is depleted (or unset), pick the best
          owned source per LightSettings.SOURCE_PRIORITY (LANTERN > TORCH > MATCH).
        - Otherwise leave the manual selection alone.
        """
        owned = self._owned_light_sources(LightSettings.SOURCE_PRIORITY)
        if not owned:
            self.selected_light_source = None
        elif self.selected_light_source not in owned:
            self.selected_light_source = owned[0]

    def cycle_selected_light_source(self, direction: int) -> None:
        """Cycle the B-button light selection through owned sources.

        Args:
            direction: +1 for next (R1), -1 for previous (L1).
        """
        owned = self._owned_light_sources(LightSettings.SOURCE_CYCLE_ORDER)
        if not owned:
            return
        if self.selected_light_source not in owned:
            self.selected_light_source = owned[0]
            return
        if len(owned) == 1:
            return
        current_index = owned.index(self.selected_light_source)
        new_index = (current_index + direction) % len(owned)
        self.selected_light_source = owned[new_index]

    def _owned_light_sources(self, order: tuple[str, ...]) -> list[str]:
        """Return the subset of light sources the player currently has, in the given order."""
        return [name for name in order if self.inventory.get(name, 0) > 0]

    # -------------------------
    # INPUT
    # -------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle edge-triggered player input (currently just light cycling).

        Polled inputs (move/dig/light/etc.) are read fresh each frame in
        read_input_intent. Light cycling needs one action per press, so
        it lives here and is fed by GameManager's main event loop.
        """
        if not self._gameplay_input_allowed():
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                self.cycle_selected_light_source(-1)
            elif event.key == pygame.K_e:
                self.cycle_selected_light_source(1)
            return

        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == InputSettings.JOY_BUTTON_L1:
                self.cycle_selected_light_source(-1)
            elif event.button == InputSettings.JOY_BUTTON_R1:
                self.cycle_selected_light_source(1)

    def read_input_intent(self) -> PlayerIntent:
        """
        Read player input and translate it into movement or action intent.

        Checks both keyboard and controller input and returns a single action
        for the current frame.

        Returns:
            A tuple of (delta_x_tiles, delta_y_tiles, action).
            Movement deltas are -1, 0, or 1.
            action is one of 'move', 'dig', 'detector', 'light',
            'repellent', or None.
        """
        keys = pygame.key.get_pressed()
        delta_x_tiles = 0
        delta_y_tiles = 0
        action: PlayerAction | None = None

        # Skip a frame of input while the tutorial is still holding the
        # dismiss key down — otherwise the press that closed a card would
        # also count as a dig. The tutorial owns this state so it can
        # release it on its own.
        if self.game.tutorial is not None and self.game.tutorial.input_locked:
            return 0, 0, None

        # -------- Keyboard movement input --------
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            delta_y_tiles = -1
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            delta_y_tiles = 1
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            delta_x_tiles = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            delta_x_tiles = 1

        if delta_x_tiles != 0 or delta_y_tiles != 0:
            action = 'move'

        # -------- Keyboard action input --------
        elif keys[pygame.K_SPACE]:
            action = 'dig'
        elif keys[pygame.K_x]:
            action = 'detector'
        elif keys[pygame.K_f]:
            action = 'light'
        elif keys[pygame.K_r]:
            action = 'repellent'
        elif keys[pygame.K_c]:
            action = 'cloak'

        # -------- Controller movement/action input --------
        if pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)
            
            # D-pad movement
            dpad_direction = joystick.get_hat(0)
            # Override keyboard movement only when the D-pad is active.
            if dpad_direction[0] != 0 or dpad_direction[1] != 0:
                delta_x_tiles = dpad_direction[0]
                delta_y_tiles = -dpad_direction[1]
                delta_x_tiles, delta_y_tiles = self._normalize_cardinal_step(delta_x_tiles, delta_y_tiles)
                action = 'move'

            # Controller actions
            if action is None:
                if joystick.get_button(InputSettings.JOY_BUTTON_A):
                    action = 'dig'
                elif joystick.get_button(InputSettings.JOY_BUTTON_B):
                    action = 'light'
                elif joystick.get_button(InputSettings.JOY_BUTTON_X):
                    action = 'detector'
                elif joystick.get_button(InputSettings.JOY_BUTTON_Y):
                    action = 'repellent'
                elif joystick.get_axis(InputSettings.JOY_AXIS_L2) > InputSettings.JOY_TRIGGER_THRESHOLD:
                    action = 'cloak'

        delta_x_tiles, delta_y_tiles = self._normalize_cardinal_step(delta_x_tiles, delta_y_tiles)
        return delta_x_tiles, delta_y_tiles, action

    def _gameplay_input_allowed(self) -> bool:
        """True only when the player is in active gameplay (no menus/transitions)."""
        game = self.game
        return (
            game.ui_state == 'playing'
            and game.game_active
            and not game.is_transitioning
            and not game.in_treasure_conversion
            and not game.in_shop_phase
        )

    def _normalize_cardinal_step(self, delta_x_tiles: int, delta_y_tiles: int) -> tuple[int, int]:
        """Allow movement on only one axis so diagonal steps are impossible."""
        if delta_x_tiles != 0 and delta_y_tiles != 0:
            # Keep vertical priority to match keyboard input ordering.
            delta_x_tiles = 0
        return delta_x_tiles, delta_y_tiles

    # -------------------------
    # ACTIONS
    # -------------------------

    def process_turn_action(self) -> None:
        """
        Process one player input action when the player is allowed to act.

        This method gates actions behind the current cooldown/timer logic,
        then dispatches movement, digging, detector use, light use, or repellent use.
        """

        # Get the direction the player wants to go
        delta_x_tiles, delta_y_tiles, action = self.read_input_intent()
        # If there is input, execute the movement and reset the timer
        if action == 'move':
            self.try_move_by_grid_step(int(delta_x_tiles), int(delta_y_tiles))

        elif action == 'dig':
            self.dig_current_tile()
            # Turn advancement is handled inside dig_current_tile().

        elif action == 'light':
            # Use the player's currently selected light source. Defensive
            # refresh in case the selection went stale (e.g. depleted between
            # presses).
            self.refresh_light_selection()
            name = self.selected_light_source

            if name and self.inventory.get(name, 0) > 0:
                radius, duration = LightSettings.SOURCE_STATS[name]
                self.inventory[name] -= 1

                # Preserve source max values for per-turn radius decay.
                self.active_light_max_radius = radius
                self.active_light_max_duration = duration
                self.light_radius = radius
                # Add one turn buffer so effects include the activation turn.
                self.light_turns_left = duration + GameSettings.STATUS_EFFECT_TURN_BUFFER

                if self.inventory.get("MAGIC MAP", 0) > 0:
                    self.game.map_memory.remember_visible_map_info()
                self.game.log_message(f"YOU LIGHT A {name.upper()}!")
                if name == 'MATCH':
                    self.game.audio.play('match_light')
                else:
                    self.game.audio.play('light')

                # Move selection to the next-best owned source if this one ran out.
                self.refresh_light_selection()
                self.game.notify_tutorial(
                    'item_used', kind='light', name=name, duration=int(duration)
                )
                self.game.advance_turn()
            else:
                self.game.log_message("YOU HAVE NO LIGHT SOURCES!")

        elif action == 'detector':
            if self.inventory.get('KEY DETECTOR', 0) > 0:
                self.activate_key_detector()
                self.game.notify_tutorial('item_used', kind='detector')
                self.game.advance_turn()
            else:
                self.game.log_message("YOU DON'T HAVE A KEY DETECTOR!")

        elif action == 'repellent':
            if self.inventory.get('MONSTER REPELLENT', 0) > 0:
                self.inventory['MONSTER REPELLENT'] -= 1
                self.repellent_turns = MonsterSettings.REPELLENT_DURATION + GameSettings.STATUS_EFFECT_TURN_BUFFER
                self.game.log_message("YOU SPRAY THE REPELLENT.")
                self.game.audio.play_repellent_sound(self.inventory['MONSTER REPELLENT'])
                self.game.notify_tutorial(
                    'item_used', kind='repellent', duration=MonsterSettings.REPELLENT_DURATION
                )
                self.game.advance_turn()
            else:
                self.game.log_message("YOU HAVE NO MONSTER REPELLENT LEFT!")

        elif action == 'cloak':
            has_scroll = self.inventory.get('INVISIBILITY SCROLL', 0) > 0
            has_cloak = self.inventory.get('INVISIBILITY CLOAK', 0) > 0

            if not has_scroll and not has_cloak:
                self.game.log_message("YOU DON'T HAVE AN INVISIBILITY SCROLL!")
            elif self.invisibility_turns > 0:
                self.game.log_message("YOU ARE ALREADY INVISIBLE!")
            elif has_cloak and self.invisibility_cooldown_turns > 0:
                self.game.log_message("THE INVISIBILITY CLOAK NEEDS TIME TO RECHARGE.")
            elif has_cloak:
                self.invisibility_turns = ItemSettings.INVISIBILITY_CLOAK_DURATION + GameSettings.STATUS_EFFECT_TURN_BUFFER
                self.invisibility_from_cloak = True
                self.game.log_message("YOU WRAP YOURSELF IN THE INVISIBILITY CLOAK.")
                self.game.audio.play('vanish')
                self.game.notify_tutorial(
                    'item_used', kind='cloak', duration=ItemSettings.INVISIBILITY_CLOAK_DURATION
                )
                self.game.advance_turn()
            else:
                self.inventory['INVISIBILITY SCROLL'] -= 1
                if self.inventory['INVISIBILITY SCROLL'] <= 0:
                    self.inventory.pop('INVISIBILITY SCROLL', None)

                self.invisibility_turns = ItemSettings.INVISIBILITY_CLOAK_DURATION + GameSettings.STATUS_EFFECT_TURN_BUFFER
                self.invisibility_from_cloak = False
                self.game.log_message("YOU READ THE INVISIBILITY SCROLL.")
                self.game.notify_tutorial(
                    'item_used', kind='scroll', duration=ItemSettings.INVISIBILITY_CLOAK_DURATION
                )
                self.game.audio.play('vanish')
                self.game.advance_turn()

    def try_move_by_grid_step(self, delta_x_tiles: int = 0, delta_y_tiles: int = 0) -> None:
        """
        Attempt to move the player by one tile.

        If the target tile is walkable, this starts movement animation,
        logs the direction, plays the movement sound, and advances the turn.
        If the target tile is blocked, it logs a boundary message instead.

        Args:
            delta_x_tiles: Horizontal tile step, usually -1, 0, or 1.
            delta_y_tiles: Vertical tile step, usually -1, 0, or 1.
        """
        delta_x_tiles, delta_y_tiles = self._normalize_cardinal_step(delta_x_tiles, delta_y_tiles)
        current_col, current_row = coords.screen_to_grid(self.position.x, self.position.y)
        target_col = current_col + delta_x_tiles
        target_row = current_row + delta_y_tiles

        if self.dungeon.is_walkable(target_col, target_row):
            target_x, target_y = coords.grid_to_screen(target_col, target_row)
            self.target_pos = pygame.math.Vector2(target_x, target_y)
            self.is_moving = True

            # Update facing for sprite flipping. Vertical-only steps leave
            # facing alone so the player keeps looking the way they last
            # walked horizontally.
            if delta_x_tiles > 0:
                self.facing = 'right'
            elif delta_x_tiles < 0:
                self.facing = 'left'

            if delta_y_tiles == -1:
                self.game.log_message("YOU MOVED NORTH.")
            elif delta_y_tiles == 1:
                self.game.log_message("YOU MOVED SOUTH.")
            elif delta_x_tiles == -1:
                self.game.log_message("YOU MOVED WEST.")
            elif delta_x_tiles == 1:
                self.game.log_message("YOU MOVED EAST.")

            self.game.audio.play('move')
            self.game.notify_tutorial('moved')
            self.game.advance_turn()
        else:
            self.game.log_message("YOU CAN'T GO THAT WAY!")
            self.game.audio.play('boundary')

    def dig_current_tile(self) -> None:
        """
        Resolve the player's dig action at the current tile.

        If the player is standing on the door, digging becomes an unlock attempt.
        Otherwise, this reveals the tile, resolves any discovered item,
        updates remembered map state, and advances the turn.
        """
        if self.position == self.game.door.position:
            if self.inventory.get('KEY', 0) > 0:
                self.game.door.open_door()
                self.game.intermission.handle_door_unlock()
            else:
                self.game.log_message("THE DOOR IS LOCKED. YOU NEED A KEY!")
                self.game.audio.play('boundary')
            return

        tile_grid_pos = coords.screen_to_grid(self.position.x, self.position.y)
        tile_state = self.dungeon.tile_data.get(tile_grid_pos)

        # Guard against invalid tile state to avoid runtime failure.
        if not tile_state:
            self.game.log_message("YOU CAN'T DIG HERE.")
            return

        if tile_state["is_dug"]:
            self.game.log_message("YOU'VE ALREADY DUG HERE.")
            return

        tile_state["is_dug"] = True
        self.game.audio.play('dig')
        self.game.notify_tutorial('dug')
        self.game.map_memory.remember_visible_map_info()
        found_item, amount = self.dungeon.get_item_at_tile(tile_grid_pos)

        # Suppress scroll drops if the player already owns the cloak upgrade.
        if found_item == 'INVISIBILITY SCROLL' and self.inventory.get('INVISIBILITY CLOAK', 0) > 0:
            found_item = None
            amount = 0

        if found_item:
            loot.resolve_pickup(self.game, found_item, amount)
        else:
            self.game.log_message("NOTHING BUT DIRT HERE.")
        self.game.advance_turn()

    def activate_key_detector(self) -> None:
        """
        Check the player's distance from the hidden key and log a hint.

        The detector uses Manhattan distance in grid space and gives stronger
        feedback as the player gets closer.
        """
        player_grid_pos = coords.screen_to_grid(self.position.x, self.position.y)
        key_grid_pos = self.dungeon.key_grid_pos
        distance = self.dungeon.manhattan_distance(player_grid_pos, key_grid_pos)

        if distance == ItemSettings.DETECTOR_DISTANCE_FOUND:
            self.game.log_message("THE KEY DETECTOR IS GOING WILD!")
            self.game.audio.play('detector_found')
        elif distance == ItemSettings.DETECTOR_DISTANCE_HOT:
            self.game.log_message("THE KEY DETECTOR BEEPS RAPIDLY!")
            self.game.audio.play('detector_hot')
        elif distance <= ItemSettings.DETECTOR_DISTANCE_STEADY:
            self.game.log_message("THE KEY DETECTOR GIVES A STEADY PULSE...")
            self.game.audio.play('detector_warm')
        elif distance <= ItemSettings.DETECTOR_DISTANCE_SLOW:
            self.game.log_message("THE KEY DETECTOR BEEPS SLOWLY...")
        elif distance <= ItemSettings.DETECTOR_DISTANCE_FAINT:
            self.game.log_message("A FAINT BEEP COMES FROM THE DETECTOR.")
        else:
            # Dead silent only when very far away.
            self.game.log_message("THE KEY DETECTOR IS SILENT.")

    # -------------------------
    # TURN-TIME UPDATES
    # -------------------------

    def tick_status_effects(self) -> None:
        """Decrement temporary status timers and surface their fade-out messages.

        Called from GameManager.advance_turn after the player commits an
        action so the player owns its own per-turn bookkeeping.
        """
        # Light source: shrink the radius proportionally each turn so the
        # circle visibly fades before the source goes out.
        if self.light_turns_left > 0:
            self.light_turns_left -= 1

            if self.light_turns_left > 0:
                radius_per_turn = self.active_light_max_radius / self.active_light_max_duration
                self.light_radius = radius_per_turn * self.light_turns_left
            else:
                self.light_radius = LightSettings.DEFAULT_RADIUS
                self.game.log_message("YOUR LIGHT FLICKERS OUT...")

        if self.repellent_turns > 0:
            self.repellent_turns -= 1
            if self.repellent_turns == 0:
                self.game.log_message("THE SCENT OF THE REPELLENT FADES AWAY...")

        if self.invisibility_turns > 0:
            self.invisibility_turns -= 1
            if self.invisibility_turns == 0:
                self.game.log_message("THE INVISIBILITY WEARS OFF.")
                # Cloak (reusable) starts cooling down immediately after
                # wearing off; scrolls are one-shots and don't.
                if self.invisibility_from_cloak:
                    self.invisibility_cooldown_turns = (
                        ItemSettings.INVISIBILITY_CLOAK_COOLDOWN
                        + GameSettings.STATUS_EFFECT_TURN_BUFFER
                    )
                    self.invisibility_from_cloak = False

        if self.invisibility_cooldown_turns > 0:
            self.invisibility_cooldown_turns -= 1

    # -------------------------
    # STATUS QUERIES
    # -------------------------

    def is_invisible(self) -> bool:
        """Return True while invisibility cloak effect is active."""
        return self.invisibility_turns > 0

    def is_repelled(self) -> bool:
        """Return True while monster repellent effect is active."""
        return self.repellent_turns > 0

    # -------------------------
    # VISUALS
    # -------------------------

    def get_action_window_border_style(self) -> tuple[str, int]:
        """Return (RGB color, alpha) for the animated action-window border."""
        if self.is_invisible():
            border_alpha = 95 if self.flash_frame < PlayerSettings.FLASH_HALF_CYCLE else 255
            border_color = ColorSettings.BORDER_REPELLED if self.is_repelled() else ColorSettings.BORDER_DEFAULT
            return border_color, border_alpha

        if self.is_repelled():
            pulse_ratio = self._get_pulse_ratio()
            border_alpha = 80 + int(80 * pulse_ratio)
            return ColorSettings.BORDER_REPELLED, border_alpha

        return ColorSettings.BORDER_DEFAULT, 255

    def update_invisibility_visual(self) -> None:
        """Apply visual effects for invisibility and repellent states."""
        is_invisible = self.is_invisible()
        is_repelled = self.is_repelled()

        if is_invisible or is_repelled:
            self.flash_frame = (self.flash_frame + 1) % PlayerSettings.FLASH_CYCLE_FRAMES
        else:
            self.flash_frame = 0

        # Helmet is "down" while a status effect is masking the player
        # (cloak or repellent); otherwise the regular helmet-up sprite.
        self.helmet_state = 'down' if (is_invisible or is_repelled) else 'up'
        # Only the helmet-up sprite has peek variants; force center otherwise.
        peek = self.peek if self.helmet_state == 'up' else 'center'
        self.base_image = self.sprites[(self.helmet_state, self.facing, peek)]
        self.image = self.base_image.copy()

        if is_repelled:
            pulse_ratio = self._get_pulse_ratio()
            tint_alpha = 70 + int(40 * pulse_ratio)
            tint_surface = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            tint_surface.fill(color_with_alpha(ColorSettings.REPELLED_TINT, tint_alpha))
            self.image.blit(tint_surface, (0, 0))

        if is_invisible:
            alpha = 95 if self.flash_frame < PlayerSettings.FLASH_HALF_CYCLE else 255
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)

    def _get_pulse_ratio(self) -> float:
        """Return a 0..1 triangle wave used by status-effect pulses."""
        # Generate a symmetric 0..1 pulse over one flash cycle.
        half_cycle = PlayerSettings.FLASH_HALF_CYCLE
        distance_from_center = abs(self.flash_frame - half_cycle)
        return 1.0 - (distance_from_center / half_cycle)

    # -------------------------
    # PER-FRAME
    # -------------------------

    def reset_idle_animation(self) -> None:
        """Cancel any active peek cycle and restart the idle trigger countdown."""
        self.idle_elapsed_ms = 0
        self.idle_frame_index = -1
        self.idle_frame_elapsed_ms = 0
        self.peek = 'center'

    def update_idle_animation(self) -> None:
        """Drive the idle "look around" peek cycle while the player is standing still."""
        # Compute real-time delta so timing is independent of FPS variance.
        now_ms = pygame.time.get_ticks()
        dt_ms = now_ms - self._idle_last_tick_ms
        self._idle_last_tick_ms = now_ms

        # Any movement or non-up helmet state cancels and resets the cycle.
        if self.is_moving or self.helmet_state != 'up':
            self.reset_idle_animation()
            return

        sequence = PlayerSettings.IDLE_ANIMATION_SEQUENCE
        if self.idle_frame_index == -1:
            # Waiting for the trigger delay before starting the peek sequence.
            self.idle_elapsed_ms += dt_ms
            if self.idle_elapsed_ms >= PlayerSettings.IDLE_ANIMATION_DELAY_MS:
                self.idle_frame_index = 0
                self.idle_frame_elapsed_ms = 0
                self.peek = sequence[0]
            return

        # Advance through the sequence, holding each frame for FRAME_MS.
        self.idle_frame_elapsed_ms += dt_ms
        if self.idle_frame_elapsed_ms >= PlayerSettings.IDLE_ANIMATION_FRAME_MS:
            self.idle_frame_elapsed_ms = 0
            self.idle_frame_index += 1
            if self.idle_frame_index >= len(sequence):
                # Cycle finished; restart the trigger countdown so it plays again later.
                self.idle_frame_index = -1
                self.idle_elapsed_ms = 0
                self.peek = 'center'
            else:
                self.peek = sequence[self.idle_frame_index]

    def animate(self) -> None:
        """
        Advance the player's movement animation toward the current target position.

        This keeps the game visually smooth while gameplay still resolves in grid steps.
        """
        if self.is_moving:
            # Move along the normalized direction vector toward target.
            direction = self.target_pos - self.position
            distance = direction.length()

            if distance < self.anim_speed:
                # Snap to destination when remaining distance is below one step.
                self.position = self.target_pos
                self.rect.topleft = (int(self.position.x), int(self.position.y))
                self.is_moving = False
            else:
                direction.scale_to_length(self.anim_speed)
                self.position += direction
                self.rect.topleft = (int(self.position.x), int(self.position.y))

        # Update peek before picking the sprite so the new frame is reflected immediately.
        self.update_idle_animation()
        self.update_invisibility_visual()

    def update(self) -> None:
        """
        Update the player's per-frame behavior.

        The player only processes new input when not already moving.
        """
        if not self.is_moving:
            self.process_turn_action()


class Monster(pygame.sprite.Sprite):
    """Represent monster behavior, movement, and chase decision logic."""

    def __init__(self, game, position: tuple[int, int], groups) -> None:
        """
        Initialize the monster sprite and its movement state.

        Sets up the monster's visual representation, position tracking,
        and animation state used for turn-based movement.

        Args:
            game: The active GameManager instance.
            position: Starting screen position.
            groups: Sprite groups this monster belongs to.
        """
        super().__init__(groups)
        self.game = game
        self.dungeon = self.game.dungeon

        # Build the spawn pool. Each entry is a "monster group" keyed by
        # the canonical filename (with any `_left` / `_right` suffix
        # stripped) so paired left/right variants count as one creature
        # rather than two. For each group we remember which sides exist
        # so the instance can flip when it changes facing.
        IMG_EXTS = ('.png', '.jpg', '.jpeg', '.webp')
        groups: dict[str, dict[str, str]] = {}
        if os.path.isdir(AssetPaths.MONSTER_VARIANTS_DIR):
            for name in os.listdir(AssetPaths.MONSTER_VARIANTS_DIR):
                candidate_path = os.path.join(AssetPaths.MONSTER_VARIANTS_DIR, name)
                if not (os.path.isfile(candidate_path) and name.lower().endswith(IMG_EXTS)):
                    continue
                stem, _ext = os.path.splitext(name)
                if stem.endswith('_left'):
                    key, side = stem[:-5], 'left'
                elif stem.endswith('_right'):
                    key, side = stem[:-6], 'right'
                else:
                    key, side = stem, 'static'
                groups.setdefault(key, {})[side] = candidate_path

        # Pick a random monster group, or fall back to the lone default
        # sprite if the directory is empty / missing.
        if groups:
            chosen_group = random.choice(list(groups.values()))
        else:
            chosen_group = {'static': AssetPaths.MONSTER}

        # Load each available side once; instance flipping is just a
        # dict lookup later.
        self.facing_images: dict[str, pygame.Surface] = {}
        for side, path in chosen_group.items():
            surf = pygame.image.load(path).convert_alpha()
            self.facing_images[side] = pygame.transform.scale(surf, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))

        # Default facing prefers right, then left, then the static sprite.
        # `self.facing` is also used as the lookup key into facing_images,
        # so 'static' is a valid value for non-flipping monsters.
        if 'right' in self.facing_images:
            self.facing = 'right'
        elif 'left' in self.facing_images:
            self.facing = 'left'
        else:
            self.facing = 'static'
        self.image = self.facing_images[self.facing]
        
        self.rect = self.image.get_rect(topleft = position)
        self.position = pygame.math.Vector2(self.rect.topleft)

        self.target_pos = pygame.math.Vector2(position)
        self.is_moving = False
        self.anim_speed = PlayerSettings.ANIMATION_SPEED
        self.is_chasing = False
        # Edge-trigger flag for the darkness hearing warning so the
        # log doesn't spam every turn the monster sits inside the
        # hearing bubble. Resets when the monster leaves the bubble
        # so a fresh approach can re-arm the warning.
        self.has_warned_player_of_proximity = False
        # Grid (col, row) of the player at the moment they were last
        # spotted. While set and is_chasing is True, the monster keeps
        # advancing toward this tile after losing sight ("investigate
        # last seen position"). Cleared inside _stop_chasing, so the
        # invariant "not chasing => no remembered tile" holds for free
        # across the give-up / repellent / invisibility paths.
        self.last_known_player_grid_pos: tuple[int, int] | None = None

    # -------------------------
    # TURN LOGIC
    # -------------------------

    def resolve_turn(self) -> None:
        """
        Determine the monster's behavior for a single turn.

        The monster can:
        - move away from the player if repelled
        - chase the player if within range and line of sight
        - move randomly or idle otherwise

        Behavior priority:
            1. Repelled → move away
            2. In range + visible → chase
            3. Otherwise → random movement or idle
        """
       
        # Check if the monster is currently repelled
        is_repelled = self.game.player.repellent_turns > 0
        player_is_invisible = self.game.player.is_invisible()

        # Calculate the Manhattan distance to the player
        delta_pixels_x = self.game.player.position.x - self.position.x
        delta_pixels_y = self.game.player.position.y - self.position.y
        manhattan_distance = (abs(delta_pixels_x) // GridSettings.TILE_SIZE) + (abs(delta_pixels_y) // GridSettings.TILE_SIZE)

        # Helper variables for readability
        player_has_light = self.game.player.light_radius > 0
        is_adjacent = manhattan_distance <= 1

        if player_is_invisible:
            self._stop_chasing()
            if random.random() > MonsterSettings.IDLE_CHANCE:
                self.move_randomly_one_tile()
            return

        # If the monster is repelled, it will try to move away from the player instead of towards them.
        if is_repelled:
            self._stop_chasing()
            chase_step_x, chase_step_y = self._choose_primary_chase_step(delta_pixels_x, delta_pixels_y)
            step_x = -chase_step_x
            step_y = -chase_step_y

            # After calculating the movement, we apply it.
            # The apply_movement function will handle boundary checks to make sure the monster doesn't move out of bounds.
            self.try_start_move(step_x, step_y)
            return

        # Whether the monster has live eyes on the player this turn.
        # Light is the danger trigger — an unlit player is never spotted
        # regardless of distance. Adjacent counts because a monster on
        # the next tile can grab the player even past the light edge.
        spotted_player = player_has_light and (
            is_adjacent
            or (manhattan_distance <= int(self.game.player.light_radius) and self.has_clear_line_of_sight_to_player())
        )

        if spotted_player:
            if not self.is_chasing:
                self.is_chasing = True
                self.game.audio.play('monster_chase')
                self.game.audio.play_chase_music()
                self._log_chase_warning(manhattan_distance)
                self.game.notify_tutorial('monster_spotted')
            # Refresh the remembered tile every turn we still see the
            # player, so the moment sight is lost we head for whichever
            # tile they were standing on most recently.
            self.last_known_player_grid_pos = coords.screen_to_grid(
                self.game.player.position.x, self.game.player.position.y
            )
        elif self.is_chasing and self.last_known_player_grid_pos is not None:
            # Sight is broken (player ducked the light, hid behind a
            # wall, or killed their lantern), but the monster still
            # remembers where they were. If the monster has reached that
            # tile, the trail goes cold and the chase ends; otherwise
            # the chase-step block below keeps advancing toward it.
            monster_grid_pos = coords.screen_to_grid(self.position.x, self.position.y)
            if monster_grid_pos == self.last_known_player_grid_pos:
                self._stop_chasing()
        else:
            self._stop_chasing()

        # The "you hear something" cue belongs to unlit gameplay only:
        # while the player is lit, the spotted/last-known branches above
        # already surface the threat. Keeping it here (after the chase
        # decision) means it can still fire mid-investigation when the
        # player has killed their light to break LOS.
        if not player_has_light:
            self._maybe_warn_proximity_in_dark(manhattan_distance)

        # If the monster is chasing, it still has a 20% chance to hesitate.
        if self.is_chasing:
            if random.random() < MonsterSettings.IDLE_CHANCE:
                return

            target_delta_x, target_delta_y = self._chase_target_delta(
                spotted_player, delta_pixels_x, delta_pixels_y
            )
            step_x, step_y = self._choose_primary_chase_step(target_delta_x, target_delta_y)

            # After calculating the movement, we apply it.
            self.try_start_move(step_x, step_y)
            return

        # If the monster is not chasing, it has a chance to move randomly or do nothing (idle).
        if random.random() > MonsterSettings.IDLE_CHANCE:
            self.move_randomly_one_tile()

    def move_randomly_one_tile(self) -> None:
        """
        Move the monster in a random cardinal direction.

        Used when the monster is not actively chasing the player.
        """
        direction = random.choice(['up', 'down', 'left', 'right'])
        step_x, step_y = 0, 0
        if direction == 'up': step_y = -GridSettings.TILE_SIZE
        elif direction == 'down': step_y = GridSettings.TILE_SIZE
        elif direction == 'left': step_x = -GridSettings.TILE_SIZE
        elif direction == 'right': step_x = GridSettings.TILE_SIZE
        
        self.try_start_move(step_x, step_y)

    def try_start_move(self, delta_pixels_x: int, delta_pixels_y: int) -> None:
        """
        Attempt to move the monster by a pixel offset.

        Converts the movement into grid space, checks if the target tile
        is walkable, and starts movement animation if valid.

        Args:
            delta_pixels_x: Pixel movement in the x direction.
            delta_pixels_y: Pixel movement in the y direction.
        """
        current_col, current_row = coords.screen_to_grid(self.position.x, self.position.y)
        target_col = current_col + (delta_pixels_x // GridSettings.TILE_SIZE)
        target_row = current_row + (delta_pixels_y // GridSettings.TILE_SIZE)

        if self.dungeon.is_walkable(target_col, target_row):
            target_x, target_y = coords.grid_to_screen(target_col, target_row)
            self.target_pos = pygame.math.Vector2(target_x, target_y)
            self.is_moving = True

            # Flip the sprite to face the direction of horizontal motion.
            # Monsters without a paired left/right image (key 'static')
            # leave their single sprite untouched.
            if delta_pixels_x > 0 and 'right' in self.facing_images:
                self.facing = 'right'
                self.image = self.facing_images['right']
            elif delta_pixels_x < 0 and 'left' in self.facing_images:
                self.facing = 'left'
                self.image = self.facing_images['left']

    def has_clear_line_of_sight_to_player(self) -> bool:
        """
        Check if the monster has a clear path to the player.

        Delegates to DungeonLevel.has_line_of_sight, which walks the grid
        cells between monster and player using Bresenham's line algorithm
        (an integer-only line-drawing routine that picks the closest grid
        cell to a true straight line at each step). Bresenham handles
        diagonal sight lines, so this no longer requires the monster and
        player to share a row or column. Walls block sight; dirt and
        other walkable tiles do not.

        Returns:
            True if no walls block the view, False otherwise.
        """
        m_col, m_row = coords.screen_to_grid(self.position.x, self.position.y)
        p_col, p_row = coords.screen_to_grid(self.game.player.position.x, self.game.player.position.y)
        return self.dungeon.has_line_of_sight((m_col, m_row), (p_col, p_row))

    def _chase_target_delta(
        self,
        has_eyes_on_player: bool,
        player_delta_pixels_x: float,
        player_delta_pixels_y: float,
    ) -> tuple[float, float]:
        """Return the pixel delta from the monster to its chase target.

        When the monster currently sees the player, the target is the
        player's live position and the precomputed delta is returned
        unchanged. When sight has been lost mid-chase, the target
        becomes the grid cell stored in last_known_player_grid_pos —
        the "investigate last seen tile" behavior. The tuple-None
        guard is defensive: the caller only invokes this while
        is_chasing, which by invariant implies last_known is set, but
        falling back to the live delta keeps the monster moving rather
        than freezing if that invariant is ever violated.

        Args:
            has_eyes_on_player: True if the player was spotted this turn.
            player_delta_pixels_x: Pre-computed pixel delta to the player.
            player_delta_pixels_y: Pre-computed pixel delta to the player.

        Returns:
            (dx, dy) in pixels from the monster to the chase target.
        """
        if has_eyes_on_player or self.last_known_player_grid_pos is None:
            return player_delta_pixels_x, player_delta_pixels_y
        last_col, last_row = self.last_known_player_grid_pos
        last_x, last_y = coords.grid_to_screen(last_col, last_row)
        return last_x - self.position.x, last_y - self.position.y

    def _choose_primary_chase_step(self, delta_pixels_x: float, delta_pixels_y: float) -> tuple[int, int]:
        """Return a one-tile movement vector toward the player.

        Args:
            delta_pixels_x: Horizontal delta from monster to player.
            delta_pixels_y: Vertical delta from monster to player.

        Returns:
            Pixel step aligned to one cardinal direction.
        """
        step_x = 0
        step_y = 0

        if abs(delta_pixels_x) >= abs(delta_pixels_y):
            if delta_pixels_x > 0:
                step_x = GridSettings.TILE_SIZE
            elif delta_pixels_x < 0:
                step_x = -GridSettings.TILE_SIZE
            elif delta_pixels_y > 0:
                step_y = GridSettings.TILE_SIZE
            elif delta_pixels_y < 0:
                step_y = -GridSettings.TILE_SIZE
        else:
            if delta_pixels_y > 0:
                step_y = GridSettings.TILE_SIZE
            elif delta_pixels_y < 0:
                step_y = -GridSettings.TILE_SIZE
            elif delta_pixels_x > 0:
                step_x = GridSettings.TILE_SIZE
            elif delta_pixels_x < 0:
                step_x = -GridSettings.TILE_SIZE

        return step_x, step_y

    def _is_visible_in_player_light(self, manhattan_distance: int) -> bool:
        """Return whether the monster is currently visible in the player's light."""
        return self.game.player.light_radius > 0 and manhattan_distance <= int(self.game.player.light_radius)

    def _log_chase_warning(self, manhattan_distance: int) -> None:
        """Log the chase warning text variant based on player-visible monster state."""
        if self._is_visible_in_player_light(manhattan_distance):
            self.game.log_message("YOU'VE BEEN SPOTTED BY A MONSTER!")
        else:
            self.game.log_message("YOU HEAR A MONSTER NEARBY!")

    def _maybe_warn_proximity_in_dark(self, manhattan_distance: int) -> None:
        """Emit a one-shot 'you hear something' log when this monster
        enters the player's hearing bubble in pitch darkness.

        Without this cue, an unlit player has no way to tell a monster
        is wandering toward them and dies to what looks like a random
        coin flip. The flag is edge-triggered: it arms when the monster
        is outside HEARING_RADIUS and fires once on entry, so the log
        doesn't repeat while the monster sits inside the bubble.

        Args:
            manhattan_distance: Manhattan distance to the player in
                tiles, computed once by the caller to avoid recomputing.
        """
        if manhattan_distance <= MonsterSettings.HEARING_RADIUS:
            if not self.has_warned_player_of_proximity:
                self.has_warned_player_of_proximity = True
                self.game.log_message("YOU HEAR SOMETHING NEARBY, YOU AREN'T ALONE...")
                # ^ add sound effect here later
        else:
            self.has_warned_player_of_proximity = False

    def _stop_chasing(self) -> None:
        """Drop chase state and resume normal music; fire tutorial hook on transition.

        Also clears last_known_player_grid_pos so the "investigate last
        seen tile" memory is wiped any time the chase ends — whether the
        monster gave up, was repelled, or the player went invisible.
        Centralizing the clear here keeps every caller from having to
        remember it.

        Music is global but is_chasing is per-monster: only switch back
        to normal background music when no other monster on the level
        is still chasing. Without this guard, a monster that doesn't
        see the player resolves its turn after a chasing monster and
        flips the music back to normal every frame — which is what
        masked the chase soundtrack after the Bresenham LOS change
        started letting more than one monster's chase decision land in
        the same player turn.
        """
        if self.is_chasing:
            self.game.notify_tutorial('monster_lost_sight')
        self.is_chasing = False
        self.last_known_player_grid_pos = None
        any_other_monster_still_chasing = any(
            other is not self and other.is_chasing
            for other in self.game.monsters
        )
        if not any_other_monster_still_chasing:
            self.game.audio.play_normal_music()

    # -------------------------
    # PER-FRAME
    # -------------------------

    def animate(self) -> None:
        """
        Advance the monster's movement animation toward its target position.
        """
        if self.is_moving:
            direction = self.target_pos - self.position
            if direction.length() < self.anim_speed:
                self.position = self.target_pos
                self.rect.topleft = (int(self.position.x), int(self.position.y))
                self.is_moving = False
            else:
                direction.scale_to_length(self.anim_speed)
                self.position += direction
                self.rect.topleft = (int(self.position.x), int(self.position.y))

    def update(self) -> None:
        """
        Placeholder for per-frame behavior.

        Monster actions are currently turn-based, so this method is unused.
        """
        pass


class NPC(pygame.sprite.Sprite):
    """A stationary NPC that gives the player a random item when approached."""

    def __init__(self, game, position: tuple[int, int], groups) -> None:
        """Initialize NPC sprite visuals and fade-out state.

        Args:
            game: Active game manager instance.
            position: Starting screen position.
            groups: Sprite groups this NPC belongs to.
        """
        super().__init__(groups)
        self.game = game

        npc_candidates: list[str] = []
        if os.path.isdir(AssetPaths.NPC_VARIANTS_DIR):
            for name in os.listdir(AssetPaths.NPC_VARIANTS_DIR):
                candidate_path = os.path.join(AssetPaths.NPC_VARIANTS_DIR, name)
                if os.path.isfile(candidate_path) and name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    npc_candidates.append(candidate_path)

        npc_sprite_path = random.choice(npc_candidates) if npc_candidates else AssetPaths.PLAYER
        surface = pygame.image.load(npc_sprite_path).convert_alpha()
        self.image = pygame.transform.scale(surface, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))

        self.rect = self.image.get_rect(topleft=position)
        self.position = pygame.math.Vector2(position)

        # Fade state: stays solid until message finishes, then fades out.
        self.fade_pending = False
        self.fading = False
        self.fade_alpha = 255

    def animate(self) -> None:
        """Advance fade-out animation once any pending message has finished typing."""
        if self.fade_pending and not self.game.message_log.is_typing:
            self.fade_pending = False
            self.fading = True

        if self.fading:
            self.fade_alpha = max(0, self.fade_alpha - NPCSettings.FADE_SPEED)
            self.image.set_alpha(self.fade_alpha)
            if self.fade_alpha <= 0:
                self.kill()

    def update(self) -> None:
        """No-op update hook kept for sprite-group compatibility."""
        pass

class Door(pygame.sprite.Sprite):
    """Represent the level door sprite and open/closed visual states."""

    def __init__(self, game, position: tuple[int, int], groups) -> None:
        """Initialize the door sprite with open and closed states."""
        super().__init__(groups)
        self.game = game

        # Load and scale both versions of the door
        closed_surf = pygame.image.load(AssetPaths.CLOSED_DOOR).convert_alpha()
        open_surf = pygame.image.load(AssetPaths.OPEN_DOOR).convert_alpha()

        self.closed_image = pygame.transform.scale(closed_surf, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))
        self.open_image = pygame.transform.scale(open_surf, (GridSettings.TILE_SIZE, GridSettings.TILE_SIZE))

        self.image = self.closed_image
        self.rect = self.image.get_rect(topleft = position)
        self.position = pygame.math.Vector2(self.rect.topleft)

    def open_door(self) -> None:
        """Switch the visible sprite to the open-door texture."""
        self.image = self.open_image

    def update(self) -> None:
        """No-op per-frame update hook required by the sprite group API."""
        pass
