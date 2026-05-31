from PySide6.QtWidgets import QWidget, QScrollArea
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QFont

class AudioTrimmer(QWidget):
    valuesChanged = Signal(float, float)

    def __init__(self):
        super().__init__()
        self.setFixedHeight(75) 
        self.setMinimumWidth(400)
        self.duration = 0.0
        self.start_pct = 0.0
        self.end_pct = 1.0
        self.active_handle = None
        self._scroll_area = None # Referência ao pai que rola
        
        # Paleta de Cores
        self.color_bg = QColor("#333333")      
        self.color_active = QColor("#58a6ff")  
        self.color_handle = QColor("#ffffff")  
        self.color_ticks_main = QColor("#666666") 
        self.color_ticks_sub = QColor("#444444")  
        self.color_text = QColor("#888888")    

    def set_duration(self, duration_seconds):
        self.duration = duration_seconds
        # Resetamos para o total ao carregar novo áudio, 
        # a menos que o load_data chame o set_values logo em seguida
        self.start_pct = 0.0
        self.end_pct = 1.0
        self.update()

    # --- NOVO MÉTODO: Essencial para carregar edições ---
    def set_values(self, start, end):
        """Ajusta as posições dos handles baseado em tempo (segundos)."""
        if self.duration > 0:
            self.start_pct = max(0.0, min(start / self.duration, 1.0))
            self.end_pct = max(0.0, min(end / self.duration, 1.0))
            self.update()

    def format_time(self, seconds):
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m:02d}:{s:02d}"

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        bar_h = 6                 
        bar_y = 25                
        padding = 20              
        draw_w = w - (padding * 2)
        
        if self.duration > 0:
            painter.setFont(QFont("Segoe UI", 7))
            
            if self.duration <= 30: 
                main_step, sub_step = 5.0, 1.0
            elif self.duration <= 120: 
                main_step, sub_step = 10.0, 2.0
            else: 
                main_step, sub_step = 60.0, 10.0

            num_sub = int(self.duration / sub_step) + 1
            for i in range(num_sub):
                tx = padding + ((i * sub_step) / self.duration) * draw_w
                painter.setPen(QPen(self.color_ticks_sub, 1))
                painter.drawLine(int(tx), bar_y + 10, int(tx), bar_y + 14)

            num_main = int(self.duration / main_step) + 1
            for i in range(num_main):
                time_val = i * main_step
                tx = padding + (time_val / self.duration) * draw_w
                painter.setPen(QPen(self.color_ticks_main, 1.5))
                painter.drawLine(int(tx), bar_y + 10, int(tx), bar_y + 18)
                painter.setPen(self.color_text)
                painter.drawText(int(tx) - 12, bar_y + 32, self.format_time(time_val))

        painter.setPen(Qt.NoPen)
        painter.setBrush(self.color_bg)
        painter.drawRoundedRect(padding, bar_y, draw_w, bar_h, 3, 3)

        if self.duration > 0:
            sx = padding + (self.start_pct * draw_w)
            ex = padding + (self.end_pct * draw_w)
            painter.setBrush(self.color_active)
            painter.drawRect(QRectF(sx, bar_y, ex - sx, bar_h))

            handle_r = 7
            painter.setBrush(self.color_handle)
            painter.setPen(QPen(QColor(0,0,0,50), 1))
            painter.drawEllipse(QPointF(sx, bar_y + (bar_h/2)), handle_r, handle_r)
            painter.drawEllipse(QPointF(ex, bar_y + (bar_h/2)), handle_r, handle_r)

            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            painter.setPen(self.color_active)
            t_start = self.format_time(self.start_pct * self.duration)
            t_end = self.format_time(self.end_pct * self.duration)
            painter.drawText(int(sx) - 15, bar_y - 10, t_start)
            painter.drawText(int(ex) - 15, bar_y - 10, t_end)

    def mousePressEvent(self, event):
        if self.duration <= 0: return
        x = event.position().x()
        padding = 20
        draw_w = self.width() - (padding * 2)
        s_pos = padding + (self.start_pct * draw_w)
        e_pos = padding + (self.end_pct * draw_w)
        
        if abs(x - s_pos) < 20: 
            self.active_handle = 'start'
        elif abs(x - e_pos) < 20: 
            self.active_handle = 'end'

        # TRAVA DE SCROLL: Se pegou um handle, bloqueia o scroll do pai
        if self.active_handle:
            self._toggle_parent_scroll(False)

    def mouseMoveEvent(self, event):
        if not self.active_handle or self.duration <= 0: return
        padding = 20
        draw_w = self.width() - (padding * 2)
        x_rel = max(0, min(event.position().x() - padding, draw_w))
        new_pct = x_rel / draw_w
        
        if self.active_handle == 'start':
            self.start_pct = min(new_pct, self.end_pct - 0.02)
        else:
            self.end_pct = max(new_pct, self.start_pct + 0.02)
            
        self.update()
        self.valuesChanged.emit(self.start_pct * self.duration, self.end_pct * self.duration)

    def mouseReleaseEvent(self, event):
        self.active_handle = None
        self._toggle_parent_scroll(True) # Destrava o scroll ao soltar

    def _toggle_parent_scroll(self, enabled):
        """Busca o ScrollArea pai e ativa/desativa a rolagem."""
        if not self._scroll_area:
            p = self.parent()
            while p:
                if isinstance(p, QScrollArea):
                    self._scroll_area = p
                    break
                p = p.parent()
        
        if self._scroll_area:
            self._scroll_area.verticalScrollBar().setEnabled(enabled)