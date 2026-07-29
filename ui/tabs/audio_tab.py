# ui/tabs/audio_tab.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QProgressBar, QGroupBox, QScrollArea, QFrame
from ui.widgets.labeled_slider import LabeledSlider
from ui.tabs.audio_tab_component.audio_visualizer import AudioVisualizerWidget
from core.event_bus import EventBus
from ui.utils.form_builder import FormBuilder

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

        # Configuração Guiada por Dados!
        self._setup_device_section()
        self._setup_visualizer_section()
        self._setup_processing_section()
        self._setup_thresholds_section()

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # Pede ao EventBus a lista inicial de microfones
        self.bus.request_refresh_devices.emit()

    def connect_bus_signals(self):
        """Inscreve a aba de áudio nos eventos de resposta do sistema (EventBus)"""
        # Verifica e conecta o sinal que traz a lista de microfones
        # Nota: Ajuste 'audio_devices_updated' se o nome do seu sinal no event_bus.py for diferente
        if hasattr(self.bus, 'audio_devices_updated'):
            self.bus.audio_devices_updated.connect(self.populate_mics)
        elif hasattr(self.bus, 'mic_list_updated'):
            self.bus.mic_list_updated.connect(self.populate_mics)

    # =================================================================
    # COMPONENTIZAÇÃO COM DATA-DRIVEN (A Grande Mudança)
    # =================================================================

    def _setup_device_section(self):
        group = QGroupBox("Dispositivo de Entrada")
        layout = QVBoxLayout(group)
        builder = FormBuilder(layout)

        # Como tem botões extra, podemos manter a criação manual aqui,
        # ou passar o botão extra pelo Schema. Para manter simples:
        self.btn_refresh = QPushButton("🔄 Atualizar")
        self.btn_refresh.clicked.connect(self.refresh_mics)

        self.mic_combo = builder.add_combobox(
            label_text="Microfone:",
            items=[],
            current_text="",
            callback=self.on_mic_selected,
            extra_widget=self.btn_refresh
        )

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(12)
        builder._add_row("Nível de Entrada:", self.progress_bar)

        self.layout.addWidget(group)

    def _setup_visualizer_section(self):
        group = QGroupBox("Visualização de Frequência")
        layout = QVBoxLayout(group)
        builder = FormBuilder(layout)

        self.visualizer = AudioVisualizerWidget()
        builder.add_custom_widget(self.visualizer)

        schema = [{
            "type": "combobox",
            "key": "style", # Chave no JSON
            "title": "Estilo do Gráfico:",
            "options": ["Clássico", "Onda Contínua", "Barras Digitais", "Neon Simétrico", "Pontos de Energia"],
            "default": "Clássico"
        }]
        
        vis_config = self.cfg.data.get("visualizer", {})
        builder.build_from_schema(schema, vis_config, self._on_visualizer_field_changed)

        # Configura o estilo inicial
        self.visualizer.set_visualizer_style(vis_config.get("style", "Clássico"))
        
        self.layout.addWidget(group)

    def _setup_processing_section(self):
        group = QGroupBox("Filtros e Processamento de Voz")
        layout = QVBoxLayout(group)
        builder = FormBuilder(layout)

        # O Schema define a estrutura de dados, o builder desenha!
        schema = [
            {
                "type": "custom_slider", "key": "gain",
                "title": "Ganho do Microfone (Volume de Entrada):",
                "min_val": 0, "max_val": 5, "default": 1.0, "step": 0.1, "unit": "x",
                "ticks": [("0x", 0), ("1x", 1), ("5x", 5)], "decimals": 1
            },
            {
                "type": "custom_slider", "key": "noise_gate",
                "title": "Noise Gate (Corte de Ruído):",
                "min_val": 0, "max_val": 1, "default": 0.02, "step": 0.01, "unit": "",
                "ticks": [("0", 0), ("0.5", 0.5), ("1", 1)], "decimals": 2
            },
            {
                "type": "custom_slider", "key": "hold_time",
                "title": "Tempo de Retenção (Hold Time):",
                "min_val": 0, "max_val": 1000, "default": 200, "step": 10, "unit": " ms",
                "decimals": 0
            },
            {
                "type": "switch", "key": "auto_ducking",
                "title": "Auto-Ducking (Abaixar música de fundo ao falar)",
                "default": False
            }
        ]

        audio_config = self.cfg.data.get("audio", {})
        builder.build_from_schema(schema, audio_config, self._on_audio_field_changed)
        
        self.layout.addWidget(group)

    def _setup_thresholds_section(self):
        group = QGroupBox("Limites de Ativação por Volume (Expressão)")
        layout = QVBoxLayout(group)
        builder = FormBuilder(layout)

        schema = [
            {"type": "custom_slider", "key": "low", "title": "Volume Baixo (Falar sutil):", "min_val": 0, "max_val": 1, "default": 0.10, "step": 0.01, "unit": "", "decimals": 2},
            {"type": "custom_slider", "key": "med", "title": "Volume Médio (Conversa normal):", "min_val": 0, "max_val": 1, "default": 0.35, "step": 0.01, "unit": "", "decimals": 2},
            {"type": "custom_slider", "key": "high", "title": "Volume Alto (Empolgado/Grito):", "min_val": 0, "max_val": 1, "default": 0.65, "step": 0.01, "unit": "", "decimals": 2},
            {"type": "custom_slider", "key": "vhigh", "title": "Volume Muito Alto (Susto/Pico):", "min_val": 0, "max_val": 1, "default": 0.85, "step": 0.01, "unit": "", "decimals": 2},
        ]

        thresh_config = self.cfg.data.get("audio", {}).get("thresholds", {})
        builder.build_from_schema(schema, thresh_config, self._on_threshold_changed)
        
        self.layout.addWidget(group)

    # =================================================================
    # EVENTOS DE CALLBACK DESPACHANTES (Roteadores Universais)
    # =================================================================

    def _on_visualizer_field_changed(self, key, value):
        if key == "style":
            self.visualizer.set_visualizer_style(value)
            self.bus.request_visualizer_style_change.emit(value)

    def _on_audio_field_changed(self, key, value):
        """Um único método roteia todas as alterações da aba de áudio."""
        if key == "gain":
            self.bus.request_audio_gain_change.emit(value)
        elif key == "noise_gate":
            self.bus.request_audio_noise_gate_change.emit(value)
        elif key == "hold_time":
            self.bus.request_audio_hold_time_change.emit(int(value))
        elif key == "auto_ducking":
            self.bus.request_audio_ducking_toggle.emit(value)

    def _on_threshold_changed(self, key, value):
        # Os Sliders retornam o float correto devido ao decimals=2, não precisa dividir por 100
        self.bus.request_audio_threshold_change.emit(key, value)

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