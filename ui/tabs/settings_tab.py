# ui/tabs/settings_tab.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QFrame, QCheckBox, QGroupBox, 
                             QScrollArea, QComboBox)
from PySide6.QtCore import Qt
from ui.styles.theme import Theme
from core.event_bus import EventBus

class SettingsTab(QWidget):
    def __init__(self, config_manager):
        super().__init__()
        self.cfg = config_manager
        self.bus = EventBus.instance()
        self.setStyleSheet(Theme.MAIN_TAB_STYLE + Theme.GROUP_BOX + Theme.BUTTON_BASE)
        
        layout_principal = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setSpacing(15)

        self._setup_system_section()
        self._setup_hotkeys_section()
        self._setup_render_section()
        
        self.main_layout.addStretch()
        
        # Botão Salvar Geral
        self.btn_save = QPushButton("💾 SALVAR TODAS AS CONFIGURAÇÕES")
        self.btn_save.setStyleSheet(Theme.BUTTON_PRIMARY + "height: 45px; font-size: 14px;")
        self.btn_save.clicked.connect(self.save_all)
        self.main_layout.addWidget(self.btn_save)

        scroll.setWidget(container)
        layout_principal.addWidget(scroll)

    def _setup_system_section(self):
        group = QGroupBox("⚙️ SISTEMA E DESEMPENHO")
        layout = QVBoxLayout(group)
        
        # Otimização: Limite de FPS
        h_fps = QHBoxLayout()
        h_fps.addWidget(QLabel("Limite de FPS (Desempenho):"))
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["30 FPS", "60 FPS", "120 FPS"])
        
        current_fps = self.cfg.data.get("system", {}).get("fps_limit", "60 FPS")
        self.fps_combo.setCurrentText(current_fps)
        self.fps_combo.currentTextChanged.connect(self.update_fps)
        
        h_fps.addWidget(self.fps_combo)
        layout.addLayout(h_fps)
        
        # Integração OBS: Chroma Key
        h_chroma = QHBoxLayout()
        h_chroma.addWidget(QLabel("Fundo do Avatar (Chroma Key):"))
        self.chroma_combo = QComboBox()
        self.chroma_combo.addItem("Transparente (Padrão)", "transparent")
        self.chroma_combo.addItem("Verde Chroma (#00FF00)", "green")
        self.chroma_combo.addItem("Magenta (#FF00FF)", "magenta")
        
        current_chroma = self.cfg.data.get("render", {}).get("chroma_key", "transparent")
        idx = self.chroma_combo.findData(current_chroma)
        if idx != -1: self.chroma_combo.setCurrentIndex(idx)
        self.chroma_combo.currentIndexChanged.connect(self.update_chroma)
        
        h_chroma.addWidget(self.chroma_combo)
        layout.addLayout(h_chroma)
        
        # Bandeja do Sistema (Tray)
        self.tray_check = QCheckBox("Minimizar para a Bandeja (System Tray) ao invés de fechar")
        current_tray = self.cfg.data.get("system", {}).get("minimize_to_tray", False)
        self.tray_check.setChecked(current_tray)
        self.tray_check.toggled.connect(self.update_tray)
        layout.addWidget(self.tray_check)
        
        self.main_layout.addWidget(group)

    def _setup_hotkeys_section(self):
        group = QGroupBox("⌨️ ATALHOS GLOBAIS")
        layout = QVBoxLayout(group)
        layout.addWidget(QLabel("<small>Estes atalhos funcionam mesmo com o app em segundo plano.</small>"))

        self.lock_hk = self._create_hk_row("Travar/Destravar Movimento:", "toggle_lock")
        self.next_hk = self._create_hk_row("Próximo Set de Animação:", "next_set")

        layout.addLayout(self.lock_hk)
        layout.addLayout(self.next_hk)
        
        self.main_layout.addWidget(group)

    def _setup_render_section(self):
        group = QGroupBox("🖥️ COMPORTAMENTO DE JANELA")
        layout = QVBoxLayout(group)

        self.on_top = QCheckBox("Janela do Avatar sempre no topo (Overlay)")
        current_on_top = self.cfg.data.get("render", {}).get("always_on_top", True)
        self.on_top.setChecked(current_on_top)
        self.on_top.toggled.connect(self.update_on_top)
        layout.addWidget(self.on_top)

        self.main_layout.addWidget(group)

    def _create_hk_row(self, label_text, config_key):
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        row.addWidget(lbl)
        
        edit = QLineEdit()
        edit.setFixedWidth(120)
        edit.setAlignment(Qt.AlignCenter)
        
        current_hk = self.cfg.data.get("hotkeys", {}).get(config_key, "")
        edit.setText(current_hk)
        edit.setPlaceholderText("ex: f10 ou shift+k")
        
        edit.textChanged.connect(lambda val: self.update_hk_config(config_key, val))
        
        row.addWidget(edit)
        return row

    def update_fps(self, val):
        if "system" not in self.cfg.data: self.cfg.data["system"] = {}
        self.cfg.data["system"]["fps_limit"] = val

    def update_chroma(self, idx):
        val = self.chroma_combo.itemData(idx)
        if "render" not in self.cfg.data: self.cfg.data["render"] = {}
        self.cfg.data["render"]["chroma_key"] = val
        self.bus.request_chroma_key_update.emit() # Desacoplado via EventBus!

    def update_tray(self, state):
        if "system" not in self.cfg.data: self.cfg.data["system"] = {}
        self.cfg.data["system"]["minimize_to_tray"] = state

    def update_hk_config(self, key, value):
        if "hotkeys" not in self.cfg.data:
            self.cfg.data["hotkeys"] = {}
        self.cfg.data["hotkeys"][key] = value.strip().lower()
        self.bus.request_hotkeys_reload.emit() 

    def update_on_top(self, state):
        self.bus.request_render_on_top_toggle.emit(state)
        if "render" not in self.cfg.data:
            self.cfg.data["render"] = {}
        self.cfg.data["render"]["always_on_top"] = state

    def save_all(self):
        try:
            self.cfg.save()
            print("✅ Configurações persistidas com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao salvar configurações: {e}")