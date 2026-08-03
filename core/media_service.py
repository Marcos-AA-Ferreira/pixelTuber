# core/media_service.py
import os
from PySide6.QtCore import QObject, Signal, QUrl, QTimer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

class PooledPlayer(QObject):
    """Encapsula um QMediaPlayer e QAudioOutput, gerenciando sua própria reciclagem."""
    finished = Signal(object)  # Emite a si mesmo quando termina de tocar

    def __init__(self, parent=None):
        super().__init__(parent)
        self.player = QMediaPlayer(self)
        self.output = QAudioOutput(self)
        self.player.setAudioOutput(self.output)
        
        # Timer para lidar com cortes de áudio (start/end)
        self._stop_timer = QTimer(self)
        self._stop_timer.setSingleShot(True)
        self._stop_timer.timeout.connect(self.stop)
        
        self.player.playbackStateChanged.connect(self._on_state_changed)

    def play_audio(self, path: str, volume: float = 1.0, start_sec: float = 0.0, end_sec: float = 0.0):
        self.output.setVolume(volume)
        self.player.setSource(QUrl.fromLocalFile(os.path.abspath(path)))
        
        if start_sec > 0:
            # QTimer para garantir que o arquivo carregou antes de pular a posição
            QTimer.singleShot(20, lambda: self.player.setPosition(int(start_sec * 1000)))
            
        self.player.play()
        
        if end_sec > start_sec:
            duration_ms = int((end_sec - start_sec) * 1000)
            self._stop_timer.start(max(100, duration_ms))

    def stop(self):
        self._stop_timer.stop()
        self.player.stop()

    def _on_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.finished.emit(self)


class MediaService(QObject):
    """Gerencia um Pool de instâncias de mídia para economizar RAM e CPU."""
    
    def __init__(self, pool_size=5, parent=None):
        super().__init__(parent)
        self._pool = []
        self._active = []
        
        # Pré-aloca os motores na memória
        for _ in range(pool_size):
            self._create_new_player()

    def _create_new_player(self):
        p = PooledPlayer(self)
        p.finished.connect(self._on_player_finished)
        self._pool.append(p)
        return p

    def play(self, path: str, volume: float = 1.0, start_sec: float = 0.0, end_sec: float = 0.0):
        if not self._pool:
            # Se a piscina esgotar (muitos sons simultâneos), aloca dinamicamente mais um
            # Em sistemas restritos, você poderia ignorar ou forçar a parada do mais antigo
            print("⚠️ Pool de mídia esgotado, alocando player extra.")
            self._create_new_player()
            
        player = self._pool.pop(0)
        self._active.append(player)
        player.play_audio(path, volume, start_sec, end_sec)

    def _on_player_finished(self, player):
        """Recicla o player devolvendo-o para a piscina."""
        if player in self._active:
            self._active.remove(player)
            self._pool.append(player)

    def stop_all(self):
        for player in self._active[:]:
            player.stop()