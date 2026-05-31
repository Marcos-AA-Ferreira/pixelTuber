from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QPushButton, QApplication)
from PySide6.QtCore import QTimer, Qt
from ui.tabs.audio_tab import AudioTab
from ui.tabs.avatar_tab import AvatarTab
# Import da ExtrasTab removido, pois agora é parte da AvatarTab
from ui.tabs.effects_tab import EffectsTab
from ui.tabs.settings_tab import SettingsTab
from ui.tabs.background_tab import BackgroundTab
from ui.tabs.help_tab import HelpTab

class ControlPanel(QWidget):
    def __init__(self, config_manager, audio, render, effects, hotkeys, overlay, bg_window):
        # Inicializado sem parent para ser uma janela totalmente independente
        super().__init__(None)
        
        # Título único para identificação no Sistema Operacional e OBS
        self.setWindowTitle("PixelTuber - Painel de Controle")
        
        # Configuração de Janela
        self.setWindowFlags(
            Qt.Window | 
            Qt.WindowStaysOnTopHint | 
            Qt.CustomizeWindowHint |
            Qt.WindowTitleHint | 
            Qt.WindowCloseButtonHint | 
            Qt.WindowMinMaxButtonsHint
        )
        
        self.config_manager = config_manager
        self.audio = audio
        self.render = render
        self.effects = effects
        self.hotkeys = hotkeys
        self.overlay = overlay
        self.bg_window = bg_window
        
        self.resize(600, 900)

        main_layout = QVBoxLayout(self)

        # --- BOTÃO SALVAR ---
        self.btn_save = QPushButton("💾 SALVAR TODAS AS CONFIGURAÇÕES")
        self.btn_save.setFixedHeight(45)
        self.btn_save.setStyleSheet("""
            QPushButton { 
                background-color: #28a745; 
                color: white; 
                font-weight: bold; 
                border-radius: 5px; 
            }
            QPushButton:hover { background-color: #218838; }
        """)
        self.btn_save.clicked.connect(self.save_settings)
        main_layout.addWidget(self.btn_save)

        # --- SISTEMA DE ABAS ---
        self.tabs = QTabWidget()
        
        # Instanciando abas
        # CORREÇÃO: Passando self.hotkeys para a AvatarTab (que agora gerencia os extras)
        self.avatar_tab = AvatarTab(self.config_manager, self.render, self.audio, self.hotkeys)
        
        self.settings_tab = SettingsTab(self.config_manager, self.render, self.hotkeys)
        self.audio_tab = AudioTab(self.config_manager, self.audio)
        self.effects_tab = EffectsTab(self.config_manager, self.effects, self.hotkeys)
        self.background_tab = BackgroundTab(self.config_manager, bg_window)
        self.help_tab = HelpTab()

        # Adicionando as abas ao widget (Extras removido pois está dentro de Avatar)
        self.tabs.addTab(self.avatar_tab, "👤 Avatar & Extras")
        self.tabs.addTab(self.settings_tab, "⚙️ Geral")
        self.tabs.addTab(self.audio_tab, "🎙 Áudio")
        self.tabs.addTab(self.effects_tab, "🚀 Efeitos")
        self.tabs.addTab(self.background_tab, "🖼️ Fundo")
        self.tabs.addTab(self.help_tab, "❓ Ajuda")
        
        main_layout.addWidget(self.tabs)

    def update_ui_feedback(self):
        """Sincroniza os elementos visuais das abas com o estado do motor."""
        if hasattr(self, 'audio_tab'):
            self.audio_tab.update_ui()
        
        if hasattr(self, 'avatar_tab'):
            self.avatar_tab.update_ui()

    def save_settings(self):
        """Salva permanentemente as posições e preferências no JSON."""
        self.config_manager.save()
        self.btn_save.setText("✅ CONFIGURAÇÕES SALVAS!")
        QTimer.singleShot(2000, lambda: self.btn_save.setText("💾 SALVAR TODAS AS CONFIGURAÇÕES"))

    def closeEvent(self, event):
        """Encerra o app inteiro ao fechar o painel."""
        QApplication.instance().quit()
        super().closeEvent(event)