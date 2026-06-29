# ui/tabs/audio_tab.py
#import sounddevice as sd
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QProgressBar, QCheckBox, QPushButton, 
                             QGroupBox, QScrollArea, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from ui.styles.theme import Theme
from ui.widgets.labeled_slider import LabeledSlider

# CORRIGIDO: Import dinâmico apontando para o seu novo caminho customizado
from ui.tabs.audio_tab_component.audio_visualizer import AudioVisualizerWidget

class AudioTab(QWidget):
    def __init__(self, config_manager, audio_manager):
        super().__init__()
        self.profile = config_manager
        self.audio = audio_manager
        self.init_ui()
        
    def init_ui(self):
        # Usamos uma ScrollArea para garantir scannabilidade se a janela for pequena
        main_layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        self.layout = QVBoxLayout(scroll_content)
        
        # 1. RESTAURADO: Seção de seleção do microfone
        self._setup_device_section()
        
        # 2. Seção do Visualizador Modularizado
        self._setup_visualizer_section()
        
        # 3. RESTAURADO: Seção de processamento (Filtros, Ganho, Ducking)
        self._setup_processing_section()
        
        # 4. Seção de limites para as expressões da boca
        self._setup_thresholds_section()
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        # Popula os microfones assim que a interface carrega
        self.refresh_mics()

        # Conecte o motor de áudio aos componentes visuais da aba
        # ADICIONADO SEGURO: Verifica se progress_bar realmente existe antes de conectar
        if hasattr(self, 'progress_bar'):
            # Multiplica o float (0.0 a 1.0) por 100 e converte em int para a barra preencher perfeitamente
            self.audio.volumeChanged.connect(lambda vol: self.progress_bar.setValue(int(vol * 100)))

        if hasattr(self, 'visualizer'):
            # Conecta o sinal que envia volume e bandas do equalizador diretamente ao widget de ondas
            self.audio.audioProcessed.connect(lambda vol, bands: self.visualizer.update_bands(bands))

    def _setup_device_section(self):
        """Monta o combo box de seleção de hardware de áudio."""
        group = QGroupBox("Dispositivo de Entrada")
        layout = QVBoxLayout(group) # Mudado para vertical para abrigar a barra embaixo
        
        # Layout para a linha do microfone
        mic_layout = QHBoxLayout()
        mic_layout.addWidget(QLabel("Microfone:"))
        self.mic_combo = QComboBox()
        self.mic_combo.currentIndexChanged.connect(self.on_mic_selected)
        mic_layout.addWidget(self.mic_combo, 1)
        
        btn_refresh = QPushButton("🔄 Atualizar")
        btn_refresh.clicked.connect(self.refresh_mics)
        mic_layout.addWidget(btn_refresh)
        layout.addLayout(mic_layout)
        
        # --- ADICIONADO: Criação da barra de progresso (Volume) ---
        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("Nível de Entrada:"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False) # Deixa o visual mais limpo
        self.progress_bar.setFixedHeight(12)   # Altura discreta
        vol_layout.addWidget(self.progress_bar, 1)
        layout.addLayout(vol_layout)
        # ----------------------------------------------------------
        
        self.layout.addWidget(group)

    def _setup_visualizer_section(self):
        """Monta a área do gráfico de frequências."""
        group = QGroupBox("Visualização de Frequência")
        layout = QVBoxLayout(group)
        
        self.visualizer = AudioVisualizerWidget()
        layout.addWidget(self.visualizer)
        
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("Estilo do Gráfico:"))
        self.combo_style = QComboBox()
        self.combo_style.addItems(["Clássico", "Onda Contínua", "Barras Digitais"])
        
        saved_style = self.profile.data.get("visualizer", {}).get("style", "Clássico")
        self.combo_style.setCurrentText(saved_style)
        self.visualizer.set_visualizer_style(saved_style)
        
        self.combo_style.currentTextChanged.connect(self.on_visualizer_style_changed)
        style_layout.addWidget(self.combo_style, 1)
        layout.addLayout(style_layout)
        
        self.layout.addWidget(group)

    def _setup_processing_section(self):
        """Monta os filtros de corte de ruído e ganho de volume."""
        group = QGroupBox("Filtros e Processamento de Voz")
        layout = QVBoxLayout(group)
        
        audio_cfg = self.profile.data.get("audio", {})
        
        # --- ADICIONADO: Slider de Ganho de Áudio ---
        # Multiplicador de 0.0 a 5.0 (exibido como 0% a 500%)
        current_gain = audio_cfg.get("gain", 1.0)
        self.slider_gain = LabeledSlider(
            "Ganho do Microfone (Volume de Entrada):", 
            0, 500, 
            default_val=int(current_gain * 100), 
            value_format="{v}%"
        )
        self.slider_gain.slider.valueChanged.connect(lambda v: self.audio.set_gain(v / 100.0))
        layout.addWidget(self.slider_gain)
        # --------------------------------------------
        
        # Noise Gate
        self.slider_gate = LabeledSlider("Noise Gate (Corte de Ruído):", 0, 100, default_val=int(audio_cfg.get("noise_gate", 0.02) * 1000), value_format="{v}")
        self.slider_gate.slider.valueChanged.connect(lambda v: self.audio.set_noise_gate(v / 1000.0))
        layout.addWidget(self.slider_gate)
        
        # Hold Time
        self.slider_hold = LabeledSlider("Tempo de Retenção (Hold Time):", 0, 1000, default_val=audio_cfg.get("hold_time", 200), value_format="{v}ms")
        self.slider_hold.slider.valueChanged.connect(lambda v: self.audio.set_hold_time(v))
        layout.addWidget(self.slider_hold)
        
        # Auto Ducking Checkbox
        self.chk_ducking = QCheckBox("Auto-Ducking (Abaixar música de fundo ao falar)")
        self.chk_ducking.setChecked(audio_cfg.get("auto_ducking", False))
        self.chk_ducking.toggled.connect(self.audio.set_auto_ducking)
        layout.addWidget(self.chk_ducking)
        
        self.layout.addWidget(group)

    def _setup_thresholds_section(self):
        """Controles para calibrar a sensibilidade da boca do avatar."""
        group = QGroupBox("Limites de Ativação por Volume (Expressão)")
        layout = QVBoxLayout(group)
        
        thresh_cfg = self.profile.data.get("audio", {}).get("thresholds", {"low": 10, "mid": 35, "high": 65, "vhigh": 85})
        
        self.slider_low = LabeledSlider("Volume Baixo (Falar sutil):", 0, 100, default_val=thresh_cfg.get("low", 10), value_format="{v}%")
        self.slider_mid = LabeledSlider("Volume Médio (Conversa normal):", 0, 100, default_val=thresh_cfg.get("mid", 35), value_format="{v}%")
        self.slider_high = LabeledSlider("Volume Alto (Empolgado/Grito):", 0, 100, default_val=thresh_cfg.get("high", 65), value_format="{v}%")
        self.slider_vhigh = LabeledSlider("Volume Muito Alto (Susto/Pico):", 0, 100, default_val=thresh_cfg.get("vhigh", 85), value_format="{v}%")
        
        self.slider_low.slider.valueChanged.connect(lambda v: self.audio.set_threshold("low", v / 100.0))
        self.slider_mid.slider.valueChanged.connect(lambda v: self.audio.set_threshold("med", v / 100.0))
        self.slider_high.slider.valueChanged.connect(lambda v: self.audio.set_threshold("high", v/ 100.0))
        self.slider_vhigh.slider.valueChanged.connect(lambda v: self.audio.set_threshold("vhigh", v/ 100.0))
        
        layout.addWidget(self.slider_low)
        layout.addWidget(self.slider_mid)
        layout.addWidget(self.slider_high)
        layout.addWidget(self.slider_vhigh)
        
        self.layout.addWidget(group)

    def on_visualizer_style_changed(self, style_name):
        self.visualizer.set_visualizer_style(style_name)
        self.audio.set_visualizer_style(style_name)

    def on_mic_selected(self, index):
        dev_idx = self.mic_combo.itemData(index)
        if dev_idx is not None:
            self.audio.set_device_index(dev_idx)

    def refresh_mics(self):
        """Apenas atualiza o componente visual com os dados fornecidos pelo Core."""
        self.mic_combo.blockSignals(True)
        self.mic_combo.clear()

        # 1. Solicita a lista de dispositivos já limpa e filtrada pelo Core
        devices = self.audio.get_filtered_input_devices()
        
        # 2. Alimenta o elemento visual
        for display_name, index in devices:
            self.mic_combo.addItem(display_name, index)

        # 3. Define a seleção atual baseando-se no estado real do Core (não lendo o JSON direto)
        saved_mic = self.audio.device_index
        if saved_mic is not None:
            idx = self.mic_combo.findData(saved_mic)
            if idx != -1:
                self.mic_combo.setCurrentIndex(idx)
            elif self.mic_combo.count() > 0:
                self.mic_combo.setCurrentIndex(0)
                
        self.mic_combo.blockSignals(False)