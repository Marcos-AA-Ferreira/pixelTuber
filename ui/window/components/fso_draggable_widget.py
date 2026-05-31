import os
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QPoint, QTimer, QSize, Signal, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from ui.styles.theme import Theme
from ui.window.components.fso_media_player_widget import MediaPlayerWidget

class DraggableEffectWidget(QWidget):
    """
    Widget independente para efeitos que podem ser movidos pela tela.
    Lida com redimensionamento dinâmico e reprodução de mídia sincronizada.
    """
    moved = Signal(int, int) # Emite as coordenadas X e Y durante o arraste

    def __init__(self, parent=None, **kwargs):
        super().__init__(None) 
        
        # Flags para garantir que a janela fique no topo, sem bordas e sem sombra
        self.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | Qt.Tool | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose) # Auto-limpeza de memória
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Container de mídia (Vídeo, GIF ou Imagem)
        self.media_container = MediaPlayerWidget(self)
        self.layout.addWidget(self.media_container)

        # Sistema de áudio local do efeito
        self.audio_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.audio_player.setAudioOutput(self.audio_output)

        self._drag_pos = QPoint()
        self.setup_effect(kwargs)

    def setup_effect(self, data):
        """
        Configura as propriedades visuais, escala e áudio do efeito.
        """
        path = data.get("path")
        scale = float(data.get("scale", 1.0))
        duration = int(data.get("duration", 4000))
        opacity = float(data.get("opacity", 1.0))
        
        # 1. CÁLCULO DE TAMANHO (ESCALA)
        # Usa o tamanho base do avatar definido no tema para calcular a proporção
        base_size = getattr(Theme, "BASE_AVATAR_SIZE", 300)
        size_val = int(base_size * max(0.1, scale))
        
        # Define o tamanho real da janela com base na escala
        self.setFixedSize(size_val, size_val)
        self.setWindowOpacity(opacity)
        
        # Posicionamento inicial
        self.move(int(data.get("x", 0)), int(data.get("y", 0)))

        # 2. COMPONENTE VISUAL
        if path and os.path.exists(path):
            # Passamos o novo tamanho escalado para o player redimensionar a mídia
            self.media_container.play(path, QSize(size_val, size_val))

        # 3. COMPONENTE DE ÁUDIO
        a_path = data.get("audio_path")
        if a_path and os.path.exists(a_path):
            start = float(data.get("audio_start", 0.0))
            end = float(data.get("audio_end", 0.0))
            
            self.audio_player.setSource(QUrl.fromLocalFile(os.path.abspath(a_path)))
            
            # Delay curto para garantir o carregamento antes de definir o tempo de início
            QTimer.singleShot(50, lambda: self.audio_player.setPosition(int(start * 1000)))
            self.audio_player.play()
            
            # Se houver um fim definido, agenda a parada
            if end > start:
                play_ms = int((end - start) * 1000)
                QTimer.singleShot(play_ms, self.audio_player.stop)

        # 4. VIDA ÚTIL
        # O efeito se auto-destrói após a duração para poupar recursos
        QTimer.singleShot(max(500, duration), self.close)
        self.show()

    # --- Lógica de Arraste ---

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            self.move(new_pos)
            # Emite sinal capturado pela Overlay para salvar a posição no JSON
            self.moved.emit(new_pos.x(), new_pos.y())
            event.accept()