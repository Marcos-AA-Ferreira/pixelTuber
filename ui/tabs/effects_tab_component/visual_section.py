import os
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QFileDialog, QSlider
from PySide6.QtCore import Qt, Signal
from ui.widgets.file_picker import FilePickerWidget

class VisualSection(QFrame):
    # Sinal enviado para o Creator, que por sua vez envia para o Overlay
    previewRequested = Signal() 

    def __init__(self):
        super().__init__()
        self.path_v = ""
        self.init_ui()

    def init_ui(self):
        self.setObjectName("VisualGroup")
        
        main_lay = QVBoxLayout(self)
        main_lay.setSpacing(12)
        
        # --- TÍTULO ---
        header_row = QHBoxLayout()
        header_row.addWidget(QLabel("🖼️ CONFIGURAÇÃO VISUAL"))
        header_row.addStretch()
        main_lay.addLayout(header_row)

        # --- ARQUIVO E TESTE ---
        row_file = QHBoxLayout()
        self.file_picker = FilePickerWidget("SELECIONAR ARQUIVO", "Selecionar Mídia", "Mídia (*.png *.jpg *.gif *.webp *.mp4)")
        
        # Conecta o sinal do nosso componente a um novo método que ativará o botão de teste
        self.file_picker.fileSelected.connect(self._on_file_selected)
        
        self.btn_live = QPushButton("👁️ TESTAR VISUAL")
        self.btn_live.setObjectName("BtnPreview")
        self.btn_live.setEnabled(False) # Começa desativado como o de áudio
        self.btn_live.clicked.connect(lambda: self.previewRequested.emit())
        
        row_file.addWidget(self.file_picker, 1)
        row_file.addWidget(self.btn_live)
        main_lay.addLayout(row_file)

        # --- ESCALA E OPACIDADE ---
        row_props = QHBoxLayout()
        
        # Escala
        scale_lay = QHBoxLayout()
        scale_lay.addWidget(QLabel("ESCALA:"))
        self.scale_in = QLineEdit("1.0")
        self.scale_in.setFixedWidth(50)
        self.scale_in.editingFinished.connect(lambda: self.previewRequested.emit())
        scale_lay.addWidget(self.scale_in)
        row_props.addLayout(scale_lay)
        
        row_props.addSpacing(20)

        # Opacidade
        opacity_lay = QVBoxLayout()
        opacity_header = QHBoxLayout()
        opacity_header.addWidget(QLabel("OPACIDADE:"))
        self.lbl_opacity_val = QLabel("100%")
        self.lbl_opacity_val.setStyleSheet("color: #58a6ff;")
        opacity_header.addWidget(self.lbl_opacity_val, 0, Qt.AlignRight)
        
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self._on_opacity_change)
        
        opacity_lay.addLayout(opacity_header)
        opacity_lay.addWidget(self.opacity_slider)
        row_props.addLayout(opacity_lay, 1)
        
        main_lay.addLayout(row_props)

        # --- POSIÇÃO (X, Y) ---
        row_pos = QHBoxLayout()
        row_pos.addWidget(QLabel("POSIÇÃO TELA:"))
        
        self.pos_x = QLineEdit("500")
        self.pos_x.setFixedWidth(60)
        self.pos_y = QLineEdit("15")
        self.pos_y.setFixedWidth(60)
        
        self.pos_x.editingFinished.connect(lambda: self.previewRequested.emit())
        self.pos_y.editingFinished.connect(lambda: self.previewRequested.emit())
        
        row_pos.addStretch()
        row_pos.addWidget(QLabel("X:"))
        row_pos.addWidget(self.pos_x)
        row_pos.addWidget(QLabel("Y:"))
        row_pos.addWidget(self.pos_y)
        main_lay.addLayout(row_pos)

    def update_position_fields(self, x, y):
        self.blockSignals(True) 
        self.pos_x.setText(str(int(x)))
        self.pos_y.setText(str(int(y)))
        self.blockSignals(False)

    def _on_opacity_change(self, val):
        self.lbl_opacity_val.setText(f"{val}%")
        if self.path_v:
            self.previewRequested.emit()

    def _on_file_selected(self, path):
        self.path_v = path
        self.btn_live.setEnabled(True) # Ativa o botão de teste
        self.previewRequested.emit()

    def get_data(self):
        try:
            scale_txt = self.scale_in.text().replace(',', '.')
            scale = float(scale_txt) if scale_txt else 1.0
            x = int(self.pos_x.text()) if self.pos_x.text() else 500
            y = int(self.pos_y.text()) if self.pos_y.text() else 15
        except ValueError:
            scale, x, y = 1.0, 500, 15
        
        return {
            "visual": self.path_v, 
            "scale": scale, 
            "opacity": self.opacity_slider.value() / 100.0,
            "x": x, 
            "y": y
        }

    def load_data(self, data):
        self.blockSignals(True)
        self.path_v = data.get("visual", "")
        self.scale_in.setText(str(data.get("scale", 1.0)))
        self.opacity_slider.setValue(int(data.get("opacity", 1.0) * 100))
        self.lbl_opacity_val.setText(f"{self.opacity_slider.value()}%")
        self.pos_x.setText(str(data.get("x", 500)))
        self.pos_y.setText(str(data.get("y", 15)))
        
        # ✅ O FilePickerWidget cuida da estética do botão automaticamente!
        self.file_picker.set_path(self.path_v)
        self.btn_live.setEnabled(bool(self.path_v))

        self.blockSignals(False)

    def reset(self):
        self.path_v = ""
        self.scale_in.setText("1.0")
        self.opacity_slider.setValue(100)
        self.pos_x.setText("500")
        self.pos_y.setText("15")
        
        # ✅ Reseta o botão para o estado original
        self.file_picker.set_path("")
        self.btn_live.setEnabled(False)