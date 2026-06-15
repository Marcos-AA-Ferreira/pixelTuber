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
    myappid = 'pixeltuber.standalone.v2'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    os.environ["QT_LOGGING_RULES"] = "qt.multimedia.ffmpeg=false;qt.multimedia.playbackengine.codec=false"
except:
    pass

class PixelTuberApp:
    def __init__(self):
        # 1. Carregar Configurações
        self.config = ConfigManager()
        
        # 2. Inicializar Motores de Áudio e Animação
        audio_cfg = self.config.data.get("audio", {})
        self.audio = AudioManager(
            device_index=audio_cfg.get("device"),
            gain=audio_cfg.get("gain", 1.0)
        )
        self.anim_logic = AnimationManager(self.config)
        
        # 3. Inicializar Janelas
        self.bg_window = BackgroundWindow()
        self.render = RenderWindow(self.config)
        self.overlay = FullScreenOverlay()
        
        # 4. Inicializar Gerenciadores de Lógica
        self.effects = EffectManager(self.overlay)
        self.hotkeys = HotkeyManager(self.config, self.render, self.overlay)
        self.hotkeys.setup_defaults()
        
        # 5. Interface de Controle
        self.panel = ControlPanel(
            self.config, 
            self.audio, 
            self.render, 
            self.effects, 
            self.hotkeys,
            overlay=self.overlay,
            bg_window=self.bg_window
        )
        
        # 6. Bandeja do Sistema
        self.setup_tray()
        
        # Variável para o Auto-Ducking da música de fundo
        self.current_duck_multiplier = 1.0
        
        # 7. Aplicação do Estado Inicial
        self.audio.start()
        bg_path = self.config.data.get("bg_path")
        if validate_path(bg_path):
            self.bg_window.set_background(bg_path)

        # 8. Exibição das Janelas
        self.bg_window.show()
        self.render.show()
        self.overlay.show()
        self.panel.show()
        self.panel.raise_()

        # 9. Loop Principal
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.apply_fps_limit()
        self.frame_count = 0

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(QIcon("assets/PAINEL-DE-CONTROLE_ICON.ico"), QApplication.instance())
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
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_panel()

    def show_panel(self):
        self.panel.showNormal()
        self.panel.raise_()
        self.panel.activateWindow()

    def apply_fps_limit(self):
        fps_setting = self.config.data.get("system", {}).get("fps_limit", "60 FPS")
        fps_map = {"30 FPS": 33, "60 FPS": 16, "120 FPS": 8}
        interval = fps_map.get(fps_setting, 16)
        if not self.timer.isActive() or self.timer.interval() != interval:
            self.timer.start(interval)

    def update_loop(self):
        """Atualiza a lógica visual e gerencia interações de áudio a cada frame."""
        # 1. Processamento de Voz -> GIF do Avatar
        vol = self.audio.get_volume()
        path = self.anim_logic.get_current_path(vol)
        if path:
            self.render.set_animation(path)
            
        # 2. Lógica de Auto-Ducking (Abaixar a música de fundo quando fala)
        # Pega as configurações base independentemente de estar tocando ou não
        bg_muted = self.config.data.get("bg_music_muted", False)
        base_vol = self.config.data.get("bg_music_vol", 50)
        
        if not bg_muted and hasattr(self.bg_window, 'audio'):
            # Se a voz passar do gate (0.02 ou customizado), reduz para 30% do volume original
            target_duck = 0.3 if vol > self.audio.noise_threshold else 1.0
            
            # Interpolação matemática para não dar um corte seco no som (easing de 10% por frame)
            self.current_duck_multiplier += (target_duck - self.current_duck_multiplier) * 0.1
            
            # Aplica o volume final recalculado no player
            final_vol = base_vol * self.current_duck_multiplier
            self.bg_window.audio.audio_output.setVolume(final_vol / 100.0)
            
        # 3. Atualização dos Acessórios
        self.render.accessories.update(self.render.main_label) 
        
        # 4. Feedback Visual no Painel
        if self.panel.isVisible():
            self.panel.update_ui_feedback()
            
        # 5. Checagem periódica de configurações de sistema
        self.frame_count += 1
        if self.frame_count >= 60:
            self.apply_fps_limit()
            self.frame_count = 0

    def quit_app(self):
        self.timer.stop()
        self.hotkeys.stop_all()
        self.audio.stop()
        self.config.save()
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) 
    
    try:
        engine = PixelTuberApp()
        sys.exit(app.exec())
    except Exception as e:
        print(f"❌ Erro Crítico: {e}")
        import traceback
        traceback.print_exc()