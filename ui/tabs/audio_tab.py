import sounddevice as sd
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
                             QComboBox, QProgressBar, QCheckBox, QPushButton, 
                             QGroupBox, QScrollArea, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence
from ui.styles.theme import Theme

class AudioTab(QWidget):
    def __init__(self, config_manager, audio):
        super().__init__()
        self.cfg = config_manager
        self.audio = audio
        self.profile = config_manager.data
        
        # Estilo unificado
        self.setStyleSheet(Theme.MAIN_TAB_STYLE + Theme.GROUP_BOX + 
                           Theme.BUTTON_BASE + Theme.BUTTON_MUTE_ACTIVE)

        layout_principal = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        self.main_layout = QVBoxLayout(container)
        
        self._setup_input_section()
        self._setup_processing_section()
        self._setup_thresholds_section()

        scroll.setWidget(container)
        layout_principal.addWidget(scroll)

    def _setup_input_section(self):
        group = QGroupBox("🎤 ENTRADA DE ÁUDIO")
        layout = QVBoxLayout(group)

        # Seleção de Mic
        layout.addWidget(QLabel("Dispositivo de Entrada:"))
        self.mic_combo = QComboBox()
        self.refresh_mics()
        saved_mic = self.profile["audio"].get("device_index")
        if saved_mic is not None:
            index = self.mic_combo.findData(saved_mic)
            if index != -1: self.mic_combo.setCurrentIndex(index)
        self.mic_combo.currentIndexChanged.connect(self.update_mic)
        layout.addWidget(self.mic_combo)

        # Feedback Visual e Mudo
        feedback_layout = QHBoxLayout()
        self.vol_bar = QProgressBar()
        self.vol_bar.setFixedHeight(15)
        self.vol_bar.setTextVisible(False)
        self.vol_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {Theme.ACCENT_GREEN}; border-radius: 2px; }}")
        
        self.btn_mute = QPushButton("🎤 MUDO (M)")
        self.btn_mute.setObjectName("BtnMute")
        self.btn_mute.setCheckable(True)
        self.btn_mute.setFixedWidth(110)
        self.btn_mute.clicked.connect(self.toggle_mute_ui)
        
        feedback_layout.addWidget(self.vol_bar)
        feedback_layout.addWidget(self.btn_mute)
        layout.addLayout(feedback_layout)

        # Atalho Tecla M
        self.mute_shortcut = QShortcut(QKeySequence("M"), self)
        self.mute_shortcut.activated.connect(self.btn_mute.click)

        # Ganho
        self.gain_label = QLabel(f"Ganho de Entrada: {self.profile['audio'].get('gain', 1.0):.1f}x")
        layout.addWidget(self.gain_label)
        self.gain_sld = QSlider(Qt.Horizontal)
        self.gain_sld.setRange(10, 1000) 
        self.gain_sld.setValue(int(self.profile["audio"].get("gain", 1.0) * 100))
        self.gain_sld.valueChanged.connect(self.update_gain)
        layout.addWidget(self.gain_sld)

        self.main_layout.addWidget(group)

    def _setup_processing_section(self):
        group = QGroupBox("⚙️ PROCESSAMENTO")
        layout = QVBoxLayout(group)

        # Noise Gate
        current_noise = self.profile["audio"].get("noise_gate", 0.02)
        self.audio.noise_threshold = current_noise 
        self.noise_label = QLabel(f"Filtro de Ruído (Gate): {current_noise:.2f}")
        layout.addWidget(self.noise_label)
        
        self.noise_sld = QSlider(Qt.Horizontal)
        self.noise_sld.setRange(0, 50) 
        self.noise_sld.setValue(int(current_noise * 100))
        self.noise_sld.valueChanged.connect(self.update_noise_gate)
        layout.addWidget(self.noise_sld)

        # Modo Smooth e Hold
        self.smooth_check = QCheckBox("✨ Modo Suavizado (Smooth Transition)")
        self.smooth_check.setChecked(self.profile["audio"].get("mode") == "smooth")
        self.smooth_check.toggled.connect(self.toggle_mode)
        layout.addWidget(self.smooth_check)

        layout.addWidget(QLabel("Tempo de Retenção (ms):"))
        self.hold_sld = QSlider(Qt.Horizontal)
        self.hold_sld.setRange(0, 1000)
        self.hold_sld.setValue(int(self.profile["audio"].get("hold_time", 0.2) * 1000))
        self.hold_sld.valueChanged.connect(self.update_hold)
        layout.addWidget(self.hold_sld)

        self.main_layout.addWidget(group)

    def _setup_thresholds_section(self):
        group = QGroupBox("📊 LIMITES DE ATIVAÇÃO")
        layout = QVBoxLayout(group)
        
        layout.addWidget(QLabel("<small>Define o volume necessário para cada estado.</small>"))

        for key in ["low", "med", "high", "very_high"]:
            h = QHBoxLayout()
            h.addWidget(QLabel(f"{key.upper()}:"), 1)
            sld = QSlider(Qt.Horizontal)
            sld.setRange(0, 100)
            sld.setValue(int(self.profile["audio"]["thresholds"].get(key, 0.1) * 100))
            sld.valueChanged.connect(lambda v, k=key: self.update_threshold(k, v))
            h.addWidget(sld, 4)
            layout.addLayout(h)

        self.main_layout.addWidget(group)

    def update_ui(self):
        if self.audio.muted:
            self.vol_bar.setValue(0)
            return
        vol = self.audio.get_volume()
        self.vol_bar.setValue(min(int(vol * 100), 100))

    def toggle_mute_ui(self, checked):
        self.audio.muted = checked
        self.btn_mute.setText("🔇 MUTADO (M)" if checked else "🎤 MUDO (M)")

    def update_noise_gate(self, v):
        val = v / 100.0
        self.profile["audio"]["noise_gate"] = val
        self.audio.noise_threshold = val
        self.noise_label.setText(f"Filtro de Ruído (Gate): {val:.2f}")

    def update_mic(self, index):
        device_id = self.mic_combo.itemData(index)
        self.profile["audio"]["device_index"] = device_id
        self.audio.change_device(device_id)
        self.cfg.save()

    def update_gain(self, v):
        gain_val = v / 100.0
        self.profile["audio"]["gain"] = gain_val
        self.gain_label.setText(f"Ganho de Entrada: {gain_val:.1f}x")
        self.audio.gain = gain_val
        self.cfg.save()

    def toggle_mode(self, v):
        self.profile["audio"]["mode"] = "smooth" if v else "standard"
        self.cfg.save()

    def update_hold(self, v):
        self.profile["audio"]["hold_time"] = v / 1000.0
        self.cfg.save()

    def update_threshold(self, key, v):
        self.profile["audio"]["thresholds"][key] = v / 100.0
        self.cfg.save()

    def refresh_mics(self):
        self.mic_combo.clear()
        for i, d in enumerate(sd.query_devices()):
            if d['max_input_channels'] > 0: 
                self.mic_combo.addItem(d['name'], i)