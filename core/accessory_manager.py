import os
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QMovie

from ui.styles.theme import Theme
from core.utils import calculate_scale, validate_path
from ui.window.components.rw_rotatable_label import RotatableLabel

class AccessoryManager:
    def __init__(self, parent_window, config_manager):
        self.parent = parent_window
        self.cfg = config_manager
        self.widgets = {}

    def update(self, main_label):
        """Atualiza todas as camadas de acessórios baseando-se no estado do config."""
        layers = self.cfg.data.get("aux_layers", {})
        active_ids = set(layers.keys())
        current_ids = set(self.widgets.keys())
        
        # 1. Limpeza
        for to_remove in (current_ids - active_ids):
            if to_remove in self.widgets:
                self.widgets[to_remove].setMovie(None)
                self.widgets[to_remove].deleteLater()
                del self.widgets[to_remove]

        # 2. Processamento
        for l_id, config in layers.items():
            if l_id not in self.widgets:
                self.widgets[l_id] = RotatableLabel(self.parent)
                self.widgets[l_id].show()
            
            lbl = self.widgets[l_id]
            is_vis = config.get("visible", True)
            lbl.setVisible(is_vis)
            if not is_vis: continue

            if config.get("z_index", 1) >= 0: lbl.raise_()
            else: lbl.lower()

            lbl.flip_h = config.get("flip_h", False)
            lbl.rotation = config.get("rotation", 0)
            
            # Cálculo de tamanho
            scale_factor = config.get("scale", 1.0)
            base_size = int(Theme.BASE_AVATAR_SIZE * scale_factor)
            margin_size = int(base_size * 1.5) 
            
            if lbl.width() != margin_size:
                lbl.setFixedSize(margin_size, margin_size)
            
            # --- CORREÇÃO DE ANCORAGEM (CENTRO) ---
            # Em vez de mover o canto superior esquerdo para rel_x, 
            # movemos o CENTRO do label para a posição desejada.
            if config.get("locked", False):
                # Posição baseada no centro do avatar + offset
                target_x = main_label.x() + (main_label.width() // 2) + config.get("rel_x", 0)
                target_y = main_label.y() + (main_label.height() // 2) + config.get("rel_y", 0)
            else:
                target_x = config.get("x", 100)
                target_y = config.get("y", 100)

            # Move o label compensando a margem para que o centro seja o ponto target
            lbl.move(target_x - (margin_size // 2), target_y - (margin_size // 2))
            
            # --- Carregamento de Media ---
            path = config.get("path")
            if validate_path(path):
                if not lbl.movie() or lbl.movie().fileName() != path:
                    m = QMovie(path)
                    m.setCacheMode(QMovie.CacheAll)
                    lbl.setMovie(m)
                    m.frameChanged.connect(lbl.update)
                    m.start()