from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import Qt

from ui.window.components.bg_content_widget import BgContentWidget
from ui.window.components.bg_audio_manager import BgAudioManager

class BackgroundWindow(QWidget):
    def __init__(self):
        super().__init__(None)
        self.setWindowTitle("PixelTuber - Background")
        
        # Inicia ocupando a tela primária por padrão
        screen = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        self.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | 
            Qt.WindowTransparentForInput | Qt.WindowStaysOnBottomHint |
            Qt.CustomizeWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating) # Não rouba o foco ao abrir

        # Layout para garantir que o widget visual preencha a janela toda (CORREÇÃO DO FUNDO SUMIDO)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Instancia Componentes
        self.visual = BgContentWidget(self)
        self.audio = BgAudioManager(self)
        
        self.main_layout.addWidget(self.visual)

    def set_layer_level(self, level):
        """
        Define a profundidade da janela:
        0 = Fundo (Atrás de tudo)
        2 = Frente (Sobre o avatar)
        """
        self.setWindowFlag(Qt.WindowStaysOnBottomHint, level == 0)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, level == 2)
        if self.isVisible(): self.show() # Força atualização das flags

    def update_background(self, config_data):
        """Atualiza visual e áudio com base no dicionário de configuração."""
        # Configurações Visuais
        path = config_data.get("path")
        width = config_data.get("width", self.width())
        height = config_data.get("height", self.height())
        opacity = config_data.get("opacity", 100)
        blur = config_data.get("blur", 0)

        self.setFixedSize(width, height)
        self.setWindowOpacity(opacity / 100)
        self.visual.update_visual(path, width, height, blur)

        # Configurações de Áudio
        audio_path = config_data.get("audio_path")
        volume = config_data.get("volume", 50)
        muted = config_data.get("muted", False)
        loop = config_data.get("loop", True) # Pega o estado do loop
        
        self.audio.update_playback(audio_path, volume, muted, loop)
        
        if path or audio_path:
            self.show()
        else:
            self.hide()