from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl, QObject
import os
from core.utils import validate_path

class BgAudioManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_output = QAudioOutput(self)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio_output)

    def update_playback(self, path, volume, muted, loop=True):
        self.audio_output.setVolume(volume / 100.0)
        self.audio_output.setMuted(muted)

        if not validate_path(path):
            self.player.stop()
            return

        # Configura Loop dinamicamente
        self.player.setLoops(QMediaPlayer.Loops.Infinite if loop else 1)

        # Só altera a fonte e dá Play se o caminho mudou
        current_source = self.player.source().toLocalFile()
        # Normaliza caminhos para comparação
        if os.path.normpath(current_source) != os.path.normpath(path):
            self.player.setSource(QUrl.fromLocalFile(path))
            self.player.play()