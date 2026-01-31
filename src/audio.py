import pygame
import os
import threading

class AudioManager:
    def __init__(self, default_music_path=None):
        self.default_music_path = default_music_path
        self._current_music_path = default_music_path
        
        # Initialize mixer
        try:
            pygame.mixer.init()
            self._is_initialized = True
        except Exception as e:
            print(f"Audio init failed: {e}")
            self._is_initialized = False

    def set_music(self, path):
        """Sets the custom music path."""
        if os.path.exists(path):
            self._current_music_path = path
            return True
        return False

    def play(self, loops=-1):
        """Plays the current music. Loops infinitely by default."""
        if not self._is_initialized:
            return

        try:
            # Try loading custom/current music
            if self._current_music_path and os.path.exists(self._current_music_path):
                pygame.mixer.music.load(self._current_music_path)
                pygame.mixer.music.play(loops)
            else:
                print(f"Music file not found: {self._current_music_path}")
                # Fallback logic could go here
        except Exception as e:
            print(f"Error playing music: {e}")

    def stop(self):
        """Stops playback."""
        if self._is_initialized:
            pygame.mixer.music.stop()

    def set_volume(self, volume):
        """Sets volume (0.0 to 1.0)."""
        if self._is_initialized:
            pygame.mixer.music.set_volume(volume)
