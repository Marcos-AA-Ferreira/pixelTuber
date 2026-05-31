from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPainter
from PySide6.QtCore import Qt, QRectF

class RotatableLabel(QLabel):
    """
    Componente especializado em renderizar sprites e GIFs com transformações 
    de alta qualidade (escala, rotação e espelhamento) via hardware.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rotation = 0
        self.flip_h = False
        
        # Garante que o fundo seja totalmente transparente
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
        """
        Sobrescreve a renderização padrão do Qt para aplicar filtros de 
        suavização e transformações matemáticas precisas.
        """
        # Verifica se há conteúdo para desenhar
        if not self.movie() or self.movie().currentPixmap().isNull():
            return
        
        pixmap = self.movie().currentPixmap()
        painter = QPainter(self)
        
        # --- FILTROS DE QUALIDADE ---
        # SmoothPixmapTransform: Essencial para evitar que a imagem fique pixelada ao aumentar a escala.
        # Antialiasing: Suaviza as bordas do sprite, especialmente durante a rotação.
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # --- SISTEMA DE COORDENADAS ---
        # Movemos o ponto de origem (0,0) para o centro do widget.
        # Isso garante que a rotação e a escala ocorram em torno do centro do acessório.
        center_x = self.width() / 2
        center_y = self.height() / 2
        painter.translate(center_x, center_y)
        
        # Aplica a rotação (em graus)
        painter.rotate(self.rotation)
        
        # Aplica o espelhamento horizontal se necessário
        if self.flip_h:
            painter.scale(-1, 1) 
        
        # --- DESENHO DO SPRITE ---
        # Como transladamos a origem para o centro, desenharemos o retângulo
        # começando em (-metade, -metade) para que o centro da imagem coincida com o centro do widget.
        draw_w = self.width()
        draw_h = self.height()
        
        # Usamos QRectF (float) para cálculos de precisão, evitando "pulos" de 1 pixel (jittering).
        target_rect = QRectF(-draw_w / 2, -draw_h / 2, draw_w, draw_h)
        
        # Renderiza o frame atual do pixmap dentro do retângulo de destino, 
        # aplicando automaticamente a escala definida pelo tamanho do widget.
        painter.drawPixmap(target_rect, pixmap, QRectF(pixmap.rect()))
        
        painter.end()