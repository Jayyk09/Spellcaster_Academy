"""Sound manager for game audio - music and sound effects."""
import os
import random
import pygame
from config.settings import SOUNDS_DIR


class SoundManager:
    """Manages all game audio: background music and sound effects."""

    def __init__(self):
        self._initialized = False
        self._sounds = {}
        self._current_music = None
        self._music_volume = 0.4
        self._sfx_volume = 0.6

        try:
            pygame.mixer.init()
            self._initialized = True
            self._load_sounds()
        except Exception as e:
            print(f"Sound init failed: {e}")

    def _load_sounds(self):
        """Load all sound effect files."""
        if not self._initialized:
            return

        spells_dir = os.path.join(SOUNDS_DIR, 'Spells')

        # Spell type -> list of sound files
        spell_map = {
            'fireball': ['Fireball 1.wav', 'Fireball 2.wav', 'Fireball 3.wav'],
            'ice': ['Ice Barrage 1.wav', 'Ice Barrage 2.wav', 'Ice Throw 1.wav', 'Ice Throw 2.wav'],
            'earth': ['Rock Meteor Throw 1.wav', 'Rock Meteor Throw 2.wav', 'Rock Meteor Swarm 1.wav'],
            'nature': ['Waterspray 1.wav', 'Waterspray 2.wav'],
            'air': ['Wave Attack 1.wav', 'Wave Attack 2.wav'],
            'arcane': ['Spell Impact 1.wav', 'Spell Impact 2.wav', 'Spell Impact 3.wav'],
            'lightning': ['Firespray 1.wav', 'Firespray 2.wav'],
        }

        for spell_type, filenames in spell_map.items():
            sounds = []
            for fname in filenames:
                path = os.path.join(spells_dir, fname)
                snd = self._load_sound(path)
                if snd:
                    sounds.append(snd)
            if sounds:
                self._sounds[f'spell_{spell_type}'] = sounds

        # Sword attack (skeleton melee)
        sword_snd = self._load_sound(os.path.join(SOUNDS_DIR, 'Sword Attack.ogg'))
        if sword_snd:
            self._sounds['sword_attack'] = [sword_snd]

        # Undine spell cast
        undine_sounds = []
        for fname in ['Wave Attack 1.wav', 'Wave Attack 2.wav']:
            snd = self._load_sound(os.path.join(spells_dir, fname))
            if snd:
                undine_sounds.append(snd)
        if undine_sounds:
            self._sounds['undine_spell'] = undine_sounds

        # Lich lightning
        lich_sounds = []
        for fname in ['Firespray 1.wav', 'Firespray 2.wav']:
            snd = self._load_sound(os.path.join(spells_dir, fname))
            if snd:
                lich_sounds.append(snd)
        if lich_sounds:
            self._sounds['lich_lightning'] = lich_sounds

        # Spell impact (when spell hits enemy)
        impact_sounds = []
        for fname in ['Spell Impact 1.wav', 'Spell Impact 2.wav', 'Spell Impact 3.wav']:
            snd = self._load_sound(os.path.join(spells_dir, fname))
            if snd:
                impact_sounds.append(snd)
        if impact_sounds:
            self._sounds['spell_impact'] = impact_sounds

    def _load_sound(self, path: str) -> pygame.mixer.Sound | None:
        """Load a single sound file, returning None on failure."""
        try:
            return pygame.mixer.Sound(path)
        except Exception as e:
            print(f"Could not load sound {path}: {e}")
            return None

    def _play_random(self, key: str, volume: float | None = None):
        """Play a random sound from the given key's sound list."""
        if not self._initialized:
            return
        sounds = self._sounds.get(key)
        if sounds:
            snd = random.choice(sounds)
            snd.set_volume(volume if volume is not None else self._sfx_volume)
            snd.play()

    # ── Music ────────────────────────────────────────────────────────────

    def play_theme(self):
        """Play the main theme music (loops)."""
        self._play_music(os.path.join(SOUNDS_DIR, 'theme.wav'), loops=-1)

    def play_final_battle(self):
        """Play the final boss battle music (loops)."""
        self._play_music(os.path.join(SOUNDS_DIR, 'Final_Battle.wav'), loops=-1)

    def play_victory(self):
        """Play the victory music after winning."""
        self._play_music(os.path.join(SOUNDS_DIR, 'After_Victory.wav'), loops=0)

    def play_game_over(self):
        """Play game over music when player dies."""
        self._play_music(os.path.join(SOUNDS_DIR, 'gane_over.wav'), loops=0)

    def play_after_battle(self):
        """Play the after-battle music (wave cleared, then resume theme)."""
        self._play_music(os.path.join(SOUNDS_DIR, 'After_Victory.wav'), loops=0)

    def stop_music(self):
        """Stop current background music."""
        if not self._initialized:
            return
        try:
            pygame.mixer.music.stop()
            self._current_music = None
        except Exception:
            pass

    def _play_music(self, path: str, loops: int = -1):
        """Load and play a music track."""
        if not self._initialized:
            return
        if self._current_music == path:
            return  # Already playing
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self._music_volume)
            pygame.mixer.music.play(loops)
            self._current_music = path
        except Exception as e:
            print(f"Could not play music {path}: {e}")

    # ── Sound Effects ────────────────────────────────────────────────────

    def play_spell_sound(self, spell_type: str):
        """Play a sound matching the spell type when player casts."""
        self._play_random(f'spell_{spell_type}')

    def play_sword_attack(self):
        """Play sword attack sound (skeleton melee hit)."""
        self._play_random('sword_attack')

    def play_undine_spell(self):
        """Play undine spell cast sound."""
        self._play_random('undine_spell', volume=0.4)

    def play_lich_lightning(self):
        """Play lich lightning attack sound."""
        self._play_random('lich_lightning')

    def play_spell_impact(self):
        """Play spell impact sound (when spell hits enemy)."""
        self._play_random('spell_impact', volume=0.5)


# Module-level singleton
sound_manager = SoundManager()
