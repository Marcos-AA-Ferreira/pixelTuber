from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QFrame, QCheckBox, QGroupBox, 
                             QScrollArea)
from PySide6.QtCore import Qt
from ui.styles.theme import Theme

class SettingsTab(QWidget):
    def __init__(self, config_manager, render, hotkeys):
        super().__init__()
        self.cfg = config_manager
        self.render = render
        self.hotkeys = hotkeys

        # Corrigido: Removido Theme.LINE_EDIT que não existe na sua classe Theme
        self.setStyleSheet(Theme.MAIN_TAB_STYLE + Theme.GROUP_BOX + 
                           Theme.BUTTON_BASE)

        layout_principal = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setSpacing(15)

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

    def _setup_hotkeys_section(self):
        group = QGroupBox("⌨️ ATALHOS GLOBAIS")
        layout = QVBoxLayout(group)
        layout.addWidget(QLabel("<small>Estes atalhos funcionam mesmo com o app em segundo plano.</small>"))

        self.lock_hk = self._create_hk_row("Travar/Destravar Movimento:", "toggle_lock")
        self.next_hk = self._create_hk_row("Próximo Set de Animação:", "next_set")
        self.close_hk = self._create_hk_row("Fechar Aplicativo:", "close_app")

        layout.addLayout(self.lock_hk)
        layout.addLayout(self.next_hk)
        layout.addLayout(self.close_hk)
        
        self.main_layout.addWidget(group)

    def _setup_render_section(self):
        group = QGroupBox("🖥️ VISUAL E RENDERIZAÇÃO")
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

    def update_hk_config(self, key, value):
        if "hotkeys" not in self.cfg.data:
            self.cfg.data["hotkeys"] = {}
        
        self.cfg.data["hotkeys"][key] = value.strip().lower()
        self.hotkeys.setup_defaults()

    def update_on_top(self, state):
        flags = self.render.windowFlags()
        if state:
            self.render.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
        else:
            self.render.setWindowFlags(flags & ~Qt.WindowStaysOnTopHint)
        
        self.render.show()
        
        if "render" not in self.cfg.data: self.cfg.data["render"] = {}
        self.cfg.data["render"]["always_on_top"] = state

    def save_all(self):
        try:
            self.cfg.save()
            print("✅ Configurações persistidas com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao salvar configurações: {e}")