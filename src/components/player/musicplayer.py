import platform
import os
import sys
from typing import Optional

from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import Qt, QObject, QTimer
from PySide6.QtGui import QAction
import vlc


class MusicPlayer(QObject):
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.vlc_instance = vlc.Instance("--no-xlib --no-video")
        self.media: Optional[vlc.Media] = None
        self.is_paused: bool = True
        self.media_player = self.vlc_instance.media_player_new()
        self.media_player.set_fullscreen(False)  # Optional, just in case fullscreen mode is enabled
        self.media_player.set_xwindow(0)  # Disable video output on specific window (useful on some systems)
        self.active_filters = set()  # Store enabled effects
        self.normalization_enabled = True
        self.equalizer = None
        self.init_preset_list()
        # Optional: Uncomment if you want to use a timer for periodic updates
        # self.timer = QTimer(self)
        # self.timer.setSingleShot(True)
        # self.timer.setInterval(500)
        # self.timer.timeout.connect(self.update_playback_status)
        
    def init_preset_list(self) -> list:
        """List all available VLC equalizer presets."""
        index = 0
        self.presets = []

        while True:
            preset_name = vlc.libvlc_audio_equalizer_get_preset_name(index)
            if preset_name is None:
                break  # Stop when VLC runs out of presets
            self.presets.append(preset_name.decode())
            index += 1

    def set_media(self, file_path: str) -> None:
        """Load a media file from the given path."""
        self.media = self.vlc_instance.media_new(file_path)
        self.media.parse()
        self.media_player.set_media(self.media)
        if self.normalization_enabled:
            self.media.add_option(":audio-filter=normvol")
        # self.play()
        # self.pause()

    def play(self) -> None:
        """Play the loaded media only if not already playing."""
        state = self.media_player.get_state()

        if state in [vlc.State.Playing, vlc.State.Buffering]:
            print("Media is already playing.")
            return

        if self.media_player.play() == -1:
            print("Error: Unable to play media.")
            return

        self.is_paused = False
        print(f"Current Time: {self.media_player.get_time()} ms")

    def pause(self) -> None:
        """Pause the currently playing media."""
        if self.media_player.get_state() == vlc.State.Playing:
            self.media_player.pause()
            self.is_paused = True

    def stop(self) -> None:
        """Stop the media playback."""
        self.media_player.stop()
        self.is_paused = True

    def set_volume(self, volume: int) -> None:
        """Set the volume level (0-100)."""
        if 0 <= volume <= 100:
            self.media_player.audio_set_volume(volume)
        else:
            print("Error: Volume must be between 0 and 100.")

    def get_volume(self) -> int:
        """Get the current volume level."""
        return self.media_player.audio_get_volume()

    def get_state(self) -> vlc.State:
        """Get the current state of the media player."""
        return self.media_player.get_state()

    def get_position(self) -> float:
        """Get the current playback position (0.0 to 1.0)."""
        return self.media_player.get_position()

    def get_length(self) -> int:
        """Get the total length of the media in milliseconds."""
        return self.media_player.get_length()
    
    def get_duration(self) -> int:
        """Get the total duration of the media in milliseconds."""
        return self.media.get_duration()
    
    def toggle_play_pause(self) -> None:
        """Toggle between play and pause states."""
        if self.media_player.get_state() == vlc.State.Playing:
            self.pause()
        else:
            self.play()

    def get_time(self) -> int:
        """Get the current playback time in milliseconds."""
        return self.media_player.get_time()
    
    def set_time(self, time_ms: int) -> None:
        """Set the current playback time in milliseconds."""
        print(self.media_player.set_time(time_ms))

    def get_title(self) -> str:
        """Get the title of the currently playing media."""
        return self.media.get_meta(vlc.Meta.Title) or "Unknown Title"

    def get_artist(self) -> str:
        """Get the artist of the currently playing media."""
        return self.media.get_meta(vlc.Meta.Artist) or "Unknown Artist"
    
    def set_position(self, value):
        """Set the playback position (0.0 to 1.0)."""
        self.media_player.set_position(value)
        
    def set_state(self, state: vlc.State):
        """Set the state of the media player."""
        self.media_player.set_state(state)
        
    def set_playback_speed(self, speed: float):
        """Set the playback speed (e.g., 1.0 for normal speed)."""
        print(speed)
        self.media_player.set_rate(speed)
        
    def enable_effect(self, effect_name: str):
        """Enable an audio effect and update the filter list."""
        self.active_filters.add(effect_name)
        self._apply_filters()    
        
    def disable_effect(self, effect_name: str):
        """Disable a specific audio effect."""
        if effect_name in self.active_filters:
            self.active_filters.remove(effect_name)
            self._apply_filters()
            
    def _apply_filters(self):
        """Apply all active filters to VLC."""
        if self.media:
            filter_string = ",".join(self.active_filters)  # Join effects
            self.media.add_option(f":audio-filter={filter_string}")
            print(f"Applied filters: {filter_string}")
            previous_time = self.media_player.get_time()
            self.media_player.set_media(self.media)
            if not self.is_paused:
                self.media_player.play()
                if previous_time and previous_time > 0:
                    self.media_player.set_time(previous_time)

    def set_equalizer(self, preset: Optional[int] = None, bands: Optional[dict] = None) -> None:
        """
        Apply an equalizer preset or custom band values.
        :param preset: Index of VLC equalizer preset (e.g., "Rock", "Jazz").
        :param bands: Dictionary of band adjustments {band_index: value}.
        """
        if preset is not None:
            # Default to the first preset if not found
            preset = min(preset, len(self.presets) - 1)
            self.equalizer = vlc.libvlc_audio_equalizer_new_from_preset(preset)
        else:
            
            self.equalizer = vlc.AudioEqualizer()  # Create a new equalizer instance
            if bands:
                for band, value in bands.items():
                    self.equalizer.set_amp_at_index(value, band)

        self.media_player.set_equalizer(self.equalizer)
        print(f"Equalizer set: {preset if preset else 'Custom'}")
        
    def get_preset_band_values(self, preset_index: str)->dict:
        """Returns band values for a given preset name."""

        preset_index = min(preset_index, len(self.presets) - 1)
        equalizer = vlc.libvlc_audio_equalizer_new_from_preset(preset_index)
        
        band_values = {}
        for band_index in range(10):  # VLC has 10 bands
            band_values[band_index] = vlc.libvlc_audio_equalizer_get_amp_at_index(equalizer, band_index)
        
        return band_values
    
    def get_preset_list(self) -> list:
        """List all available VLC equalizer presets."""
        return self.presets

    def disable_equalizer(self) -> None:
        """Disable the equalizer effect."""
        self.media_player.set_equalizer(None)
        print("Equalizer disabled")
    
    def set_stereo_effect(self, enable: bool) -> None:
        """Enable or disable stereo effect."""
        if enable:
            self.enable_effect("stereo_widen")
        else:
            self.disable_effect("stereo_widen")
            
    def set_echo(self, enable: bool, delay: int = 1000, decay: float = 0.3):
        """Enable or disable echo effect."""
        if enable:
            self.enable_effect("aecho")
            self.media.add_option(f":aecho-delay={delay}")   # Delay in ms
            self.media.add_option(f":aecho-decay={decay}") 
        else:
            self.disable_effect("aecho")
            
    def set_reverb(self, enable: bool):
        """Enable or disable reverb effect."""
        if enable:
            self.enable_effect("extrastereo")
            self.media.add_option(":reverb-delay=1000")   # Delay in ms
            self.media.add_option(":reverb-decay=0.3")
        else:
            self.disable_effect("reverb")
            
    def set_normalization(self, enable: bool):
        """Enable or disable normalization effect."""
        self.normalization_enabled = enable
        if enable:
            self.enable_effect("normvol")
        else:
            self.disable_effect("normvol")
            
    def disable_audio_effects(self):
        """Remove all audio filters and reset equalizer."""
        self.active_filters.clear()
        self.media.add_option(":audio-filter=")  # Clear filters
        self.media_player.set_equalizer(None)  # Remove EQ settings
        print("Audio Effects Disabled")
        
    def cleanup(self) -> None:
        """Release resources before destruction."""
        self.stop()
        self.media_player.release()
        self.vlc_instance.release()

# Example usage:
# print(list_equalizer_presets())
    
if(__name__ == "__main__"):
    import time
    from loguru import logger
    player = MusicPlayer()
    song = r"D:\Program\Musify\Sample Songs\Song\T-Series Bollywood Classics - Hum Tumko Nigahon Mein Lyrical Video ｜ Garv-Pride & Honour ｜ Udit N,Shreya G｜Salman Khan, Shilpa S.m4a"
    # player.media_player.audio_filter_set("normvol", True)
    player.set_media(song)
    player.set_volume(100)
    # player.set_echo(True)
    player.set_reverb(True)
    player.set_normalization(True)
    bands = {
    0: 5.0,  # Boost deep bass (60 Hz) by +5 dB
    1: 3.0,  # Boost bass (170 Hz) by +3 dB
    8: -4.0, # Reduce brightness (14 kHz) by -4 dB
    9: -5.0  # Reduce airiness (16 kHz) by -5 dB
}   
    print(player.get_preset_band_values(2))
    player.set_equalizer(0, bands)
    # player.disable_equalizer()
    # player.set_stereo_effect(True)
    
    
    # player.set_reverb(True)
    # player.play()
    # # player.pause()
    # logger.catch(lambda: player.play())
    # while player.get_state() != vlc.State.Ended:
    #     time.sleep(1)  # Check every second
    #     print(f"Current Time: {player.get_time()} ms")
    #     # if player.get_time() > 12000:
    #     #     print("duration: ", player.get_length())
    #     #     player.pause()
    #     #     break
    # # player.stop()
    
    logger.debug(f"Presets: {player.get_preset_list()}")
    # logger.debug(f"Rock index: {player.presets.index('rock')}")