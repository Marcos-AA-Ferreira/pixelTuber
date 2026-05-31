import os
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsBlurEffect
from PySide6.QtGui import QPixmap, QMovie
from PySide6.QtCore import Qt, QSize
from core.utils import validate_path, get_extension

class BgContentWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.bg_label = QLabel()
        self.bg_label.setScaledContents(True)
        # Garante que o label tente ocupar o máximo de espaço
        self.bg_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.bg_label)
        
        # Efeito de Desfoque
        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurHints(QGraphicsBlurEffect.PerformanceHint)
        self.bg_label.setGraphicsEffect(self.blur_effect)
        
        self._current_movie = None

    def update_visual(self, path, width, height, blur_radius):
        """Atualiza a imagem/GIF e o nível de desfoque."""
        self.blur_effect.setBlurRadius(blur_radius)
        
        if not validate_path(path):
            self.bg_label.clear()
            if self._current_movie: 
                self._current_movie.stop()
                self._current_movie = None
            return

        ext = get_extension(path).lower()
        if ext == 'gif':
            # Se for um GIF novo ou diferente do atual
            if not self._current_movie or self._current_movie.fileName() != path:
                if self._current_movie: self._current_movie.stop()
                self._current_movie = QMovie(path)
                self.bg_label.setMovie(self._current_movie)
                self._current_movie.start()
            
            self._current_movie.setScaledSize(QSize(width, height))
        else:
            # Se era um GIF antes, para ele
            if self._current_movie: 
                self._current_movie.stop()
                self._current_movie = None
            
            pix = QPixmap(path)
            if not pix.isNull():
                self.bg_label.setPixmap(pix.scaled(
                    width, height, 
                    Qt.IgnoreAspectRatio, 
                    Qt.SmoothTransformation
                ))