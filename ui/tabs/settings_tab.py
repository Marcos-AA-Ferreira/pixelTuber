from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QGroupBox, QScrollArea

from core.event_bus import EventBus

from ui.utils.form_builder import FormBuilder
from ui.schemas.settings_schema import SYSTEM_SCHEMA, HOTKEYS_SCHEMA, WINDOW_SCHEMA

class SettingsTab(QWidget):
    def __init__(self, config_manager):
        super().__init__()
        self.cfg = config_manager
        self.bus = EventBus.instance()
        
        # Mapeamento do Chroma Key
        self.chroma_map = {
            "Transparente (Padrão)": "transparent",
            "Verde Chroma (#00FF00)": "green",
            "Magenta (#FF00FF)": "magenta"
        }
        
        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setSpacing(15)

        self._setup_sections()

        self.main_layout.addStretch()

        self.btn_save = QPushButton("💾 SALVAR TODAS AS CONFIGURAÇÕES")
        self.btn_save.clicked.connect(self.save_all)
        self.main_layout.addWidget(self.btn_save)

        scroll.setWidget(container)
        layout_principal.addWidget(scroll)

    # =================================================================
    # LÓGICA DE DADOS (GETTERS E SETTERS CENTRAIS)
    # =================================================================

    def _get_setting_value(self, key: str):
        """Lê o valor atual do JSON usando notação de ponto (ex: system.fps_limit)"""
        domain, subkey = key.split('.')
        
        # Tradução reversa do Chroma Key ('transparent' -> 'Transparente (Padrão)')
        if key == "render.chroma_key":
            val = self.cfg.data.get(domain, {}).get(subkey, "transparent")
            return next((k for k, v in self.chroma_map.items() if v == val), "Transparente (Padrão)")
        
        return self.cfg.data.get(domain, {}).get(subkey)

    def _on_setting_changed(self, key: str, value):
        """Roteador inteligente: recebe qualquer mudança da UI e aplica no lugar certo"""
        domain, subkey = key.split('.')
        
        # 1. Tratamento específico para o Chroma Key
        if key == "render.chroma_key":
            value = self.chroma_map.get(value, "transparent")
            self.cfg.data.setdefault(domain, {})[subkey] = value
            self.bus.request_chroma_key_update.emit()
            return

        # 2. Tratamento específico para os atalhos de teclado
        if domain == "hotkeys":
            value = value.strip().lower()
            self.cfg.data.setdefault(domain, {})[subkey] = value
            self.bus.request_hotkeys_reload.emit()
            return

        # 3. Tratamento padrão (salva o dado diretamente)
        self.cfg.data.setdefault(domain, {})[subkey] = value
        
        # Eventos paralelos
        if key == "render.always_on_top":
            self.bus.request_render_on_top_toggle.emit(value)

    # =================================================================
    # DATA-DRIVEN UI (SEM REPETIÇÃO)
    # =================================================================

    def _setup_sections(self):
        # --- 1. SISTEMA E DESEMPENHO ---
        sys_group = QGroupBox("⚙️ SISTEMA E DESEMPENHO")
        sys_builder = FormBuilder(QVBoxLayout(sys_group))
        sys_builder.build_from_schema(SYSTEM_SCHEMA, self._get_setting_value, self._on_setting_changed)
        self.main_layout.addWidget(sys_group)

        # --- 2. ATALHOS GLOBAIS ---
        hk_group = QGroupBox("⌨️ ATALHOS GLOBAIS")
        hk_lay = QVBoxLayout(hk_group)
        hk_lay.addWidget(QLabel("<small>Estes atalhos funcionam mesmo com o app em segundo plano.</small>"))
        FormBuilder(hk_lay).build_from_schema(HOTKEYS_SCHEMA, self._get_setting_value, self._on_setting_changed)
        self.main_layout.addWidget(hk_group)

        # --- 3. COMPORTAMENTO DE JANELA ---
        win_group = QGroupBox("🖥️ COMPORTAMENTO DE JANELA")
        FormBuilder(QVBoxLayout(win_group)).build_from_schema(WINDOW_SCHEMA, self._get_setting_value, self._on_setting_changed)
        self.main_layout.addWidget(win_group)

    def save_all(self):
        try:
            self.cfg.save()
            print("✅ Configurações persistidas com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao salvar configurações: {e}")