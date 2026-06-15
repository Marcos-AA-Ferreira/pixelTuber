import os
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QMovie, QIcon
from PySide6.QtCore import Qt, QPoint, Signal

from ui.styles.theme import Theme
from ui.window.components.rw_rotatable_label import RotatableLabel
from core.accessory_manager import AccessoryManager

class RenderWindow(QWidget):
    """
    Janela de renderização principal (Overlay).
    Responsável por exibir o avatar, gerenciar acessórios e lidar com
    a interação do usuário (arrastar e posicionar).
    """
    effectPositionChanged = Signal(int, int)

    def __init__(self, config_manager):
        super().__init__(None) 
        self.cfg = config_manager
        self.movie_cache = {}
        self.current_state = None 
        
        self.setWindowTitle("PixelTuber - Avatar")
        self.setWindowIcon(QIcon("assets/AVATAR_ICON.ico"))
        
        # Configurações de Janela: Sem Bordas e Sempre no Topo
        self.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.canvas_size = 2048 
        self.setFixedSize(self.canvas_size, self.canvas_size)
        
        # Label principal do Avatar
        self.main_label = RotatableLabel(self)
        self.main_label.setAlignment(Qt.AlignCenter)
        
        # Gerenciador de Acessórios (Camadas extras)
        self.accessories = AccessoryManager(self, config_manager)
        
        # Variáveis de controle de arrasto
        self._drag_target = None  
        self._drag_offset = QPoint()

        # Posicionamento inicial
        r = self.cfg.data.get("render", {})
        self.move(r.get("x", 100), r.get("y", 100))
        
        # Aplica a cor de fundo (Chroma Key ou Transparente)
        self.apply_chroma_key()
        self.update_geometry()

    def apply_chroma_key(self):
        """Define o fundo como transparente ou colorido para captura no OBS."""
        color = self.cfg.data.get("render", {}).get("chroma_key", "transparent")
        
        if color == "transparent":
            self.setStyleSheet("background: transparent;")
        elif color == "green":
            # Verde Chroma Key padrão
            self.setStyleSheet("background-color: #00FF00;")
        elif color == "magenta":
            # Magenta puro
            self.setStyleSheet("background-color: #FF00FF;")

    def update_geometry(self):
        """Atualiza o tamanho e a posição do avatar e acessórios com base na escala."""
        scale = self.cfg.data["render"].get("scale", 1.0)
        avatar_size = int(Theme.BASE_AVATAR_SIZE * scale)
        
        offset = (self.canvas_size - avatar_size) // 2
        self.main_label.setGeometry(offset, offset, avatar_size, avatar_size)
        
        self.accessories.update(self.main_label)
        
        self.cfg.data["render"]["x"] = self.x()
        self.cfg.data["render"]["y"] = self.y()

    def set_animation(self, path, state=None):
        """Define o GIF atual do avatar."""
        if state: self.current_state = state

        if not path or not os.path.exists(path):
            if self.main_label.movie(): self.main_label.movie().stop()
            self.main_label.setMovie(None)
            self.main_label.clear()
            return
        
        if path not in self.movie_cache:
            m = QMovie(path)
            m.setCacheMode(QMovie.CacheAll)
            self.movie_cache[path] = m
        
        target_movie = self.movie_cache[path]
        
        if self.main_label.movie() != target_movie:
            self.main_label.setMovie(target_movie)
            target_movie.start()
            self.raise_()

    # --- Lógica de Interação e Movimento ---

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton: return
        pos = event.position().toPoint()
        
        for l_id, lbl in reversed(list(self.accessories.widgets.items())):
            if lbl.isVisible() and lbl.geometry().contains(pos):
                layer_cfg = self.cfg.data.get("aux_layers", {}).get(l_id, {})
                if not layer_cfg.get("locked", False): 
                    self._drag_target = l_id
                    self._drag_offset = pos - lbl.pos()
                    return
        
        if self.main_label.geometry().contains(pos):
            if not self.cfg.data["render"].get("locked", False):
                self._drag_target = "window"
                self._drag_offset = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if not self._drag_target: return
        
        if self._drag_target == "window":
            new_pos = event.globalPosition().toPoint() - self._drag_offset
            self.move(new_pos)
            self.cfg.data["render"]["x"] = new_pos.x()
            self.cfg.data["render"]["y"] = new_pos.y()
        else:
            l_id = self._drag_target
            new_pos = event.position().toPoint() - self._drag_offset
            self.accessories.widgets[l_id].move(new_pos)
            
            if l_id in self.cfg.data["aux_layers"]:
                c = self.cfg.data["aux_layers"][l_id]
                lbl_widget = self.accessories.widgets[l_id]
                center_x = new_pos.x() + (lbl_widget.width() // 2)
                center_y = new_pos.y() + (lbl_widget.height() // 2)
                
                c["x"] = center_x
                c["y"] = center_y
                
                avatar_center_x = self.main_label.x() + (self.main_label.width() // 2)
                avatar_center_y = self.main_label.y() + (self.main_label.height() // 2)
                
                c["rel_x"] = center_x - avatar_center_x
                c["rel_y"] = center_y - avatar_center_y

    def mouseReleaseEvent(self, event):
        if self._drag_target:
            self.cfg.save()
        self._drag_target = None