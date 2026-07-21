import sys
import ctypes
import os
import random 
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QTimer, Qt

# --- Importação dos Gerenciadores do Core ---
from core.config_manager import ConfigManager
from core.audio_manager import AudioManager
from core.animation_manager import AnimationManager
from core.background_manager import BackgroundManager
from core.hotkey_manager import HotkeyManager
from core.effect_manager import EffectManager
from core.utils import validate_path
from core.event_bus import EventBus

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
        self.audio = AudioManager(self.config)
        
        # Conecta o evento do áudio diretamente ao atualizador da interface! 🚀
        self.audio.audioProcessed.connect(self.on_audio_processed, Qt.QueuedConnection)
        self.audio.start()

        # 3. Inicializar Janelas
        self.bg_window = BackgroundWindow()
        self.bg_manager = BackgroundManager(self.config, self.bg_window)
        self.render = RenderWindow(self.config)
        self.overlay = FullScreenOverlay()


        self.anim_logic = AnimationManager(self.config, self.render)
        
        # 4. Inicializar Gerenciadores de Lógica
        self.effects = EffectManager(self.overlay)
        self.hotkeys = HotkeyManager(self.config, self.render, self.overlay)
        self.hotkeys.setup_defaults()

        self.hotkeys.register_action("next_music", self.bg_manager.play_next)
        self.hotkeys.register_action("prev_music", self.bg_manager.play_prev)
        
        # 5. Interface de Controle
        self.panel = ControlPanel(self.config)

        # 6. Bandeja do Sistema
        self.setup_tray()
        self.current_duck_multiplier = 1.0
        
        # 7. Aplicação do Estado Inicial
        self.audio.start()
        
        # O Gerenciador assume o controle: ele lê o JSON, junta as peças e atualiza a janela!
        self.bg_manager._apply_background_to_window()

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

        # ==========================================
        # CONEXÕES DO EVENT BUS
        # ==========================================
        bus = EventBus.instance()
        
        # Conecta os sinais da UI aos métodos reais dos Managers
        bus.request_music_next.connect(self.bg_manager.play_next)
        bus.request_music_prev.connect(self.bg_manager.play_prev)
        bus.request_music_remove.connect(self.bg_manager.remove_music)
        bus.request_music_change.connect(self.bg_manager.set_music)
        # Se você tivesse um método genérico play/pause:
        # bus.request_music_play_pause.connect(self.bg_manager.toggle_play_pause)
        
        # Conexões para efeitos
        bus.request_play_effect.connect(self.effects.play_effect)

        # PONTE DO OVERLAY: Pega o sinal do overlay e repassa para o Event Bus global
        self.overlay.effectPositionChanged.connect(bus.effect_position_updated.emit)

        # UI -> Manager (Comandos)
        bus.request_bg_image_change.connect(self.bg_manager.set_background_image)
        bus.request_bg_image_remove.connect(self.bg_manager.remove_background_image)
        bus.request_bg_visual_update.connect(lambda d: self.bg_manager.update_visual_settings(d))
        bus.request_bg_audio_update.connect(lambda d: self.bg_manager.update_audio_settings(d.get("volume"), d.get("muted"), d.get("loop")))

        # Manager -> UI (Atualizações de Estado)
        self.bg_manager.visualChanged.connect(bus.bg_visual_changed.emit)
        self.bg_manager.musicChanged.connect(bus.bg_music_changed.emit)

        # --- NOVAS CONEXÕES DO ÁUDIO (A Ponte) ---
        # 1. Escuta comandos da UI e executa no AudioManager
        bus.request_audio_gain_change.connect(self.audio.set_gain)
        bus.request_audio_noise_gate_change.connect(self.audio.set_noise_gate)
        bus.request_audio_hold_time_change.connect(self.audio.set_hold_time)
        bus.request_audio_ducking_toggle.connect(self.audio.set_auto_ducking)
        bus.request_audio_threshold_change.connect(self.audio.set_threshold)
        bus.request_visualizer_style_change.connect(self.audio.set_visualizer_style)
        bus.request_audio_device_change.connect(self.audio.set_device_index)

        # Trata o pedido de recarregar microfones: pega a lista do Manager e devolve pro Bus
        bus.request_refresh_devices.connect(
            lambda: bus.audio_devices_updated.emit(self.audio.get_filtered_input_devices())
        )

        # 2. Envia atualizações de estado do AudioManager para a UI
        self.audio.volumeChanged.connect(bus.audio_volume_updated.emit)
        self.audio.audioProcessed.connect(lambda vol, bands: bus.audio_processed_updated.emit(vol, bands))
        
        # --- NOVAS CONEXÕES DO AVATAR/RENDER (A Ponte) ---
        bus.request_geometry_update.connect(self.render.update_geometry)
        bus.request_animation_set_change.connect(self.anim_logic.set_active_set)
        
        bus.request_avatar_visibility_toggle.connect(self.render.setVisible)
        bus.request_avatar_minimize_toggle.connect(
            lambda: self.render.showNormal() if self.render.isMinimized() else self.render.showMinimized()
        )
        bus.request_mic_mute_toggle.connect(self.audio.set_muted)
        bus.request_hotkeys_reload.connect(self.hotkeys.setup_defaults)

        # O Manager avisa a UI quando o estado do microfone muda:
        self.audio.muteToggled.connect(bus.audio_mute_updated.emit)

        # --- NOVAS CONEXÕES FINAIS (Settings, Effects, Background) ---
        
        # 1. Configurações da Janela de Renderização
        def toggle_on_top(state):
            flags = self.render.windowFlags()
            if state:
                self.render.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
            else:
                self.render.setWindowFlags(flags & ~Qt.WindowStaysOnTopHint)
            self.render.show()
            
        bus.request_render_on_top_toggle.connect(toggle_on_top)

        # --- NOVA CONEXÃO DO CHROMA KEY ---
        bus.request_chroma_key_update.connect(self.render.apply_chroma_key)
        
        # 2. Atalhos Dinâmicos dos Efeitos
        bus.request_register_effect_hotkey.connect(self.hotkeys.register_custom_effect)
        bus.request_remove_effect_hotkey.connect(self.hotkeys.remove_custom_hotkey)
        
        # 3. Status e Controle da Música de Fundo
        from PySide6.QtMultimedia import QMediaPlayer, QMediaMetaData
        
        if hasattr(self.bg_manager, 'bg_window') and hasattr(self.bg_manager.bg_window, 'audio'):
            player = self.bg_manager.bg_window.audio.player
            
            # Pedidos da UI para o Player
            bus.request_bg_player_set_position.connect(player.setPosition)
            bus.request_music_play_pause.connect(
                lambda: player.pause() if player.playbackState() == QMediaPlayer.PlayingState else player.play()
            )
            
            # Respostas do Player para a UI
            player.positionChanged.connect(bus.bg_player_position_updated.emit)
            player.durationChanged.connect(bus.bg_player_duration_updated.emit)
            player.playbackStateChanged.connect(
                lambda state: bus.bg_player_state_changed.emit(state == QMediaPlayer.PlayingState)
            )
            player.metaDataChanged.connect(
                lambda: bus.bg_player_metadata_updated.emit(
                    player.metaData().value(QMediaMetaData.Key.Title) or ""
                )
            )

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

    def on_audio_processed(self, volume, eq_bands):
        """Slot acionado assim que o microfone processa o áudio."""
        # 1. Atualiza a animação do Avatar com o volume atual
        if hasattr(self, 'anim_logic') and self.anim_logic:
            self.anim_logic.update(volume)
            
        # 2. Atualiza o Visualizador de Áudio na tela de renderização
        vis_config = self.config.data.get("visualizer", {})
        if vis_config.get("enabled", True) and hasattr(self.render, 'visualizer'):
            self.render.visualizer.bands = eq_bands
            self.render.visualizer.update()

        # 3. Lógica do Auto-Ducking reativa
        bg_muted = self.config.data.get("bg_music_muted", False)
        base_vol = self.config.data.get("bg_music_vol", 50)
        ducking_enabled = self.config.data.get("audio", {}).get("auto_ducking", True)
        
        if hasattr(self.bg_window, 'audio') and not bg_muted:
            if ducking_enabled:
                target_duck = 0.3 if volume > self.audio.noise_threshold else 1.0
                if not hasattr(self, 'current_duck_multiplier'):
                    self.current_duck_multiplier = 1.0
                self.current_duck_multiplier += (target_duck - self.current_duck_multiplier) * 0.1
                final_vol = base_vol * self.current_duck_multiplier
                self.bg_window.audio.audio_output.setVolume(final_vol / 100.0)
            else:
                self.bg_window.audio.audio_output.setVolume(base_vol / 100.0)

    def update_loop(self):
        """Atualiza a lógica visual e gerencia interações a cada frame."""
        # 1. Atualização dos Acessórios
        self.render.accessories.update(self.render.main_label) 
        
        # 2. Atualização de feedback visual do painel se estiver aberto
        if self.panel.isVisible():
            self.panel.update_ui_feedback()
            
        # 3. Controlo de FPS
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
    
    # --- CARREGAMENTO DO TEMA GLOBAL (QSS) ---
    qss_path = os.path.join(os.path.dirname(__file__), "ui", "styles", "main.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    else:
        print("Aviso: Arquivo main.qss não encontrado.")
    # -----------------------------------------

    try:
        engine = PixelTuberApp()
        sys.exit(app.exec())

    except Exception as e:
        print(f"❌ Erro Crítico: {e}")
        import traceback
        traceback.print_exc()