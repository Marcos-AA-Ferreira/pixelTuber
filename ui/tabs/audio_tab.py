import sounddevice as sd
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
                             QComboBox, QProgressBar, QCheckBox, QPushButton, \
                             QGroupBox, QScrollArea, QFrame)
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QShortcut, QKeySequence, QPainter, QColor, QPainterPath
from ui.styles.theme import Theme

# === MINI-VISUALIZADOR PARA O PAINEL DE CONTROLE ===
class PreviewVisualizerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bands = [0.0] * 8
        self.style = "Clássico"
        self.bar_color = QColor(0, 255, 150, 220) 
        self.setFixedHeight(50) 

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        num_bars = len(self.bands)
        
        if self.style == "Onda Contínua":
            path = QPainterPath()
            step = w / max(1, num_bars - 1)
            points = [QPointF(i * step, h - (self.bands[i] * h)) for i in range(num_bars)]
            
            path.moveTo(0, h)
            path.lineTo(points[0])
            for i in range(len(points) - 1):
                p1, p2 = points[i], points[i+1]
                ctrl1 = QPointF((p1.x() + p2.x()) / 2, p1.y())
                ctrl2 = QPointF((p1.x() + p2.x()) / 2, p2.y())
                path.cubicTo(ctrl1, ctrl2, p2)
            
            path.lineTo(w, h)
            path.lineTo(0, h)
            painter.setBrush(self.bar_color)
            painter.setPen(Qt.NoPen)
            painter.drawPath(path)
            
        elif self.style == "Pontos de Energia":
            painter.setBrush(self.bar_color)
            painter.setPen(Qt.NoPen)
            spacing = 15
            bar_w = (w - (spacing * (num_bars - 1))) / num_bars
            for i, val in enumerate(self.bands):
                bar_h = val * h
                x = i * (bar_w + spacing)
                radius = min(bar_w / 2, 8)
                center_y = h - bar_h - radius
                painter.drawEllipse(QPointF(x + radius, center_y), radius, radius)
                painter.setOpacity(0.3)
                painter.drawEllipse(QPointF(x + radius, center_y + (radius * 1.5)), radius * 0.7, radius * 0.7)
                painter.setOpacity(1.0)
                
        else:
            spacing = 4
            bar_w = (w - (spacing * (num_bars - 1))) / num_bars
            for i, val in enumerate(self.bands):
                bar_h = val * h
                x = i * (bar_w + spacing)
                if self.style == "Neon Simétrico":
                    painter.fillRect(int(x), int((h / 2) - (bar_h / 2)), int(bar_w), int(bar_h), self.bar_color)
                else: 
                    painter.fillRect(int(x), int(h - bar_h), int(bar_w), int(bar_h), self.bar_color)

# === ABA PRINCIPAL ===
class AudioTab(QWidget):
    def __init__(self, config_manager, audio):
        super().__init__()
        self.cfg = config_manager
        self.audio = audio
        self.profile = config_manager.data
        
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
        self._setup_visualizer_section()
        self._setup_thresholds_section()

        scroll.setWidget(container)
        layout_principal.addWidget(scroll)

    def _setup_input_section(self):
        group = QGroupBox("🎤 ENTRADA DE ÁUDIO")
        layout = QVBoxLayout(group)

        layout.addWidget(QLabel("Dispositivo de Entrada:"))
        self.mic_combo = QComboBox()
        self.refresh_mics()
        
        saved_mic = self.profile.get("audio", {}).get("device_index")
        if saved_mic is not None:
            index = self.mic_combo.findData(saved_mic)
            if index != -1: 
                self.mic_combo.setCurrentIndex(index)
                
        self.mic_combo.currentIndexChanged.connect(self.update_mic)
        layout.addWidget(self.mic_combo)

        feedback_layout = QHBoxLayout()
        self.vol_bar = QProgressBar()
        self.vol_bar.setFixedHeight(15)
        self.vol_bar.setTextVisible(False)
        self.vol_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {Theme.ACCENT_GREEN}; border-radius: 2px; }}")
        
        self.btn_mute = QPushButton("🎤 MUDO (M)")
        self.btn_mute.setObjectName("BtnMute")
        self.btn_mute.setCheckable(True)
        self.btn_mute.setChecked(self.audio.muted)
        self.btn_mute.setFixedWidth(110)
        self.btn_mute.clicked.connect(self.toggle_mute_ui)
        
        feedback_layout.addWidget(self.vol_bar)
        feedback_layout.addWidget(self.btn_mute)
        layout.addLayout(feedback_layout)

        self.mute_shortcut = QShortcut(QKeySequence("M"), self)
        self.mute_shortcut.activated.connect(self.btn_mute.click)

        self.gain_label = QLabel(f"Ganho de Entrada: {self.profile.get('audio', {}).get('gain', 1.0):.1f}x")
        layout.addWidget(self.gain_label)
        self.gain_sld = QSlider(Qt.Horizontal)
        self.gain_sld.setRange(10, 1000) 
        self.gain_sld.setValue(int(self.profile.get("audio", {}).get("gain", 1.0) * 100))
        self.gain_sld.valueChanged.connect(self.update_gain)
        layout.addWidget(self.gain_sld)

        self.main_layout.addWidget(group)

    def _setup_processing_section(self):
        group = QGroupBox("⚙️ PROCESSAMENTO INTELIGENTE")
        layout = QVBoxLayout(group)

        current_noise = self.profile.get("audio", {}).get("noise_gate", 0.02)
        self.audio.noise_threshold = current_noise 
        self.noise_label = QLabel(f"Filtro de Ruído (Gate): {current_noise:.2f}")
        layout.addWidget(self.noise_label)
        
        self.noise_sld = QSlider(Qt.Horizontal)
        self.noise_sld.setRange(0, 50) 
        self.noise_sld.setValue(int(current_noise * 100))
        self.noise_sld.valueChanged.connect(self.update_noise_gate)
        layout.addWidget(self.noise_sld)

        self.chk_bandpass = QCheckBox("Filtro Passa-Banda (Isolar Voz Humana)")
        self.chk_bandpass.setChecked(self.profile.get("audio", {}).get("use_bandpass", True))
        self.audio.use_bandpass = self.chk_bandpass.isChecked()
        self.chk_bandpass.toggled.connect(self.toggle_bandpass)
        layout.addWidget(self.chk_bandpass)

        self.chk_ducking = QCheckBox("Auto-Ducking (Abaixar Música de Fundo ao Falar)")
        self.chk_ducking.setChecked(self.profile.get("audio", {}).get("auto_ducking", True))
        self.chk_ducking.toggled.connect(self.toggle_ducking)
        layout.addWidget(self.chk_ducking)

        self.smooth_check = QCheckBox("✨ Modo Suavizado (Fechamento de boca orgânico)")
        self.smooth_check.setChecked(self.profile.get("audio", {}).get("mode") == "smooth")
        self.smooth_check.toggled.connect(self.toggle_mode)
        layout.addWidget(self.smooth_check)

        layout.addWidget(QLabel("Tempo de Retenção (ms):"))
        self.hold_sld = QSlider(Qt.Horizontal)
        self.hold_sld.setRange(0, 1000)
        self.hold_sld.setValue(int(self.profile.get("audio", {}).get("hold_time", 0.2) * 1000))
        self.hold_sld.valueChanged.connect(self.update_hold)
        layout.addWidget(self.hold_sld)

        self.main_layout.addWidget(group)

    def _setup_visualizer_section(self):
        group = QGroupBox("📊 INDICADORES DE ÁUDIO")
        layout = QVBoxLayout(group)

        self.chk_vis = QCheckBox("Exibir Barra de Som abaixo do Avatar (no OBS)")
        self.chk_vis.setChecked(self.profile.get("visualizer", {}).get("enabled", False))
        self.chk_vis.toggled.connect(self.toggle_visualizer)
        layout.addWidget(self.chk_vis)

        row_style = QHBoxLayout()
        row_style.addWidget(QLabel("Estilo:"))
        self.combo_style = QComboBox()
        self.combo_style.addItems(["Clássico", "Neon Simétrico", "Onda Contínua", "Pontos de Energia"])
        current_style = self.profile.get("visualizer", {}).get("style", "Clássico")
        self.combo_style.setCurrentText(current_style)
        self.combo_style.currentTextChanged.connect(self.change_vis_style)
        row_style.addWidget(self.combo_style)
        layout.addLayout(row_style)
        
        layout.addWidget(QLabel("<small>Prévia do Estilo (Monitoramento):</small>"))
        self.preview_vis = PreviewVisualizerWidget()
        self.preview_vis.style = current_style
        layout.addWidget(self.preview_vis)

        self.main_layout.addWidget(group)

    def _setup_thresholds_section(self):
        group = QGroupBox("📊 LIMITES DE ATIVAÇÃO")
        layout = QVBoxLayout(group)
        layout.addWidget(QLabel("<small>Define o volume necessário para cada estado do Avatar.</small>"))

        for key in ["low", "med", "high", "very_high"]:
            h = QHBoxLayout()
            h.addWidget(QLabel(f"{key.upper()}:"), 1)
            sld = QSlider(Qt.Horizontal)
            sld.setRange(0, 100)
            
            audio_cfg = self.profile.setdefault("audio", {})
            th_cfg = audio_cfg.setdefault("thresholds", {})
            
            sld.setValue(int(th_cfg.get(key, 0.1) * 100))
            sld.valueChanged.connect(lambda v, k=key: self.update_threshold(k, v))
            h.addWidget(sld, 4)
            layout.addLayout(h)

        self.main_layout.addWidget(group)

    def update_ui(self):
        if self.btn_mute.isChecked() != self.audio.muted:
            self.btn_mute.blockSignals(True)
            self.btn_mute.setChecked(self.audio.muted)
            self.btn_mute.setText("🔇 MUTADO (M)" if self.audio.muted else "🎤 MUDO (M)")
            self.btn_mute.blockSignals(False)

        if self.audio.muted:
            self.vol_bar.setValue(0)
            if hasattr(self, 'preview_vis'):
                self.preview_vis.bands = [0.0] * 8
                self.preview_vis.update()
            return
            
        vol = self.audio.get_volume()
        self.vol_bar.setValue(min(int(vol * 100), 100))
        
        if hasattr(self, 'preview_vis') and hasattr(self.audio, 'eq_bands'):
            self.preview_vis.style = self.combo_style.currentText()
            self.preview_vis.bands = list(self.audio.eq_bands) 
            self.preview_vis.update()

    def toggle_mute_ui(self, checked):
        self.audio.muted = checked
        self.btn_mute.setText("🔇 MUTADO (M)" if checked else "🎤 MUDO (M)")

    def update_noise_gate(self, v):
        val = v / 100.0
        self.profile.setdefault("audio", {})["noise_gate"] = val
        self.audio.noise_threshold = val
        self.noise_label.setText(f"Filtro de Ruído (Gate): {val:.2f}")
        self.cfg.save() 

    def toggle_bandpass(self, checked):
        self.audio.use_bandpass = checked
        self.profile.setdefault("audio", {})["use_bandpass"] = checked
        self.cfg.save()

    def toggle_ducking(self, checked):
        self.profile.setdefault("audio", {})["auto_ducking"] = checked
        self.cfg.save()

    def toggle_visualizer(self, checked):
        self.profile.setdefault("visualizer", {})["enabled"] = checked
        self.cfg.save()

    def change_vis_style(self, text):
        self.profile.setdefault("visualizer", {})["style"] = text
        self.cfg.save()

    def update_mic(self, index):
        device_id = self.mic_combo.itemData(index)
        self.profile.setdefault("audio", {})["device_index"] = device_id
        self.audio.change_device(device_id)
        self.cfg.save()

    def update_gain(self, v):
        gain_val = v / 100.0
        self.profile.setdefault("audio", {})["gain"] = gain_val
        self.gain_label.setText(f"Ganho de Entrada: {gain_val:.1f}x")
        self.audio.gain = gain_val
        self.cfg.save()

    def toggle_mode(self, v):
        self.profile.setdefault("audio", {})["mode"] = "smooth" if v else "standard"
        self.cfg.save()

    def update_hold(self, v):
        self.profile.setdefault("audio", {})["hold_time"] = v / 1000.0
        self.cfg.save()

    def update_threshold(self, key, v):
        self.profile.setdefault("audio", {}).setdefault("thresholds", {})[key] = v / 100.0
        self.cfg.save()

    def refresh_mics(self):
        self.mic_combo.clear()
        for i, d in enumerate(sd.query_devices()):
            if d['max_input_channels'] > 0: 
                self.mic_combo.addItem(d['name'], i)