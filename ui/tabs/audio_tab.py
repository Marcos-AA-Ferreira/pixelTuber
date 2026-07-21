# ui/tabs/audio_tab.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QProgressBar, QCheckBox, QPushButton, 
                             QGroupBox, QScrollArea, QFrame)
from PySide6.QtCore import Qt

from ui.widgets.labeled_slider import LabeledSlider
from ui.tabs.audio_tab_component.audio_visualizer import AudioVisualizerWidget
from core.event_bus import EventBus

class AudioTab(QWidget):
    def __init__(self, config_manager):
        super().__init__()
        self.cfg = config_manager
        self.bus = EventBus.instance()
        self.init_ui()
        self.connect_bus_signals()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        self.layout = QVBoxLayout(scroll_content)
        
        self._setup_device_section()
        self._setup_visualizer_section()
        self._setup_processing_section()
        self._setup_thresholds_section()
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        # Pede ao EventBus a lista inicial de microfones
        self.refresh_mics()

    def connect_bus_signals(self):
        """Escuta os retornos do motor de áudio via EventBus"""
        if hasattr(self, 'progress_bar'):
            self.bus.audio_volume_updated.connect(lambda vol: self.progress_bar.setValue(int(vol * 100)))

        if hasattr(self, 'visualizer'):
            self.bus.audio_processed_updated.connect(lambda vol, bands: self.visualizer.update_bands(bands))

        # Quando o EventBus devolver a lista de microfones, roda a função populate_mics
        self.bus.audio_devices_updated.connect(self.populate_mics)

    def _setup_device_section(self):
        group = QGroupBox("Dispositivo de Entrada")
        layout = QVBoxLayout(group)
        
        mic_layout = QHBoxLayout()
        mic_layout.addWidget(QLabel("Microfone:"))
        self.mic_combo = QComboBox()
        self.mic_combo.currentIndexChanged.connect(self.on_mic_selected)
        mic_layout.addWidget(self.mic_combo, 1)
        
        btn_refresh = QPushButton("🔄 Atualizar")
        btn_refresh.clicked.connect(self.refresh_mics)
        mic_layout.addWidget(btn_refresh)
        layout.addLayout(mic_layout)
        
        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("Nível de Entrada:"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(12)
        vol_layout.addWidget(self.progress_bar, 1)
        layout.addLayout(vol_layout)
        
        self.layout.addWidget(group)

    def _setup_visualizer_section(self):
        group = QGroupBox("Visualização de Frequência")
        layout = QVBoxLayout(group)
        
        self.visualizer = AudioVisualizerWidget()
        layout.addWidget(self.visualizer)
        
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("Estilo do Gráfico:"))
        self.combo_style = QComboBox()
        self.combo_style.addItems(["Clássico", "Onda Contínua", "Barras Digitais"])
        
        # Lê direto do ConfigManager (self.cfg)
        saved_style = self.cfg.data.get("visualizer", {}).get("style", "Clássico")
        self.combo_style.setCurrentText(saved_style)
        self.visualizer.set_visualizer_style(saved_style)
        
        self.combo_style.currentTextChanged.connect(self.on_visualizer_style_changed)
        style_layout.addWidget(self.combo_style, 1)
        layout.addLayout(style_layout)
        
        self.layout.addWidget(group)

    def _setup_processing_section(self):
        group = QGroupBox("Filtros e Processamento de Voz")
        layout = QVBoxLayout(group)
        
        # Lê direto do ConfigManager
        audio_cfg = self.cfg.data.get("audio", {})
        
        current_gain = audio_cfg.get("gain", 1.0)
        self.slider_gain = LabeledSlider("Ganho do Microfone (Volume de Entrada):", 0, 500, default_val=int(current_gain * 100), value_format="{v}%")
        self.slider_gain.slider.valueChanged.connect(lambda v: self.bus.request_audio_gain_change.emit(v / 100.0))
        layout.addWidget(self.slider_gain)
        
        self.slider_gate = LabeledSlider("Noise Gate (Corte de Ruído):", 0, 100, default_val=int(audio_cfg.get("noise_gate", 0.02) * 1000), value_format="{v}")
        self.slider_gate.slider.valueChanged.connect(lambda v: self.bus.request_audio_noise_gate_change.emit(v / 1000.0))
        layout.addWidget(self.slider_gate)
        
        self.slider_hold = LabeledSlider("Tempo de Retenção (Hold Time):", 0, 1000, default_val=audio_cfg.get("hold_time", 200), value_format="{v}ms")
        self.slider_hold.slider.valueChanged.connect(lambda v: self.bus.request_audio_hold_time_change.emit(v))
        layout.addWidget(self.slider_hold)
        
        self.chk_ducking = QCheckBox("Auto-Ducking (Abaixar música de fundo ao falar)")
        self.chk_ducking.setChecked(audio_cfg.get("auto_ducking", False))
        self.chk_ducking.toggled.connect(self.bus.request_audio_ducking_toggle.emit)
        layout.addWidget(self.chk_ducking)
        
        self.layout.addWidget(group)

    def _setup_thresholds_section(self):
        group = QGroupBox("Limites de Ativação por Volume (Expressão)")
        layout = QVBoxLayout(group)
        
        thresh_cfg = self.cfg.data.get("audio", {}).get("thresholds", {"low": 10, "mid": 35, "high": 65, "vhigh": 85})
        
        self.slider_low = LabeledSlider("Volume Baixo (Falar sutil):", 0, 100, default_val=thresh_cfg.get("low", 10), value_format="{v}%")
        self.slider_mid = LabeledSlider("Volume Médio (Conversa normal):", 0, 100, default_val=thresh_cfg.get("mid", 35), value_format="{v}%")
        self.slider_high = LabeledSlider("Volume Alto (Empolgado/Grito):", 0, 100, default_val=thresh_cfg.get("high", 65), value_format="{v}%")
        self.slider_vhigh = LabeledSlider("Volume Muito Alto (Susto/Pico):", 0, 100, default_val=thresh_cfg.get("vhigh", 85), value_format="{v}%")
        
        self.slider_low.slider.valueChanged.connect(lambda v: self.bus.request_audio_threshold_change.emit("low", v / 100.0))
        self.slider_mid.slider.valueChanged.connect(lambda v: self.bus.request_audio_threshold_change.emit("med", v / 100.0))
        self.slider_high.slider.valueChanged.connect(lambda v: self.bus.request_audio_threshold_change.emit("high", v / 100.0))
        self.slider_vhigh.slider.valueChanged.connect(lambda v: self.bus.request_audio_threshold_change.emit("vhigh", v / 100.0))
        
        layout.addWidget(self.slider_low)
        layout.addWidget(self.slider_mid)
        layout.addWidget(self.slider_high)
        layout.addWidget(self.slider_vhigh)
        
        self.layout.addWidget(group)

    def on_visualizer_style_changed(self, style_name):
        self.visualizer.set_visualizer_style(style_name)
        self.bus.request_visualizer_style_change.emit(style_name)

    def on_mic_selected(self, index):
        dev_idx = self.mic_combo.itemData(index)
        if dev_idx is not None:
            self.bus.request_audio_device_change.emit(dev_idx)

    def refresh_mics(self):
        """Pede para o EventBus atualizar a lista de microfones"""
        self.bus.request_refresh_devices.emit()

    def populate_mics(self, devices):
        """Recebe a lista filtrada do EventBus e popula a interface"""
        self.mic_combo.blockSignals(True)
        self.mic_combo.clear()

        for display_name, index in devices:
            self.mic_combo.addItem(display_name, index)

        saved_mic = self.cfg.data.get("audio", {}).get("device_index")
        if saved_mic is not None:
            idx = self.mic_combo.findData(saved_mic)
            if idx != -1:
                self.mic_combo.setCurrentIndex(idx)
            elif self.mic_combo.count() > 0:
                self.mic_combo.setCurrentIndex(0)
                
        self.mic_combo.blockSignals(False)