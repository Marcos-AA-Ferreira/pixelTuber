from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QPushButton, QApplication)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QIcon

from ui.tabs.audio_tab import AudioTab
from ui.tabs.avatar_tab import AvatarTab
from ui.tabs.effects_tab import EffectsTab
from ui.tabs.settings_tab import SettingsTab
from ui.tabs.background_tab import BackgroundTab
from ui.tabs.help_tab import HelpTab

class ControlPanel(QWidget):

    def __init__(self, config_manager):
        super().__init__(None)
        
        self.setWindowTitle("PixelTuber - Painel de Controle")
        self.setWindowIcon(QIcon("assets/PAINEL-DE-CONTROLE_ICON.ico"))
        
        self.setWindowFlags(
            Qt.Window | Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint | 
            Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint
        )
        
        self.config_manager = config_manager
        self.resize(600, 900)

        main_layout = QVBoxLayout(self)
        
        # --- SISTEMA DE ABAS ---
        self.tabs = QTabWidget()
        
        # Nenhuma aba recebe managers a partir de agora
        self.avatar_tab = AvatarTab(self.config_manager)
        self.settings_tab = SettingsTab(self.config_manager)
        self.audio_tab = AudioTab(self.config_manager)
        self.effects_tab = EffectsTab(self.config_manager)
        self.background_tab = BackgroundTab(self.config_manager)
        self.help_tab = HelpTab()
        
        self.tabs.addTab(self.avatar_tab, "👤 Avatar & Extras")
        self.tabs.addTab(self.settings_tab, "⚙️ Geral")
        self.tabs.addTab(self.audio_tab, "🎙 Áudio")
        self.tabs.addTab(self.effects_tab, "🚀 Efeitos")
        self.tabs.addTab(self.background_tab, "🖼️ Fundo")
        self.tabs.addTab(self.help_tab, "❓ Ajuda")
        
        main_layout.addWidget(self.tabs)

    def update_ui_feedback(self):
        
        if hasattr(self, 'avatar_tab'):
            self.avatar_tab.update_ui()

    def save_settings(self):
        """Salva permanentemente as posições e preferências no JSON."""
        self.config_manager.save()
        self.btn_save.setText("✅ CONFIGURAÇÕES SALVAS!")
        QTimer.singleShot(2000, lambda: self.btn_save.setText("💾 SALVAR TODAS AS CONFIGURAÇÕES"))

    def closeEvent(self, event):
        """Verifica a configuração de Tray antes de decidir se oculta ou encerra o app."""
        minimize_to_tray = self.config_manager.data.get("system", {}).get("minimize_to_tray", False)
        
        if minimize_to_tray:
            self.hide()
            event.ignore() # Impede o fechamento real, apenas oculta a interface
        else:
            QApplication.instance().quit()
            super().closeEvent(event)