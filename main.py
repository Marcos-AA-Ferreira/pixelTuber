import sys
import ctypes
import os
from PySide6.QtWidgets import QApplication
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
        # Corrigido para device_index conforme o seu AudioManager original
        self.audio = AudioManager(
            device_index=audio_cfg.get("device"),
            gain=audio_cfg.get("gain", 1.0)
        )
        self.anim_logic = AnimationManager(self.config)
        
        # 3. Inicializar Janelas de Interface
        self.bg_window = BackgroundWindow()
        self.render = RenderWindow(self.config) # O AccessoryManager já é criado aqui dentro
        self.overlay = FullScreenOverlay()
        
        # 4. Inicializar Gerenciadores de Lógica Adicional
        # Note: Removemos o self.accessories daqui para não criar labels duplicadas.
        
        # EffectManager: Conecta as hotkeys à FullScreenOverlay
        self.effects = EffectManager(self.overlay)
        
        # HotkeyManager: Escuta o teclado globalmente
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
        
        # 6. Aplicação do Estado Inicial
        self.audio.start()
        
        # Carrega o fundo inicial se houver um salvo
        bg_path = self.config.data.get("bg_path")
        if validate_path(bg_path):
            self.bg_window.set_background(bg_path)

        # 7. Exibição das Janelas
        self.bg_window.show()
        self.render.show()
        self.overlay.show()
        self.panel.show()
        
        # Traz o painel para o foco inicial
        self.panel.raise_()

        # 8. Loop Principal de Sincronização (Aprox. 60 FPS)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(16)

    def update_loop(self):
        """Atualiza a lógica visual a cada frame."""
        
        # 1. Processamento de Voz -> GIF do Avatar
        vol = self.audio.get_volume()
        path = self.anim_logic.get_current_path(vol)
        if path:
            self.render.set_animation(path)
            
        # 2. Atualização dos Acessórios
        # Corrigido para usar a instância de acessórios que vive dentro da RenderWindow
        self.render.accessories.update(self.render.main_label) 
        
        # 3. Feedback Visual no Painel
        if self.panel.isVisible():
            self.panel.update_ui_feedback()

    def quit_app(self):
        """Encerra o programa garantindo que tudo seja salvo e parado."""
        self.timer.stop()
        self.hotkeys.stop_all()
        self.audio.stop()
        self.config.save()
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