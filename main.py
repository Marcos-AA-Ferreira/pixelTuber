import sys
import ctypes
import os
import random 
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
            device_index=audio_cfg.get("device_index"),
            gain=audio_cfg.get("gain", 1.0)
        )
        # REMOVA O self.anim_logic DAQUI!

        # 3. Inicializar Janelas
        self.bg_window = BackgroundWindow()
        self.render = RenderWindow(self.config)
        self.overlay = FullScreenOverlay()

        # ---> ADICIONE AQUI! <---
        # Agora o self.render já existe e pode ser passado para o manager
        self.anim_logic = AnimationManager(self.config, self.render)
        
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
            self.anim_logic,
            self.hotkeys,
            overlay=self.overlay,
            bg_window=self.bg_window
        )
        
        # 6. Bandeja do Sistema
        self.setup_tray()
        self.current_duck_multiplier = 1.0
        
        # 7. Aplicação do Estado Inicial
        self.audio.start()
        bg_path = self.config.data.get("bg_path")
        if validate_path(bg_path):
            self.bg_window.set_background(bg_path)
            
        # --- MUDANÇA 2: FORÇAR O AVATAR A APARECER LOGO DE CARA ---
        main_set = self.config.data.get("animations", {}).get("main_set", "default")
        self.anim_logic.set_active_set(main_set)

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
        vol = self.audio.get_volume()
        
        # --- MUDANÇA 1: CÓDIGO DESCOMENTADO ---
        path = self.anim_logic.get_current_path(vol)
        if path:
            # Passamos também o estado (fala, mudo) para a UI acender a cor verde certa
            self.render.set_animation(path, getattr(self.anim_logic, "last_state", None))
        
        # 1. Lógica do Auto-Ducking
        bg_muted = self.config.data.get("bg_music_muted", False)
        base_vol = self.config.data.get("bg_music_vol", 50)
        ducking_enabled = self.config.data.get("audio", {}).get("auto_ducking", True)
        
        if hasattr(self.bg_window, 'audio') and not bg_muted:
            if ducking_enabled:
                target_duck = 0.3 if vol > self.audio.noise_threshold else 1.0
                self.current_duck_multiplier += (target_duck - self.current_duck_multiplier) * 0.1
                final_vol = base_vol * self.current_duck_multiplier
                self.bg_window.audio.audio_output.setVolume(final_vol / 100.0)
            else:
                self.bg_window.audio.audio_output.setVolume(base_vol / 100.0)
            
        # 2. Lógica Segura da Barra de Som (Visualizador)
        if hasattr(self.render, 'visualizer'):
            vis_config = self.config.data.get("visualizer", {})
            is_vis_enabled = vis_config.get("enabled", False)
            
            if is_vis_enabled:
                self.render.visualizer.show()
                self.render.visualizer.style = vis_config.get("style", "Clássico")
                
                # Usa as bandas reais do microfone
                if hasattr(self.audio, 'eq_bands') and self.audio.eq_bands:
                    self.render.visualizer.bands = self.audio.eq_bands
                else:
                    self.render.visualizer.bands = [0.0] * 8
                        
                self.render.visualizer.update()
            else:
                self.render.visualizer.hide()

        # 3. Atualização dos Acessórios
        self.render.accessories.update(self.render.main_label) 
        
        if self.panel.isVisible():
            self.panel.update_ui_feedback()
            
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