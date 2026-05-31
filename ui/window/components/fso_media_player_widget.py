from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QMovie, QPixmap
from PySide6.QtCore import Qt, QUrl, QSize
from core.utils import get_extension # Usando nossa utilidade

class MediaPlayerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Labels para Imagem e GIF
        self.display_label = QLabel()
        self.display_label.setAlignment(Qt.AlignCenter)
        
        # Widget para Vídeo
        self.video_widget = QVideoWidget()
        
        # Player de Vídeo
        self.video_player = QMediaPlayer(self)
        self.video_player.setVideoOutput(self.video_widget)

        self.layout.addWidget(self.display_label)
        self.layout.addWidget(self.video_widget)
        self._active_movie = None
        self.hide_all()

    def hide_all(self):
        self.display_label.hide()
        self.video_widget.hide()
        self.video_player.stop()
        if self._active_movie:
            self._active_movie.stop()
            self._active_movie = None

    def play(self, path, size: QSize):
        self.hide_all()
        ext = get_extension(path)

        if ext in ['mp4', 'mov', 'avi']:
            self.video_widget.show()
            self.video_player.setSource(QUrl.fromLocalFile(path))
            self.video_player.play()
        
        elif ext == 'gif':
            self.display_label.show()
            self._active_movie = QMovie(path)
            self._active_movie.setScaledSize(size)
            self.display_label.setMovie(self._active_movie)
            self._active_movie.start()
        
        else: # Imagens estáticas
            pix = QPixmap(path)
            if not pix.isNull():
                self.display_label.show()
                self.display_label.setPixmap(pix.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation))