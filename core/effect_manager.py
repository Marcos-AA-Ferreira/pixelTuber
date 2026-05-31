import os
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl, QTimer, QObject, Signal
from core.utils import validate_path

class EffectManager(QObject):
    """
    Controlador de alto nível para disparar efeitos visuais e sonoros.
    Faz a ponte entre a lógica de negócio e a FullScreenOverlay.
    """
    # Avisa quando um efeito Draggable foi movido para podermos salvar X e Y
    # Agora inclui o effect_id para sabermos qual entrada no JSON atualizar
    positionUpdated = Signal(str, int, int) # effect_id, x, y

    def __init__(self, overlay_window):
        super().__init__()
        self.overlay = overlay_window
        
        # Conecta o sinal de movimento que vem da Overlay (UI) para este Manager
        # A Overlay agora passará (str, int, int) -> id, x, y
        self.overlay.effectPositionChanged.connect(self._handle_position_change)
        
        # Player dedicado para sons sem imagem
        self.audio_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.audio_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)

    def play_effect(self, effect_id="preview", **kwargs):
        """
        Recebe os argumentos da aba de efeitos e processa o disparo.
        Suporta chamadas como: play_effect(id, visual_path="...", duration=1000)
        """
        config = kwargs
        
        # Mapeamento de compatibilidade
        if "visual_path" in config:
            config["path"] = config.pop("visual_path")
            
        visual = config.get("path")
        audio = config.get("audio_path")
        
        # Se houver um caminho visual válido, envia para a Overlay
        if validate_path(visual):
            # Injetamos o ID na config para que o Widget saiba quem ele é ao ser movido
            config["effect_id"] = effect_id
            self.overlay.play_custom_effect(config)
        
        # Se for apenas áudio
        elif validate_path(audio):
            self._play_standalone_audio(
                audio, 
                config.get("audio_start", 0.0),
                config.get("audio_end", 0.0)
            )

    def _play_standalone_audio(self, path, start, end):
        """Executa áudio sem componente visual."""
        self.audio_player.stop()
        self.audio_player.setSource(QUrl.fromLocalFile(os.path.abspath(path)))
        
        # Pequena pausa para garantir que o arquivo foi indexado
        QTimer.singleShot(20, lambda: self.audio_player.setPosition(int(start * 1000)))
        self.audio_player.play()
        
        if end > start:
            duration_ms = int((end - start) * 1000)
            QTimer.singleShot(duration_ms, self.audio_player.stop)

    def _handle_position_change(self, eid, x, y):
        """
        Recebe a nova posição da Overlay e repassa para a EffectsTab salvar.
        """
        self.positionUpdated.emit(eid, x, y)

    def stop_all(self):
        """Interrompe todos os sons e limpa a Overlay."""
        self.audio_player.stop()
        self.overlay.stop_all()