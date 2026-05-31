import os
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Qt, Signal, QSize, QTimer

class EffectCard(QFrame):
    clicked_delete = Signal(str)
    clicked_edit = Signal(str)

    def __init__(self, eid, data, overlay_manager):
        super().__init__()
        self.eid = eid
        self.data = data
        self.overlay = overlay_manager 
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(115, 165)
        # Estilo refinado para o card
        self.setStyleSheet("""
            QFrame { background-color: #0d1117; border: 1px solid #30363d; border-radius: 8px; }
            QFrame:hover { border: 1px solid #58a6ff; }
            QPushButton { border: none; background: transparent; }
            QPushButton:hover { background: #1f242b; border-radius: 4px; }
        """)
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)

        # --- CABEÇALHO (LED E HOTKEY) ---
        header = QHBoxLayout()
        
        # O LED agora representa o estado de "Em uso"
        self.led = QLabel()
        self.led.setFixedSize(10, 10)
        self.set_led_state(False) # Inicia em Vermelho (Inativo)
        
        hk_text = self.data.get('hotkey', '').upper()
        self.lbl_hk = QLabel(hk_text if hk_text else "---")
        self.lbl_hk.setStyleSheet("color: #d4a017; font-size: 9px; font-weight: bold; font-family: 'Consolas';")
        
        header.addWidget(self.led)
        header.addStretch()
        header.addWidget(self.lbl_hk)
        lay.addLayout(header)

        # --- BOTÃO CENTRAL (PLAY) ---
        self.btn_play = QPushButton()
        self.btn_play.setCursor(Qt.PointingHandCursor)
        
        img_path = self.data.get('image_icon', '')
        if img_path and os.path.exists(img_path):
            icon = QIcon(img_path)
            self.btn_play.setIcon(icon)
            self.btn_play.setIconSize(QSize(55, 55))
        else:
            self.btn_play.setText(self.data.get('emoji', '✨'))
            self.btn_play.setFont(QFont("Segoe UI Emoji", 26))

        # Ao clicar no play, ativamos o LED e chamamos o overlay
        self.btn_play.clicked.connect(self.trigger_effect)
        lay.addWidget(self.btn_play, 0, Qt.AlignCenter)

        # --- NOME DO EFEITO ---
        name = QLabel(self.data.get('name', 'Sem Nome'))
        name.setAlignment(Qt.AlignCenter)
        name.setStyleSheet("color: #c9d1d9; font-size: 10px; border: none; font-weight: bold;")
        name.setWordWrap(True)
        lay.addWidget(name)

        # --- BOTÕES DE AÇÃO (Limpado e Centralizado) ---
        btns_row = QHBoxLayout()
        btns_row.setSpacing(10)
        
        # Botão Editar
        b_edit = QPushButton("✏️")
        b_edit.setFixedSize(28, 28)
        b_edit.setToolTip("Editar Efeito e Áudio")
        b_edit.clicked.connect(lambda: self.clicked_edit.emit(self.eid))
        
        # Botão Excluir
        b_del = QPushButton("🗑️")
        b_del.setFixedSize(28, 28)
        b_del.setToolTip("Excluir Efeito")
        b_del.clicked.connect(lambda: self.clicked_delete.emit(self.eid))
        
        btns_row.addStretch()
        btns_row.addWidget(b_edit)
        btns_row.addWidget(b_del)
        btns_row.addStretch()
        lay.addLayout(btns_row)

    def set_led_state(self, active: bool):
        """Muda a cor do LED: Verde para ativo, Vermelho para inativo."""
        color = "#2ea043" if active else "#f85149" # Verde vs Vermelho
        glow = f"border: 1px solid {color}; box-shadow: 0 0 5px {color};" if active else ""
        self.led.setStyleSheet(f"""
            background-color: {color}; 
            border-radius: 5px; 
            {glow}
        """)

    def trigger_effect(self):
        """Dispara o efeito e controla o LED baseado na duração."""
        self.set_led_state(True) # Fica Verde
        
        # Envia comando para o Overlay
        self.overlay.play_effect(
            visual_path=self.data.get('visual'),
            audio_path=self.data.get('audio'),
            duration=self.data.get('duration', 4000),
            scale=self.data.get('scale', 1.0),
            opacity=self.data.get('opacity', 1.0),
            x=self.data.get('x', 500),
            y=self.data.get('y', 300),
            audio_start=self.data.get('audio_start', 0.0),
            audio_end=self.data.get('audio_end', 0.0)
        )
        
        # Timer para voltar o LED para vermelho após a duração do efeito
        duration = self.data.get('duration', 4000)
        QTimer.singleShot(duration, lambda: self.set_led_state(False))

    def update_data(self, new_data):
        """Útil para quando editamos o efeito, atualizar o card sem recriar tudo."""
        self.data = new_data
        self.init_ui() # Redesenha com os novos dados (incluindo áudio novo)