import os
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QSize, Signal

from ui.window.components.fso_media_player_widget import MediaPlayerWidget
from ui.window.components.fso_draggable_widget import DraggableEffectWidget

class FullScreenOverlay(QWidget):
    """
    Gestor Central de Efeitos. 
    Lida com efeitos de ecrã inteiro e gere janelas de efeitos arrastáveis.
    """
    # Sinal atualizado para incluir o ID do efeito: (id, x, y)
    effectPositionChanged = Signal(str, int, int)

    def __init__(self):
        super().__init__()
        
        # Configuração Base: Invisível e ignora cliques (pass-through) por padrão
        self.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput | Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Componente para Efeitos Fixos (tela cheia)
        self.full_screen_media = MediaPlayerWidget(self)
        
        # Lista de Controlo para Efeitos Draggable Ativos
        self._active_effects = []

        self.showFullScreen()

    # ================================================================
    # LÓGICA PARA EFEITOS FIXOS (FULL SCREEN)
    # ================================================================
    def play_static_effect(self, visual_path=None, duration=4000, opacity=1.0):
        """Reproduz um efeito visual estático que ocupa o ecrã inteiro."""
        self.full_screen_media.hide_all()
        self.setWindowOpacity(opacity)
        
        if visual_path and os.path.exists(visual_path):
            self.full_screen_media.setGeometry(self.rect())
            self.full_screen_media.play(visual_path, self.size())

        QTimer.singleShot(duration, self.full_screen_media.hide_all)

    # ================================================================
    # LÓGICA PARA EFEITOS INTERATIVOS (DRAGGABLE)
    # ================================================================
    def play_custom_effect(self, config):
        """
        Cria e gere uma nova janela de efeito interativa.
        """
        eid = config.get("effect_id", "preview")
        
        effect_win = DraggableEffectWidget(
            path=config.get("path"),
            duration=config.get("duration", 4000),
            scale=config.get("scale", 1.0),
            opacity=config.get("opacity", 1.0),
            x=config.get("x", 0),
            y=config.get("y", 0),
            audio_path=config.get("audio_path"),
            audio_start=config.get("audio_start", 0.0),
            audio_end=config.get("audio_end", 0.0)
        )

        # Conecta o sinal de movimento repassando o ID do efeito
        effect_win.moved.connect(lambda x, y, id=eid: self.effectPositionChanged.emit(id, x, y))
        
        # Monitoriza a destruição para limpar a lista
        effect_win.destroyed.connect(lambda: self._cleanup_effect(effect_win))
        
        self._active_effects.append(effect_win)

    def _cleanup_effect(self, win):
        """Remove a referência da lista quando o efeito fecha."""
        if win in self._active_effects:
            self._active_effects.remove(win)

    # ================================================================
    # GESTÃO DE ESTADO
    # ================================================================
    def stop_all(self):
        """Para todos os efeitos globais e fecha todas as janelas de efeitos ativas."""
        self.full_screen_media.hide_all()
        
        for effect in self._active_effects[:]:
            try:
                effect.close()
            except:
                pass
        self._active_effects.clear()