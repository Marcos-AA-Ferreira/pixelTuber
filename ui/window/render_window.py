import os
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QMovie, QIcon, QPainter, QColor, QPainterPath
from PySide6.QtCore import Qt, QPoint, Signal, QPointF

from ui.styles.theme import Theme
from ui.window.components.rw_rotatable_label import RotatableLabel
from core.accessory_manager import AccessoryManager

# === WIDGET: BARRA DE SOM COM NOVOS ESTILOS ===
class VisualizerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bands = [0.0] * 8
        self.style = "Clássico" 
        self.bar_color = QColor(0, 255, 150, 220) 
        self.setFixedSize(300, 100)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        num_bars = len(self.bands)
        
        if self.style == "Onda Contínua":
            # Estilo fluido de onda conectando os pontos
            path = QPainterPath()
            step = w / max(1, num_bars - 1)
            points = [QPointF(i * step, h - (self.bands[i] * h)) for i in range(num_bars)]
            
            path.moveTo(0, h)
            path.lineTo(points[0])
            for i in range(len(points) - 1):
                p1, p2 = points[i], points[i+1]
                ctrl1 = QPointF((p1.x() + p2.x()) / 2, p1.y())
                ctrl2 = QPointF((p1.x() + p2.x()) / 2, p2.y())
                path.cubicTo(ctrl1, ctrl2, p2)
            
            path.lineTo(w, h)
            path.lineTo(0, h)
            painter.setBrush(self.bar_color)
            painter.setPen(Qt.NoPen)
            painter.drawPath(path)
            
        elif self.style == "Pontos de Energia":
            # Estilo com bolinhas que saltam
            painter.setBrush(self.bar_color)
            painter.setPen(Qt.NoPen)
            spacing = 15
            bar_w = (w - (spacing * (num_bars - 1))) / num_bars
            for i, val in enumerate(self.bands):
                bar_h = val * h
                x = i * (bar_w + spacing)
                radius = min(bar_w / 2, 8)
                center_y = h - bar_h - radius
                painter.drawEllipse(QPointF(x + radius, center_y), radius, radius)
                # Rastro suave abaixo
                painter.setOpacity(0.3)
                painter.drawEllipse(QPointF(x + radius, center_y + (radius * 1.5)), radius * 0.7, radius * 0.7)
                painter.setOpacity(1.0)
                
        else:
            # Clássico e Neon Simétrico
            spacing = 6
            bar_w = (w - (spacing * (num_bars - 1))) / num_bars
            for i, val in enumerate(self.bands):
                bar_h = val * h
                x = i * (bar_w + spacing)
                
                if self.style == "Neon Simétrico":
                    painter.fillRect(int(x), int((h / 2) - (bar_h / 2)), int(bar_w), int(bar_h), self.bar_color)
                else: # Clássico
                    painter.fillRect(int(x), int(h - bar_h), int(bar_w), int(bar_h), self.bar_color)


class RenderWindow(QWidget):
    effectPositionChanged = Signal(int, int)

    def __init__(self, config_manager):
        super().__init__(None) 
        self.cfg = config_manager
        self.movie_cache = {}
        self.current_state = None 
        
        self.setWindowTitle("PixelTuber - Avatar")
        self.setWindowIcon(QIcon("assets/AVATAR_ICON.ico"))
        
        self.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.canvas_size = 2048 
        self.setFixedSize(self.canvas_size, self.canvas_size)
        
        self.main_label = RotatableLabel(self)
        self.main_label.setAlignment(Qt.AlignCenter)
        
        self.accessories = AccessoryManager(self, config_manager)
        
        self._drag_target = None  
        self._drag_offset = QPoint()

        r = self.cfg.data.get("render", {})
        self.move(r.get("x", 100), r.get("y", 100))
        
        self.apply_chroma_key()
        self.update_geometry()

        self.visualizer = VisualizerWidget(self)
        self.visualizer.move((self.width() - self.visualizer.width()) // 2, (self.height() // 2) + 200)
        self.visualizer.hide() 

    def apply_chroma_key(self):
        color = self.cfg.data.get("render", {}).get("chroma_key", "transparent")
        if color == "transparent":
            self.setStyleSheet("background: transparent;")
        elif color == "green":
            self.setStyleSheet("background-color: #00FF00;")
        elif color == "magenta":
            self.setStyleSheet("background-color: #FF00FF;")

    def update_geometry(self):
        scale = self.cfg.data["render"].get("scale", 1.0)
        avatar_size = int(Theme.BASE_AVATAR_SIZE * scale)
        
        offset = (self.canvas_size - avatar_size) // 2
        self.main_label.setGeometry(offset, offset, avatar_size, avatar_size)
        self.accessories.update(self.main_label)
        
        self.cfg.data["render"]["x"] = self.x()
        self.cfg.data["render"]["y"] = self.y()

    def set_animation(self, path, state=None):
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
        if self._drag_target: self.cfg.save()
        self._drag_target = None