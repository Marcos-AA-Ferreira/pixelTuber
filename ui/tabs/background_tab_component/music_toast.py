from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QFrame, QGraphicsOpacityEffect, QApplication)
from PySide6.QtCore import Qt, QPropertyAnimation, QTimer, QSize
from PySide6.QtGui import QIcon, QPixmap

class MusicToast(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(340, 90)
        
        # Flags para janela flutuante independente (sem barra, sempre no topo)
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground) # Permite cantos arredondados reais
        
        self.init_ui()
        
        # Animação de Opacidade (Fade In / Fade Out)
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(300)
        
        # Timer para fechar automaticamente após 4 segundos
        self.hide_timer = QTimer(self)
        self.hide_timer.setInterval(4000)
        self.hide_timer.timeout.connect(self.hide_toast)

    def init_ui(self):
        # Layout principal da janela
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Fundo arredondado (estilo Xiaomi/Dark Mode)
        self.frame = QFrame(self)
        self.frame.setStyleSheet("""
            QFrame { 
                background-color: #1c1c1e; /* Fundo escuro moderno */
                border-radius: 12px; 
                border: 1px solid #333333; 
            }
        """)
        layout.addWidget(self.frame)
        
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(12, 8, 12, 8)
        frame_layout.setSpacing(4)
        
        # --- CABEÇALHO (Ícone + App + Tempo) ---
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)
        
        self.lbl_app_icon = QLabel("🎵") # Pode trocar por um QIcon depois
        self.lbl_app_icon.setStyleSheet("border: none; background: transparent; font-size: 10px;")
        
        self.lbl_app_name = QLabel("Música • Agora")
        self.lbl_app_name.setStyleSheet("color: #8e8e93; font-size: 10px; border: none; background: transparent;")
        
        header_layout.addWidget(self.lbl_app_icon)
        header_layout.addWidget(self.lbl_app_name)
        header_layout.addStretch()
        frame_layout.addLayout(header_layout)
        
        # --- CORPO (Capa + Título/Artista + Botões) ---
        body_layout = QHBoxLayout()
        body_layout.setSpacing(10)
        
        # Capa do Álbum
        self.lbl_cover = QLabel()
        self.lbl_cover.setFixedSize(40, 40)
        self.lbl_cover.setStyleSheet("background-color: #2c2c2e; border-radius: 6px; border: none;")
        self.lbl_cover.setAlignment(Qt.AlignCenter)
        self.lbl_cover.setText("💿") # Placeholder
        
        # Textos (Título e Artista)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        
        self.lbl_title = QLabel("Nenhuma faixa")
        self.lbl_title.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold; border: none; background: transparent;")
        
        self.lbl_artist = QLabel("Desconhecido")
        self.lbl_artist.setStyleSheet("color: #8e8e93; font-size: 11px; border: none; background: transparent;")
        
        text_layout.addWidget(self.lbl_title)
        text_layout.addWidget(self.lbl_artist)
        text_layout.addStretch()
        
        # Botões de Controlo
        btn_style = """
            QPushButton { background: transparent; border: none; color: #ffffff; font-size: 14px; }
            QPushButton:hover { color: #0a84ff; }
        """
        self.btn_play = QPushButton("▶️")
        self.btn_next = QPushButton("⏭️")
        self.btn_close = QPushButton("✖")
        
        for btn in [self.btn_play, self.btn_next, self.btn_close]:
            btn.setFixedSize(24, 24)
            btn.setStyleSheet(btn_style)
            btn.setCursor(Qt.PointingHandCursor)
            
        self.btn_close.clicked.connect(self.hide_toast)
        
        # Montagem do Corpo
        body_layout.addWidget(self.lbl_cover)
        body_layout.addLayout(text_layout)
        body_layout.addStretch()
        body_layout.addWidget(self.btn_play)
        body_layout.addWidget(self.btn_next)
        body_layout.addWidget(self.btn_close)
        
        frame_layout.addLayout(body_layout)

    def update_info(self, title, artist, cover_pixmap=None):
        # Trunca o texto se for muito longo
        self.lbl_title.setText(title[:25] + "..." if len(title) > 25 else title)
        self.lbl_artist.setText(artist[:25] + "..." if len(artist) > 25 else artist)
        
        if cover_pixmap:
            self.lbl_cover.setPixmap(cover_pixmap.scaled(40, 40, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        else:
            self.lbl_cover.setText("💿") # Reset ao placeholder

    def show_toast(self, position_name="bottom_right"):
        # Garante que a notificação se posiciona corretamente no ecrã ativo
        screen_geo = QApplication.primaryScreen().availableGeometry()
        
        margin = 20
        x, y = 0, 0
        
        if position_name == "top_right":
            x = screen_geo.right() - self.width() - margin
            y = screen_geo.top() + margin
        elif position_name == "bottom_right":
            x = screen_geo.right() - self.width() - margin
            y = screen_geo.bottom() - self.height() - margin
        elif position_name == "top_left":
            x = screen_geo.left() + margin
            y = screen_geo.top() + margin
        elif position_name == "bottom_left":
            x = screen_geo.left() + margin
            y = screen_geo.bottom() - self.height() - margin
            
        self.move(x, y)
        self.show()
        
        # Inicia a animação de Fade In
        self.anim.stop()
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()
        
        # Reinicia o timer para esconder
        self.hide_timer.start()

    def hide_toast(self):
        self.anim.stop()
        self.anim.setStartValue(self.opacity_effect.opacity())
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(self.hide) # Esconde a janela quando o fade out terminar
        self.anim.start()
        self.hide_timer.stop()

    def mousePressEvent(self, event):
        # Opcional: Se clicar no corpo da notificação, ela reinicia o timer
        self.hide_timer.start()
        super().mousePressEvent(event)