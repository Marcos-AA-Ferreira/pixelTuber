import os
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QMovie, QPixmap
from PySide6.QtWidgets import QGraphicsOpacityEffect

from ui.styles.theme import Theme
from core.utils import validate_path
from ui.window.components.rw_rotatable_label import RotatableLabel

class AccessoryManager:
    def __init__(self, parent_window, config_manager):
        self.parent = parent_window
        self.cfg = config_manager
        self.widgets = {}

    def update(self, main_label):
        layers = self.cfg.data.get("aux_layers", {})
        active_ids = set(layers.keys())
        current_ids = set(self.widgets.keys())
        
        # 1. Limpeza de camadas excluídas
        for to_remove in (current_ids - active_ids):
            if to_remove in self.widgets:
                self.widgets[to_remove].setMovie(None)
                self.widgets[to_remove].deleteLater()
                del self.widgets[to_remove]

        # 2. Ordenação rigorosa por Z-Index
        sorted_layers = sorted(layers.items(), key=lambda item: item[1].get("z_index", 1))

        for l_id, config in sorted_layers:
            if not config.get("visible", True):
                if l_id in self.widgets:
                    self.widgets[l_id].hide()
                continue

            if l_id not in self.widgets:
                self.widgets[l_id] = RotatableLabel(self.parent)
            
            lbl = self.widgets[l_id]
            lbl.show()
            
            # Dimensionamento do bounding-box
            scale_factor = config.get("scale", 1.0)
            base_size = int(Theme.BASE_AVATAR_SIZE * scale_factor)
            margin_size = int(base_size * 1.5) 
            
            if lbl.width() != margin_size:
                lbl.setFixedSize(margin_size, margin_size)
            
            if hasattr(lbl, 'set_rotation'):
                lbl.set_rotation(config.get("rotation", 0))

            # Opacidade Nativa do PySide6
            opacity = config.get("opacity", 1.0)
            opacity_effect = QGraphicsOpacityEffect(lbl)
            opacity_effect.setOpacity(opacity)
            lbl.setGraphicsEffect(opacity_effect)

            # Cálculo de Posicionamento Centrado
            if config.get("locked", False):
                target_x = main_label.x() + (main_label.width() // 2) + config.get("rel_x", 0)
                target_y = main_label.y() + (main_label.height() // 2) + config.get("rel_y", 0)
            else:
                target_x = config.get("x", 100)
                target_y = config.get("y", 100)

            lbl.move(target_x - (margin_size // 2), target_y - (margin_size // 2))
            
            # Carregamento Dinâmico (GIF ou Estático)
            path = config.get("path")
            if validate_path(path):
                if path.lower().endswith('.gif'):
                    if not lbl.movie() or lbl.movie().fileName() != path:
                        movie = QMovie(path)
                        movie.setScaledSize(QSize(base_size, base_size))
                        lbl.setMovie(movie)
                        movie.start()
                else:
                    pix = QPixmap(path).scaled(base_size, base_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    lbl.setPixmap(pix)

            # Empurra o acessório para a camada certa
            lbl.raise_()