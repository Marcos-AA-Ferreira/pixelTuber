import os
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl, QTimer, QObject, Signal
from core.utils import validate_path

class EffectManager(QObject):
    positionUpdated = Signal(str, int, int)

    def __init__(self, overlay_window, media_service):
        super().__init__()
        self.overlay = overlay_window
        self.media_service = media_service
        
        self.overlay.effectPositionChanged.connect(self._handle_position_change)

    def play_effect(self, config):
        """Recebe o dicionário via EventBus e processa o disparo."""
        effect_id = config.get("effect_id", "preview")
        
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
            # ✅ DELEGUE AO SERVIÇO:
            self.media_service.play(
                path=audio,
                start_sec=config.get("audio_start", 0.0),
                end_sec=config.get("audio_end", 0.0)
            )

    def _handle_position_change(self, eid, x, y):
        """
        Recebe a nova posição da Overlay e repassa para a EffectsTab salvar.
        """
        self.positionUpdated.emit(eid, x, y)

    def stop_all(self):
        """Interrompe todos os sons e limpa a Overlay."""
        self.audio_player.stop()
        self.overlay.stop_all()