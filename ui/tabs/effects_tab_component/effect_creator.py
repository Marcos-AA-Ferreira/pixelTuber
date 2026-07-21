import uuid
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QMessageBox, QFileDialog, 
                             QCheckBox, QStackedWidget, QWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QKeySequence, QIcon

try:
    from .visual_section import VisualSection
    from .audio_section import AudioSection
except ImportError:
    from visual_section import VisualSection
    from audio_section import AudioSection

class EffectCreator(QDialog):
    effect_created = Signal(dict)
    test_requested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.editing_id = None
        self.temp_hotkey = ""
        self.icon_path = "" 
        
        # Configurações da Janela Modal (Pop-up)
        self.setWindowTitle("Configurar Efeito Customizado")
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setModal(True) # Bloqueia a janela de trás enquanto esta estiver aberta
        self.setMinimumWidth(500)
        
        self.init_ui()

    def init_ui(self):
        self.setObjectName("MainForm")
        
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(30, 30, 30, 30)
        main_lay.setSpacing(20)

        # --- NOME E ATALHO ---
        row1 = QHBoxLayout()
        self.name_in = QLineEdit()
        self.name_in.setPlaceholderText("Nome do efeito...")
        
        self.btn_capture = QPushButton("⌨️ ATALHO")
        self.btn_capture.setCheckable(True)
        self.btn_capture.setFixedWidth(100)
        self.btn_capture.setStyleSheet("background: #3d3d3d; color: white; border-radius: 6px;")
        self.btn_capture.clicked.connect(self.start_capture)
        
        self.lbl_hk = QLabel("NENHUM")
        self.lbl_hk.setStyleSheet("color: #f1c40f; font-family: 'Consolas'; font-weight: bold;")
        
        row1.addWidget(self.name_in)
        row1.addWidget(self.btn_capture)
        row1.addWidget(self.lbl_hk)
        main_lay.addLayout(row1)

        # --- SEÇÃO DE CONFIGURAÇÃO (ÍCONE E DURAÇÃO) ---
        config_lay = QHBoxLayout()
        
        # 1. SELETOR DE ÍCONE
        icon_box = QVBoxLayout()
        icon_box.addWidget(QLabel("ÍCONE DO CARD", objectName="SubLabel"))
        
        mode_switcher = QHBoxLayout()
        self.btn_mode_emoji = QPushButton("EMOJI")
        self.btn_mode_emoji.setObjectName("ModeBtn")
        self.btn_mode_emoji.setCheckable(True)
        self.btn_mode_emoji.setChecked(True)
        
        self.btn_mode_image = QPushButton("IMAGEM")
        self.btn_mode_image.setObjectName("ModeBtn")
        self.btn_mode_image.setCheckable(True)

        self.btn_mode_emoji.clicked.connect(lambda: self.switch_icon_mode("emoji"))
        self.btn_mode_image.clicked.connect(lambda: self.switch_icon_mode("image"))
        
        mode_switcher.addWidget(self.btn_mode_emoji)
        mode_switcher.addWidget(self.btn_mode_image)
        icon_box.addLayout(mode_switcher)

        self.icon_stack = QStackedWidget()
        
        self.emoji_in = QLineEdit()
        self.emoji_in.setPlaceholderText("Cole um emoji...")
        self.emoji_in.setAlignment(Qt.AlignCenter)
        self.icon_stack.addWidget(self.emoji_in)
        
        self.btn_select_img = QPushButton("📁 BUSCAR IMAGEM")
        self.btn_select_img.setStyleSheet("background: #3d3d3d; color: white; border-radius: 6px; padding: 5px;")
        self.btn_select_img.clicked.connect(self.select_icon_image)
        self.icon_stack.addWidget(self.btn_select_img)
        
        icon_box.addWidget(self.icon_stack)
        config_lay.addLayout(icon_box, 1)

        # 2. SELETOR DE DURAÇÃO
        dur_box = QVBoxLayout()
        dur_box.addWidget(QLabel("DURAÇÃO (MS)", objectName="SubLabel"))
        
        dur_ctrl = QHBoxLayout()
        btn_minus = QPushButton("-")
        btn_minus.setObjectName("StepBtn")
        btn_minus.clicked.connect(lambda: self.adjust_duration(-500))
        
        self.dur_display = QLabel("4000")
        self.dur_display.setObjectName("DurDisplay")
        self.dur_display.setAlignment(Qt.AlignCenter)
        
        btn_plus = QPushButton("+")
        btn_plus.setObjectName("StepBtn")
        btn_plus.clicked.connect(lambda: self.adjust_duration(500))
        
        dur_ctrl.addWidget(btn_minus)
        dur_ctrl.addWidget(self.dur_display)
        dur_ctrl.addWidget(btn_plus)
        dur_box.addLayout(dur_ctrl)

        self.sync_check = QCheckBox("Sincronizar Áudio")
        self.sync_check.setChecked(True)
        self.sync_check.setStyleSheet("color: #888; font-size: 11px;")
        dur_box.addWidget(self.sync_check, 0, Qt.AlignCenter)

        config_lay.addLayout(dur_box, 1)
        main_lay.addLayout(config_lay)

        # --- COMPONENTES ---
        self.visual_module = VisualSection()
        self.audio_module = AudioSection()
        
        self.audio_module.trimmer.valuesChanged.connect(self.auto_sync_duration)
        self.visual_module.previewRequested.connect(self.request_test) 
        
        main_lay.addWidget(self.visual_module)
        main_lay.addWidget(self.audio_module)

        # --- BOTÕES FINAIS ---
        action_lay = QHBoxLayout()
        self.btn_cancel = QPushButton("CANCELAR")
        self.btn_cancel.setObjectName("CancelBtn")
        self.btn_cancel.clicked.connect(self.reject) # Fecha janela sem salvar
        
        self.btn_save = QPushButton("✨ SALVAR EFEITO")
        self.btn_save.setObjectName("SaveBtn")
        self.btn_save.clicked.connect(self.submit)
        
        action_lay.addWidget(self.btn_cancel)
        action_lay.addWidget(self.btn_save)
        main_lay.addLayout(action_lay)

    def adjust_duration(self, delta):
        current = int(self.dur_display.text())
        new_val = max(100, min(60000, current + delta))
        self.dur_display.setText(str(new_val))

    def auto_sync_duration(self, start, end):
        if self.sync_check.isChecked():
            duration_ms = int((end - start) * 1000)
            if duration_ms > 0:
                self.dur_display.setText(str(duration_ms))

    def request_test(self):
        v_data = self.visual_module.get_data()
        a_data = self.audio_module.get_data()
        
        test_data = {
            "id": "preview_temp",
            "name": self.name_in.text().strip() or "Teste Visual",
            "hotkey": self.temp_hotkey,
            "emoji": self.emoji_in.text() or "✨",
            "image_icon": self.icon_path,
            "duration": int(self.dur_display.text()),
            **v_data,
            **a_data
        }
        
        if v_data.get("visual"):
            self.test_requested.emit(test_data)

    def switch_icon_mode(self, mode):
        if mode == "emoji":
            self.btn_mode_emoji.setChecked(True)
            self.btn_mode_image.setChecked(False)
            self.icon_stack.setCurrentIndex(0)
            self.icon_path = ""
        else:
            self.btn_mode_emoji.setChecked(False)
            self.btn_mode_image.setChecked(True)
            self.icon_stack.setCurrentIndex(1)

    def select_icon_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Ícone", "", "Imagens (*.png *.jpg *.webp)")
        if path:
            self.icon_path = path
            self.btn_select_img.setText(f"✅ {os.path.basename(path)[:15]}...")
            self.request_test() 

    def _collect_data(self):
        name = self.name_in.text().strip()
        if not name:
            QMessageBox.warning(self, "Erro", "Dê um nome ao efeito antes de salvar!")
            return None
        
        v_data = self.visual_module.get_data()
        a_data = self.audio_module.get_data()
        
        return {
            "id": self.editing_id or f"eff_{uuid.uuid4().hex[:6]}",
            "name": name,
            "hotkey": self.temp_hotkey,
            "emoji": self.emoji_in.text() or "✨",
            "image_icon": self.icon_path,
            "duration": int(self.dur_display.text()),
            **v_data,
            **a_data
        }

    def start_capture(self):
        if self.btn_capture.isChecked():
            self.btn_capture.setText("...")
            self.setFocus()

    def keyPressEvent(self, event: QKeyEvent):
        if self.btn_capture.isChecked():
            key = event.key()
            if key in [Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt]: return
            seq = QKeySequence(event.modifiers() | key).toString().lower()
            self.temp_hotkey = seq
            self.lbl_hk.setText(seq.upper())
            self.btn_capture.setChecked(False)
            self.btn_capture.setText("⌨️ ATALHO")

    def submit(self):
        data = self._collect_data()
        if data:
            self.effect_created.emit(data)
            self.accept() # Fecha a janela modal após salvar

    def load_effect(self, eid, data):
        self.editing_id = eid
        self.name_in.setText(data.get("name", ""))
        self.temp_hotkey = data.get("hotkey", "")
        self.lbl_hk.setText(self.temp_hotkey.upper() if self.temp_hotkey else "NENHUM")
        
        self.icon_path = data.get("image_icon", "")
        if self.icon_path:
            self.switch_icon_mode("image")
            self.btn_select_img.setText(f"✅ {os.path.basename(self.icon_path)[:15]}...")
        else:
            self.switch_icon_mode("emoji")
            self.emoji_in.setText(data.get("emoji", "✨"))
            
        self.dur_display.setText(str(data.get("duration", 4000)))
        self.visual_module.load_data(data)
        self.audio_module.load_data(data.get("audio", ""), data.get("audio_start", 0.0), data.get("audio_end", 0.0))