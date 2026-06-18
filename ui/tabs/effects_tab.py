from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QScrollArea, 
                             QGridLayout, QMessageBox, QFrame, QGroupBox, QPushButton)
from PySide6.QtCore import Qt
from ui.styles.theme import Theme
from .effects_tab_component.effect_creator import EffectCreator
from .effects_tab_component.effect_card import EffectCard

class EffectsTab(QWidget):
    def __init__(self, config_manager, overlay_manager, hotkey_manager):
        super().__init__()
        self.cfg = config_manager
        self.overlay = overlay_manager 
        self.hotkeys = hotkey_manager
        self.profile = config_manager.data
        
        if "custom_effects" not in self.profile:
            self.profile["custom_effects"] = {}

        self.setStyleSheet(Theme.MAIN_TAB_STYLE + Theme.GROUP_BOX)
        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(15, 15, 15, 15)
        layout_principal.setSpacing(15)

        # --- BOTÃO PRINCIPAL (NOVA JANELA) ---
        self.btn_new = QPushButton("➕ CRIAR NOVO EFEITO")
        self.btn_new.setStyleSheet("""
            QPushButton {
                background-color: #238636; color: white; font-weight: bold; 
                font-size: 14px; padding: 15px; border-radius: 6px; border: none;
            }
            QPushButton:hover { background-color: #2ea043; }
        """)
        self.btn_new.clicked.connect(self.open_creator)
        layout_principal.addWidget(self.btn_new)
        
        # --- ÁREA DE SCROLL DA BIBLIOTECA ---
        self.main_scroll = QScrollArea()
        self.main_scroll.setWidgetResizable(True)
        self.main_scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        main_lay = QVBoxLayout(container)
        main_lay.setContentsMargins(0, 0, 0, 0)

        self.library_group = QGroupBox("📚 MINHA BIBLIOTECA")
        library_layout = QVBoxLayout(self.library_group)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid #333; background: {Theme.BG_DARK}; border-radius: 5px; }}
            QTabBar::tab {{ background: {Theme.BG_CARD}; color: {Theme.TEXT_MUTED}; padding: 10px 20px; border-top-left-radius: 4px; border-top-right-radius: 4px; }}
            QTabBar::tab:selected {{ background: {Theme.BG_DARK}; color: {Theme.ACCENT}; border-bottom: 2px solid {Theme.ACCENT}; }}
        """)

        self.grids = { "visual": QGridLayout(), "audio": QGridLayout(), "combo": QGridLayout() }
        sections = [("visual", "🖼️ VISUAIS"), ("audio", "🎵 ÁUDIO"), ("combo", "🎭 COMBOS")]
        
        for key, label in sections:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setMinimumHeight(400)
            scroll.setFrameShape(QFrame.NoFrame)
            
            content = QWidget()
            content.setStyleSheet("background: transparent;")
            self.grids[key].setAlignment(Qt.AlignTop | Qt.AlignLeft)
            self.grids[key].setSpacing(15)
            content.setLayout(self.grids[key])
            
            scroll.setWidget(content)
            self.tabs.addTab(scroll, label)
            
        library_layout.addWidget(self.tabs)
        main_lay.addWidget(self.library_group)
        
        self.main_scroll.setWidget(container)
        layout_principal.addWidget(self.main_scroll)
        
        # Conecta o sinal global da Overlay para tratar o salvamento de coordenadas
        self.overlay.positionUpdated.connect(self._handle_position_update)
        
        self.refresh_list()

    def open_creator(self, eid=None, data=None):
        """Instancia e abre o QDialog (Janela Modal) para criar/editar efeitos."""
        dialog = EffectCreator(self.hotkeys, self)
        
        # Se for edição, carrega os dados no modal
        if eid and data:
            dialog.load_effect(eid, data)
            
        dialog.effect_created.connect(self.add_new_effect)
        dialog.test_requested.connect(self.preview_effect)
        dialog.exec() # Pausa a interface de trás até a janela fechar

    def _handle_position_update(self, eid, x, y):
        # Ignoramos "preview_temp" já que ele só ocorre enquanto o modal de teste está aberto
        if eid in self.profile["custom_effects"]:
            self.profile["custom_effects"][eid]["x"] = x
            self.profile["custom_effects"][eid]["y"] = y
            self.cfg.save()

    def preview_effect(self, data):
        self.overlay.play_effect(
            effect_id="preview_temp", 
            visual_path=data.get('visual', ''),
            audio_path=data.get('audio', ''),
            duration=data.get('duration', 4000),
            scale=data.get('scale', 1.0),
            opacity=data.get('opacity', 1.0),
            x=data.get('x', 500), 
            y=data.get('y', 300),
            audio_start=data.get('audio_start', 0.0),
            audio_end=data.get('audio_end', 0.0)
        )

    def add_new_effect(self, data):
        eid = data.pop("id")
        data["type"] = self._determine_effect_type(data)
        
        if eid in self.profile["custom_effects"]:
            self.hotkeys.remove_custom_hotkey(eid)

        self.profile["custom_effects"][eid] = data
        
        if data.get("hotkey"):
            self.hotkeys.register_custom_effect(eid, data["hotkey"], data)
        
        self.cfg.save() 
        self.refresh_list()
        
        tab_idx = {"visual": 0, "audio": 1, "combo": 2}.get(data["type"], 0)
        self.tabs.setCurrentIndex(tab_idx)

    def _determine_effect_type(self, data):
        has_v = bool(data.get("visual"))
        has_a = bool(data.get("audio"))
        if has_v and has_a: return "combo"
        return "audio" if has_a else "visual"

    def refresh_list(self):
        for g in self.grids.values():
            while g.count():
                child = g.takeAt(0)
                if child.widget(): child.widget().deleteLater()

        counts = {"visual": 0, "audio": 0, "combo": 0}
        sorted_effects = sorted(self.profile["custom_effects"].items(), key=lambda x: x[1]['name'].lower())

        for eid, d in sorted_effects:
            t = d.get("type") or self._determine_effect_type(d)
            if t not in self.grids: t = "visual"
            
            card = EffectCard(eid, d, self.overlay)
            card.clicked_delete.connect(self.remove_effect)
            
            # Ao invés de mandar para o painel antigo, agora chama o modal `open_creator`
            card.clicked_edit.connect(lambda e=eid, data=d: self.open_creator(e, data))
            
            # Acomoda até 4 cards na mesma linha graças à aba maior
            row, col = divmod(counts[t], 4) 
            self.grids[t].addWidget(card, row, col)
            counts[t] += 1

    def remove_effect(self, eid):
        if QMessageBox.question(self, "Confirmar", "Deseja excluir este efeito?") == QMessageBox.Yes:
            self.hotkeys.remove_custom_hotkey(eid)
            if eid in self.profile["custom_effects"]:
                del self.profile["custom_effects"][eid]
                self.cfg.save()
                self.refresh_list()