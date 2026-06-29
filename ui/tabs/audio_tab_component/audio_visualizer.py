from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPainterPath
from PySide6.QtCore import Qt

class AudioVisualizerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bands = [0.0] * 8
        self.style = "Clássico"
        self.bar_color = QColor(0, 255, 150, 220) 
        self.setFixedHeight(50) 

    def update_bands(self, bands):
        self.bands = bands
        self.update()

    def set_visualizer_style(self, style):
        self.style = style
        self.update()

    def paintEvent(self, event):
        painter = QPainter()
        if not painter.begin(self):
            return
            
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            w, h = self.width(), self.height()
            num_bars = len(self.bands)
            
            if num_bars == 0:
                return

            # Roteamento dinâmico de estilos (Fácil de expandir futuramente!)
            if self.style == "Onda Contínua":
                self._draw_continuous_wave(painter, w, h, num_bars)
            elif self.style == "Barras Digitais":
                self._draw_digital_bars(painter, w, h, num_bars)
            else:
                self._draw_classic_bars(painter, w, h, num_bars)
        finally:
            painter.end()

    def _draw_continuous_wave(self, painter, w, h, num_bars):
        path = QPainterPath()
        step = w / max(1, num_bars - 1)
        path.moveTo(0, h)
        for i, val in enumerate(self.bands):
            x = i * step
            y = h - (val * h)
            path.lineTo(x, y)
        path.lineTo(w, h)
        path.closeSubpath()
        painter.fillPath(path, self.bar_color)

    def _draw_classic_bars(self, painter, w, h, num_bars):
        gap = 4
        bar_w = (w - (gap * (num_bars - 1))) / num_bars
        for i, val in enumerate(self.bands):
            bar_h = val * h
            x = i * (bar_w + gap)
            y = h - bar_h
            painter.fillRect(int(x), int(y), int(bar_w), int(bar_h), self.bar_color)

    def _draw_digital_bars(self, painter, w, h, num_bars):
        # Um estilo extra de brinde para testar a futura expansão!
        gap = 5
        bar_w = (w - (gap * (num_bars - 1))) / num_bars
        segments = 5
        seg_gap = 2
        seg_h = (h - (seg_gap * (segments - 1))) / segments

        for i, val in enumerate(self.bands):
            x = i * (bar_w + gap)
            active_segs = int(val * segments)
            for s in range(segments):
                y = h - ((s + 1) * (seg_h + seg_gap))
                color = self.bar_color if s < active_segs else QColor(50, 50, 50, 80)
                painter.fillRect(int(x), int(y), int(bar_w), int(seg_h), color)