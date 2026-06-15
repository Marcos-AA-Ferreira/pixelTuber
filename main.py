import sys
import ctypes
import os
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QTimer

# --- Importação dos Gerenciadores do Core ---
from core.config_manager import ConfigManager
from core.audio_manager import AudioManager
from core.animation_manager import AnimationManager
from core.hotkey_manager import HotkeyManager
from core.effect_manager import EffectManager
from core.utils import validate_path

# --- Importação das Interfaces (UI) ---
from ui.window.render_window import RenderWindow
from ui.window.fullscreen_overlay import FullScreenOverlay
from ui.window.background_window import BackgroundWindow
from ui.control_panel import ControlPanel

try:
    # ID único para evitar agrupamento na barra de tarefas do Windows
    myappid = 'pixeltuber.standalone.v2'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    # Silencia avisos desnecessários de codecs no console
    os.environ["QT_LOGGING_RULES"] = "qt.multimedia.ffmpeg=false;qt.multimedia.playbackengine.codec=false"
except:
    pass

class PixelTuberApp:
    def __init__(self):
        # 1. Carregar Configurações e Perfis
        self.config = ConfigManager()
        
        # 2. Inicializar Motores de Áudio e Animação
        audio_cfg = self.config.data.get("audio", {})
        self.audio = AudioManager(
            device_index=audio_cfg.get("device"),
            gain=audio_cfg.get("gain", 1.0)
        )
        self.anim_logic = AnimationManager(self.config)
        
        # 3. Inicializar Janelas de Interface
        self.bg_window = BackgroundWindow()
        self.render = RenderWindow(self.config)
        self.overlay = FullScreenOverlay()
        
        # 4. Inicializar Gerenciadores de Lógica Adicional
        self.effects = EffectManager(self.overlay)
        
        self.hotkeys = HotkeyManager(self.config, self.render, self.overlay)
        self.hotkeys.setup_defaults()
        
        # 5. Interface de Controle (Painel de Configurações)
        self.panel = ControlPanel(
            self.config, 
            self.audio, 
            self.render, 
            self.effects, 
            self.hotkeys,
            overlay=self.overlay,
            bg_window=self.bg_window
        )
        
        # 6. Configuração da Bandeja do Sistema (System Tray)
        self.setup_tray()
        
        # 7. Aplicação do Estado Inicial
        self.audio.start()
        
        bg_path = self.config.data.get("bg_path")
        if validate_path(bg_path):
            self.bg_window.set_background(bg_path)

        # 8. Exibição das Janelas
        self.bg_window.show()
        self.render.show()
        self.overlay.show()
        
        # Só exibe o painel se não estiver configurado para iniciar minimizado (opcional futuro)
        self.panel.show()
        self.panel.raise_()

        # 9. Loop Principal de Sincronização
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)
        
        # Aplica o FPS inicial salvo
        self.apply_fps_limit()
        
        # Contador de frames para evitar leitura de disco excessiva
        self.frame_count = 0

    def setup_tray(self):
        """Configura o ícone e o menu na bandeja do sistema (perto do relógio)."""
        self.tray_icon = QSystemTrayIcon(QIcon("assets\AVATAR_ICON.ico"), QApplication.instance())
        self.tray_icon.setToolTip("PixelTuber")
        
        menu = QMenu()
        
        show_action = QAction("Abrir Painel de Controle", menu)
        show_action.triggered.connect(self.show_panel)
        menu.addAction(show_action)
        
        menu.addSeparator()
        
        quit_action = QAction("Sair do PixelTuber", menu)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.tray_activation)
        self.tray_icon.show()

    def tray_activation(self, reason):
        """Restaura o painel com duplo clique no ícone da bandeja."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_panel()

    def show_panel(self):
        self.panel.showNormal()
        self.panel.raise_()
        self.panel.activateWindow()

    def apply_fps_limit(self):
        """Lê a configuração e ajusta a taxa de atualização do motor principal."""
        fps_setting = self.config.data.get("system", {}).get("fps_limit", "60 FPS")
        fps_map = {"30 FPS": 33, "60 FPS": 16, "120 FPS": 8}
        
        # Evita resetar o timer se não houve mudança
        interval = fps_map.get(fps_setting, 16)
        if not self.timer.isActive() or self.timer.interval() != interval:
            self.timer.start(interval)

    def update_loop(self):
        """Atualiza a lógica visual a cada frame."""
        # 1. Processamento de Voz -> GIF do Avatar
        vol = self.audio.get_volume()
        path = self.anim_logic.get_current_path(vol)
        if path:
            self.render.set_animation(path)
            
        # 2. Atualização dos Acessórios
        self.render.accessories.update(self.render.main_label) 
        
        # 3. Feedback Visual no Painel
        if self.panel.isVisible():
            self.panel.update_ui_feedback()
            
        # 4. Checagem periódica de configurações do sistema (a cada ~60 frames)
        self.frame_count += 1
        if self.frame_count >= 60:
            self.apply_fps_limit()
            self.frame_count = 0

    def quit_app(self):
        """Encerra o programa garantindo que tudo seja salvo e parado."""
        self.timer.stop()
        self.hotkeys.stop_all()
        self.audio.stop()
        self.config.save()
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Mantém a aplicação rodando mesmo que o painel de controle seja fechado pelo "X"
    app.setQuitOnLastWindowClosed(False) 
    
    try:
        engine = PixelTuberApp()
        sys.exit(app.exec())
    except Exception as e:
        print(f"❌ Erro Crítico: {e}")
        import traceback
        traceback.print_exc()