# ui/tabs/audio_tab.py
import sounddevice as sd
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QProgressBar, QCheckBox, QPushButton, 
                             QGroupBox, QScrollArea, QFrame)
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QShortcut, QKeySequence, QPainter, QColor, QPainterPath

from ui.styles.theme import Theme
from ui.widgets.labeled_slider import LabeledSlider  # <-- IMPORTAÇÃO DO NOVO WIDGET

# === MINI-VISUALIZADOR PARA O PAINEL DE CONTROLE (MANTIDO INTACTO) ===
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
    def __init__(self, config_manager, audio_manager):
        super().__init__()
        self.cfg = config_manager
        self.profile = self.cfg.data       
        self.audio = audio_manager
        
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

        # 1. SINTONIZANDO NOS SINAIS
        self.audio.volumeChanged.connect(self.atualizar_barra_de_volume)
        self.audio.muteToggled.connect(self.atualizar_botao_mudo)
        self.audio.muteToggled.connect(self.update_mute_ui)
        self.audio.audioProcessed.connect(self.update_audio_ui)
        
        # Certifique-se de que o clique do botão de mudo apenas chame o Core
        self.btn_mute.clicked.connect(self.on_mute_clicked)

    # 2. FUNÇÕES "SLOT" QUE REAGEM AOS SINAIS
    def atualizar_barra_de_volume(self, volume_atual):
        # Converte o volume (0.0 a 1.0) para porcentagem (0 a 100)
        porcentagem = int(volume_atual * 100)
        # Usando o nome correto da sua barra de progresso:
        self.vol_bar.setValue(porcentagem)

    def atualizar_botao_mudo(self, esta_mutado):
        # Usando o nome correto do seu botão:
        self.btn_mute.blockSignals(True) # Impede loop infinito de sinais
        self.btn_mute.setChecked(esta_mutado)
        self.btn_mute.setText("🔇 MUTADO (M)" if esta_mutado else "🎤 MUDO (M)")
        self.btn_mute.blockSignals(False)

    # ================================================================
    # MONTAGEM DA INTERFACE (MUITO MAIS LIMPA!)
    # ================================================================

    def _setup_input_section(self):
        group = QGroupBox("🎤 ENTRADA DE ÁUDIO")
        layout = QVBoxLayout(group)

        layout.addWidget(QLabel("Dispositivo de Entrada:"))

        # Combobox de Microfone com Botão de Atualizar (Hotplug)
        row_mic = QHBoxLayout()
        self.mic_combo = QComboBox()
        self.mic_combo.currentIndexChanged.connect(self.update_mic)

        self.btn_refresh_mic = QPushButton("🔄")
        self.btn_refresh_mic.setFixedSize(28, 28)
        self.btn_refresh_mic.setToolTip("Atualizar lista de dispositivos USB/P2")
        self.btn_refresh_mic.clicked.connect(self.refresh_mics)

        row_mic.addWidget(self.mic_combo)
        row_mic.addWidget(self.btn_refresh_mic)
        layout.addLayout(row_mic)

        self.refresh_mics()

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
        self.btn_mute.clicked.connect(self.on_mute_clicked)
        
        feedback_layout.addWidget(self.vol_bar)
        feedback_layout.addWidget(self.btn_mute)
        layout.addLayout(feedback_layout)

        self.mute_shortcut = QShortcut(QKeySequence("M"), self)
        self.mute_shortcut.activated.connect(self.btn_mute.click)
        self.btn_mute.clicked.connect(self.on_mute_clicked)
        self.audio.muteToggled.connect(self.update_mute_ui)

        # 🌟 APLICANDO O NOSSO COMPONENTE DRY:
        curr_gain = self.profile.get("audio", {}).get("gain", 1.0)
        self.gain_slider = LabeledSlider("Ganho de Entrada:", min_val=0.1, max_val=10.0, default_val=curr_gain, divider=100, value_format="{v:.1f}x")
        self.gain_slider.valueChanged.connect(self.update_gain)
        layout.addWidget(self.gain_slider)

        self.main_layout.addWidget(group)

    def _setup_processing_section(self):
        group = QGroupBox("⚙️ PROCESSAMENTO INTELIGENTE")
        layout = QVBoxLayout(group)

        # 🌟 APLICANDO O NOSSO COMPONENTE DRY:
        curr_noise = self.profile.get("audio", {}).get("noise_gate", 0.02)
        self.audio.noise_threshold = curr_noise 
        
        self.noise_slider = LabeledSlider("Filtro de Ruído (Gate):", min_val=0.0, max_val=0.5, default_val=curr_noise, divider=100, value_format="{v:.2f}")
        self.noise_slider.valueChanged.connect(self.update_noise_gate)
        layout.addWidget(self.noise_slider)

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

        # 🌟 APLICANDO O NOSSO COMPONENTE DRY:
        curr_hold = self.profile.get("audio", {}).get("hold_time", 0.2)
        self.hold_slider = LabeledSlider("Tempo de Retenção:", min_val=0.0, max_val=1.0, default_val=curr_hold, divider=1000, value_format="{v:.3f}s")
        self.hold_slider.valueChanged.connect(self.update_hold)
        layout.addWidget(self.hold_slider)

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

        th_cfg = self.profile.setdefault("audio", {}).setdefault("thresholds", {})
        
        # 🌟 APLICANDO O COMPONENTE NO LOOP! (Menos 10 linhas de código por loop)
        for key in ["low", "med", "high", "very_high"]:
            val = th_cfg.get(key, 0.1)
            sld = LabeledSlider(f"{key.upper()}:", min_val=0.0, max_val=1.0, default_val=val, divider=100, value_format="{v:.2f}")
            sld.valueChanged.connect(lambda v, k=key: self.update_threshold(k, v))
            layout.addWidget(sld)

        self.main_layout.addWidget(group)

    # ================================================================
    # LÓGICA DE EVENTOS (MAIS LIMPA E DIRETA)
    # ================================================================

    def on_mute_clicked(self):
        """Disparado ao clicar no botão. Altera o estado no Core."""
        self.audio.toggle_mute()

    def update_mute_ui(self, is_muted):
        """Reage à alteração real do Core e atualiza o visual da janela."""
        if is_muted:
            self.btn_mute.setText("🔇 DESMUTAR")
            # Se usares estilos CSS do teu Theme:
            if hasattr(Theme, 'BUTTON_MUTE_ACTIVE'):
                self.btn_mute.setStyleSheet(Theme.BUTTON_MUTE_ACTIVE)
        else:
            self.btn_mute.setText("🎙️ MUTAR")
            if hasattr(Theme, 'BUTTON_BASE'):
                self.btn_mute.setStyleSheet(Theme.BUTTON_BASE)

    def update_audio_ui(self, volume, eq_bands):
        """Slot acionado AUTOMATICAMENTE a cada bloco de som processado pelo hardware."""
        # Se estiver mutado, não gaste processamento atualizando gráficos de som
        if self.audio.muted:
            return
            
        # Sincroniza a barra de volume com o valor exato emitido pelo sinal do microfone
        self.vol_bar.setValue(min(int(volume * 100), 100))
        
        # Atualiza o mini-visualizador integrado do painel
        if hasattr(self, 'preview_vis'):
            self.preview_vis.style = self.combo_style.currentText()
            self.preview_vis.bands = list(eq_bands)
            self.preview_vis.update()

    # --- Os demais métodos permanecem iguais (apenas repassando dados ao Core) ---
    def update_noise_gate(self, val):
        self.audio.set_noise_gate(val)

    def toggle_bandpass(self, checked):
        self.audio.set_use_bandpass(checked)

    def toggle_ducking(self, checked):
        self.audio.set_auto_ducking(checked)

    def toggle_visualizer(self, checked):
        self.audio.set_visualizer_enabled(checked)

    def change_vis_style(self, text):
        self.audio.set_visualizer_style(text)

    def update_mic(self, index):
        device_id = self.mic_combo.itemData(index)
        self.audio.change_device(device_id)

    def update_gain(self, val):
        self.audio.set_gain(val)

    def toggle_mode(self, checked):
        mode = "smooth" if checked else "standard"
        self.audio.set_mode(mode)

    def update_hold(self, val):
        self.audio.set_hold_time(val)

    def update_threshold(self, key, val):
        self.audio.set_threshold(key, val)

    def refresh_mics(self):
        """Reinicia o motor de áudio temporariamente, detecta hardware novo e filtra lixo."""
        was_running = self.audio.stream is not None
        if was_running:
            self.audio.stop()

        sd._terminate()
        sd._initialize()

        self.mic_combo.blockSignals(True)
        self.mic_combo.clear()

        banned_words = ["mapeador", "mapper", "primary", "principal"]
        
        for i, d in enumerate(sd.query_devices()):
            if d['max_input_channels'] > 0:
                name = d['name']
                if any(banned in name.lower() for banned in banned_words):
                    continue
                api = sd.query_hostapis(d['hostapi'])['name']
                display_name = name if "MME" in api else f"{name} [{api}]"
                self.mic_combo.addItem(display_name, i)

        saved_mic = self.profile.get("audio", {}).get("device_index")
        if saved_mic is not None:
            idx = self.mic_combo.findData(saved_mic)
            if idx != -1:
                self.mic_combo.setCurrentIndex(idx)
            elif self.mic_combo.count() > 0:
                self.mic_combo.setCurrentIndex(0)
                self.update_mic(0)
        elif self.mic_combo.count() > 0:
            self.mic_combo.setCurrentIndex(0)
            self.update_mic(0)

        self.mic_combo.blockSignals(False)

        if was_running:
            self.audio.start()