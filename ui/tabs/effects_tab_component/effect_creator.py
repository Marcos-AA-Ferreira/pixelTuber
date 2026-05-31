import uuid
import os
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QMessageBox, QFileDialog, 
                             QSpinBox, QCheckBox, QStackedWidget, QWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QKeySequence, QIcon

try:
    from .visual_section import VisualSection
    from .audio_section import AudioSection
except ImportError:
    from visual_section import VisualSection
    from audio_section import AudioSection

class EffectCreator(QFrame):
    effect_created = Signal(dict)
    test_requested = Signal(dict)

    def __init__(self, hotkey_manager):
        super().__init__()
        self.hotkeys = hotkey_manager
        self.editing_id = None
        self.temp_hotkey = ""
        self.icon_path = "" 
        
        self.init_ui()

    def init_ui(self):
        self.setObjectName("MainForm")
        self.setStyleSheet("""
            #MainForm { background-color: #2b2b2b; border-radius: 12px; border: 1px solid #3d3d3d; }
            QLineEdit { 
                padding: 10px; border-radius: 6px; background: #1a1a1a; color: white; border: 1px solid #444; 
            }
            #Title { color: #58a6ff; font-size: 15px; font-weight: bold; }
            #SubLabel { color: #8b949e; font-size: 10px; font-weight: bold; text-transform: uppercase; }
            
            /* Botões de Modo */
            #ModeBtn { background: #3d3d3d; border: 1px solid #555; padding: 5px; font-size: 10px; border-radius: 4px; }
            #ModeBtn:checked { background: #1f6feb; border-color: #58a6ff; }

            /* Botões de Duração (+ / -) */
            #StepBtn { 
                background: #3d3d3d; color: white; border-radius: 15px; 
                font-weight: bold; font-size: 16px; min-width: 30px; max-width: 30px; min-height: 30px;
            }
            #StepBtn:hover { background: #58a6ff; }
            
            #DurDisplay { 
                background: #1a1a1a; color: #58a6ff; font-weight: bold; font-family: 'Consolas';
                font-size: 14px; border: 1px solid #444; border-radius: 6px; padding: 5px 15px;
            }

            #SaveBtn { background: #238636; color: white; font-weight: bold; font-size: 12px; }
        """)
        
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(30, 30, 30, 30)
        main_lay.setSpacing(20)

        # --- CABEÇALHO ---
        self.header_label = QLabel("🚀 CONFIGURAR EFEITO")
        self.header_label.setObjectName("Title")
        main_lay.addWidget(self.header_label)

        # --- NOME E ATALHO ---
        row1 = QHBoxLayout()
        self.name_in = QLineEdit()
        self.name_in.setPlaceholderText("Nome do efeito...")
        
        self.btn_capture = QPushButton("⌨️ ATALHO")
        self.btn_capture.setCheckable(True)
        self.btn_capture.setFixedWidth(100)
        self.btn_capture.clicked.connect(self.start_capture)
        
        self.lbl_hk = QLabel("NENHUM")
        self.lbl_hk.setStyleSheet("color: #f1c40f; font-family: 'Consolas'; font-weight: bold;")
        
        row1.addWidget(self.name_in)
        row1.addWidget(self.btn_capture)
        row1.addWidget(self.lbl_hk)
        main_lay.addLayout(row1)

        # --- SEÇÃO DE CONFIGURAÇÃO (ÍCONE E DURAÇÃO) ---
        config_lay = QHBoxLayout()
        
        # 1. SELETOR DE ÍCONE (MODO EMOJI OU IMAGEM)
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
        self.btn_select_img.clicked.connect(self.select_icon_image)
        self.icon_stack.addWidget(self.btn_select_img)
        
        icon_box.addWidget(self.icon_stack)
        config_lay.addLayout(icon_box, 1)

        # 2. SELETOR DE DURAÇÃO (+ / -)
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
        self.sync_check.setStyleSheet("color: #888; font-size: 9px;")
        dur_box.addWidget(self.sync_check, 0, Qt.AlignCenter)

        config_lay.addLayout(dur_box, 1)
        main_lay.addLayout(config_lay)

        # --- COMPONENTES ---
        self.visual_module = VisualSection()
        self.audio_module = AudioSection()
        
        # --- CONEXÕES DE SINAIS (AJUSTADO) ---
        self.audio_module.trimmer.valuesChanged.connect(self.auto_sync_duration)
        self.visual_module.previewRequested.connect(self.request_test) # <--- CONEXÃO ADICIONADA
        
        main_lay.addWidget(self.visual_module)
        main_lay.addWidget(self.audio_module)

        # --- SALVAR ---
        self.btn_save = QPushButton("✨ SALVAR EFEITO")
        self.btn_save.setObjectName("SaveBtn")
        self.btn_save.setFixedHeight(40)
        self.btn_save.clicked.connect(self.submit)
        main_lay.addWidget(self.btn_save)

    # --- LÓGICA DE DURAÇÃO ---
    def adjust_duration(self, delta):
        current = int(self.dur_display.text())
        new_val = max(100, min(60000, current + delta))
        self.dur_display.setText(str(new_val))

    def auto_sync_duration(self, start, end):
        if self.sync_check.isChecked():
            duration_ms = int((end - start) * 1000)
            if duration_ms > 0:
                self.dur_display.setText(str(duration_ms))

    # --- LÓGICA DE TESTE (MÉTODO ADICIONADO) ---
    def request_test(self):
        """Coleta dados para o overlay sem exigir preenchimento total (ex: nome)."""
        v_data = self.visual_module.get_data()
        a_data = self.audio_module.get_data()
        
        # Criamos o pacote de dados para o overlay
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
        
        # Só emite o sinal se houver um arquivo visual selecionado
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
            self.request_test() # Atualiza o preview ao selecionar imagem

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
            self.reset_form()

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

    def reset_form(self):
        self.editing_id = None
        self.name_in.clear()
        self.emoji_in.clear()
        self.switch_icon_mode("emoji")
        self.dur_display.setText("4000")
        self.temp_hotkey = ""
        self.lbl_hk.setText("NENHUM")
        self.visual_module.reset()
        self.audio_module.reset()