# core/background_manager.py
import os
import glob
from PySide6.QtCore import QObject, Signal

class BackgroundManager(QObject):
    # Sinais para notificar a View (UI) sobre mudanças de estado
    musicChanged = Signal(str)         # Caminho da música atual
    playlistChanged = Signal(list)     # Lista atualizada de músicas
    visualChanged = Signal(dict)       # Dicionário completo de configurações visuais

    def __init__(self, config_manager, bg_window):
        super().__init__()
        self.cfg = config_manager
        self.bg_window = bg_window
        
        self.playlist = []
        self.current_index = -1
        
        self._ensure_config_keys()
        self.load_initial_state()

    def _ensure_config_keys(self):
        """Garante que as chaves padrão existam usando a API blindada do ConfigManager."""
        defaults = {
            "bg_path": "", "bg_opacity": 100, "bg_blur": 0, "bg_layer_level": 0,
            "bg_music_path": "", "bg_music_vol": 50, "bg_music_muted": False, "bg_music_loop": True
        }
        for key, value in defaults.items():
            if self.cfg.get_bg_config(key) is None:
                self.cfg.set_bg_config(key, value)
        
        if self.cfg.get_system_config("toast_position") is None:
            self.cfg.set_system_config("toast_position", "Canto Inferior Direito")

    def load_initial_state(self):
        """Carrega o estado inicial do JSON."""
        current_music = self.cfg.data.get("bg_music_path", "")
        if current_music and os.path.exists(current_music):
            folder = os.path.dirname(current_music)
            self.load_playlist_from_folder(folder, select_path=current_music)

    def load_playlist_from_folder(self, folder_path, select_path=None):
        """Varre o diretório e monta a estrutura interna da playlist."""
        self.playlist = glob.glob(os.path.join(folder_path, "*.mp3")) + glob.glob(os.path.join(folder_path, "*.wav"))
        self.playlist.sort()
        
        if select_path in self.playlist:
            self.current_index = self.playlist.index(select_path)
        elif self.playlist:
            self.current_index = 0
            
        self.playlistChanged.emit(self.playlist)

    # --- LÓGICA VISUAL ---
    def update_visual_settings(self, settings: dict):
        """Atualiza as configurações visuais de background de forma segura."""
        for key, value in settings.items():
            self.cfg.set_bg_config(key, value)
            
        self._apply_background_to_window()

    def set_background_image(self, path):
        """Define uma nova imagem de fundo."""
        self.cfg.data["bg_path"] = path
        self.cfg.save()
        self._apply_background_to_window()

    def remove_background_image(self):
        """Remove a imagem de fundo atual."""
        self.cfg.data["bg_path"] = ""
        self.cfg.save()
        self._apply_background_to_window()

    def _apply_background_to_window(self):
        """Gera o payload de configuração e despacha para a janela ativa e para a UI."""
        bg_config = {
            "path": self.cfg.data.get("bg_path", ""),
            "width": self.bg_window.width() if self.bg_window else 800,
            "height": self.bg_window.height() if self.bg_window else 600,
            "opacity": self.cfg.data.get("bg_opacity", 100),
            "blur": self.cfg.data.get("bg_blur", 0),
            "audio_path": self.cfg.data.get("bg_music_path", ""),
            "volume": self.cfg.data.get("bg_music_vol", 50),
            "muted": self.cfg.data.get("bg_music_muted", False),
            "loop": self.cfg.data.get("bg_music_loop", True)
        }

        if self.bg_window:
            if hasattr(self.bg_window, 'set_layer_level'):
                self.bg_window.set_layer_level(self.cfg.data["bg_layer_level"])
            self.bg_window.update_background(bg_config)

        self.visualChanged.emit(bg_config)

    # --- LÓGICA DE ÁUDIO ---
    
    def update_audio_settings(self, volume, muted, loop):
        """Atualiza volumes e estados de reprodução."""
        self.cfg.data.update({
            "bg_music_vol": volume,
            "bg_music_muted": muted,
            "bg_music_loop": loop
        })
        self.cfg.save()
        self._apply_background_to_window()

    def set_music(self, path):
        if not path:
            self.remove_music()
            return

        if os.path.exists(path):
            folder = os.path.dirname(path)
            if not self.playlist or os.path.dirname(self.playlist[0]) != folder:
                self.load_playlist_from_folder(folder, select_path=path)
            else:
                if path in self.playlist:
                    self.current_index = self.playlist.index(path)

            self.cfg.set_bg_config("bg_music_path", path)
            self.musicChanged.emit(path)
            self._apply_background_to_window()

    def get_current_music_path(self):
        """Retorna o caminho da música atual guardado nas configurações."""
        return self.cfg.get_bg_config("bg_music_path", "")

    def play_next(self):
        if not self.playlist: return
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.set_music(self.playlist[self.current_index])

    def play_prev(self):
        if not self.playlist: return
        self.current_index = (self.current_index - 1) % len(self.playlist)
        self.set_music(self.playlist[self.current_index])

    def remove_music(self):
        self.cfg.data["bg_music_path"] = ""
        self.playlist = []
        self.current_index = -1
        self.cfg.save()
        self.playlistChanged.emit([])
        self.musicChanged.emit("")
        self._apply_background_to_window()