# ui/tabs/settings_tab.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, 
                             QLabel, QFrame, QGroupBox, QScrollArea)
from core.event_bus import EventBus
from ui.utils.form_builder import FormBuilder

class SettingsTab(QWidget):
    def __init__(self, config_manager):
        super().__init__()
        self.cfg = config_manager
        self.bus = EventBus.instance()
        
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
        self.btn_save.clicked.connect(self.save_all)
        self.main_layout.addWidget(self.btn_save)

        scroll.setWidget(container)
        layout_principal.addWidget(scroll)

    def _setup_system_section(self):
        group = QGroupBox("⚙️ SISTEMA E DESEMPENHO")
        layout = QVBoxLayout(group)
        builder = FormBuilder(layout)
        
        # 1. Otimização: Limite de FPS
        current_fps = self.cfg.data.get("system", {}).get("fps_limit", "60 FPS")
        self.fps_combo = builder.add_combobox(
            label_text="Limite de FPS (Desempenho):",
            items=["30 FPS", "60 FPS", "120 FPS"],
            current_text=current_fps,
            callback=self.update_fps
        )
        
        # 2. Integração OBS: Chroma Key
        # Usamos um dicionário para mapear os nomes amigáveis para os valores do JSON
        self.chroma_map = {
            "Transparente (Padrão)": "transparent",
            "Verde Chroma (#00FF00)": "green",
            "Magenta (#FF00FF)": "magenta"
        }
        current_chroma_val = self.cfg.data.get("render", {}).get("chroma_key", "transparent")
        current_chroma_text = next((k for k, v in self.chroma_map.items() if v == current_chroma_val), "Transparente (Padrão)")
        
        self.chroma_combo = builder.add_combobox(
            label_text="Fundo do Avatar (Chroma Key):",
            items=list(self.chroma_map.keys()),
            current_text=current_chroma_text,
            callback=self.update_chroma
        )
        
        # 3. Bandeja do Sistema (Tray)
        current_tray = self.cfg.data.get("system", {}).get("minimize_to_tray", False)
        self.tray_check = builder.add_checkbox(
            label_text="Minimizar para a Bandeja (System Tray) ao invés de fechar",
            is_checked=current_tray,
            callback=self.update_tray
        )
        
        self.main_layout.addWidget(group)

    def _setup_hotkeys_section(self):
        group = QGroupBox("⌨️ ATALHOS GLOBAIS")
        layout = QVBoxLayout(group)
        layout.addWidget(QLabel("<small>Estes atalhos funcionam mesmo com o app em segundo plano.</small>"))
        builder = FormBuilder(layout)

        hk_cfg = self.cfg.data.get("hotkeys", {})
        
        # 1. Travar Movimento
        self.lock_hk = builder.add_lineedit(
            label_text="Travar/Destravar Movimento:",
            current_text=hk_cfg.get("toggle_lock", ""),
            placeholder="ex: f10 ou shift+k",
            callback=lambda val: self.update_hk_config("toggle_lock", val)
        )

        # 2. Próximo Set de Animação
        self.next_hk = builder.add_lineedit(
            label_text="Próximo Set de Animação:",
            current_text=hk_cfg.get("next_set", ""),
            placeholder="ex: f10 ou shift+k",
            callback=lambda val: self.update_hk_config("next_set", val)
        )
        
        self.main_layout.addWidget(group)

    def _setup_render_section(self):
        group = QGroupBox("🖥️ COMPORTAMENTO DE JANELA")
        layout = QVBoxLayout(group)
        builder = FormBuilder(layout)

        current_on_top = self.cfg.data.get("render", {}).get("always_on_top", True)
        self.on_top = builder.add_checkbox(
            label_text="Janela do Avatar sempre no topo (Overlay)",
            is_checked=current_on_top,
            callback=self.update_on_top
        )

        self.main_layout.addWidget(group)

    # ==========================================
    # LÓGICA E CALLBACKS
    # ==========================================
    def update_fps(self, val):
        self.cfg.data.setdefault("system", {})["fps_limit"] = val

    def update_chroma(self, text):
        val = self.chroma_map.get(text, "transparent") # Pega o valor real baseado no texto
        self.cfg.data.setdefault("render", {})["chroma_key"] = val
        self.bus.request_chroma_key_update.emit() 

    def update_tray(self, state):
        self.cfg.data.setdefault("system", {})["minimize_to_tray"] = state

    def update_hk_config(self, key, value):
        self.cfg.data.setdefault("hotkeys", {})[key] = value.strip().lower()
        self.bus.request_hotkeys_reload.emit() 

    def update_on_top(self, state):
        self.bus.request_render_on_top_toggle.emit(state)
        self.cfg.data.setdefault("render", {})["always_on_top"] = state

    def save_all(self):
        try:
            self.cfg.save()
            print("✅ Configurações persistidas com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao salvar configurações: {e}")