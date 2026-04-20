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
            logging.error(f"Audio init failed: {e}")
            self._is_initialized = False

    def set_music(self, path):
        """Sets the custom music path."""
        if os.path.exists(path):
            self._current_music_path = path
            return True
        return False

    def play(self, path=None, loops=-1):
        """Plays music. If path is provided, it updates current music and plays. Loops infinitely by default."""
        if not self._is_initialized:
            return

        target = path or self._current_music_path
        if not target or not os.path.exists(target):
            logging.error(f"Music file not found: {target}")
            return

        try:
            pygame.mixer.music.load(target)
            pygame.mixer.music.play(loops)
            if path:
                self._current_music_path = path
        except Exception as e:
            logging.error(f"Error playing music: {e}")

    def stop(self):
        """Stops playback."""
        if self._is_initialized:
            pygame.mixer.music.stop()

    def set_volume(self, volume):
        """Sets volume (0.0 to 1.0)."""
        if self._is_initialized:
            pygame.mixer.music.set_volume(volume)
