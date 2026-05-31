from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QScrollArea, 
                             QGridLayout, QMessageBox, QFrame, QGroupBox, QLabel)
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

        # Aplica o estilo visual do tema
        self.setStyleSheet(Theme.MAIN_TAB_STYLE + Theme.GROUP_BOX)
        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        
        # --- ÁREA DE SCROLL PRINCIPAL ---
        self.main_scroll = QScrollArea()
        self.main_scroll.setWidgetResizable(True)
        self.main_scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        main_lay = QVBoxLayout(container)
        main_lay.setContentsMargins(10, 10, 10, 10)
        main_lay.setSpacing(20)

        # --- SEÇÃO DO CRIADOR/EDITOR ---
        self.creator_group = QGroupBox("✨ GESTÃO DE EFEITO")
        creator_layout = QVBoxLayout(self.creator_group)
        
        self.creator = EffectCreator(self.hotkeys)
        self.creator.effect_created.connect(self.add_new_effect)
        self.creator.test_requested.connect(self.preview_effect)
        
        # SISTEMA DE POSIÇÃO DINÂMICO
        # Conecta o sinal global da Overlay para tratar o salvamento de coordenadas
        self.overlay.positionUpdated.connect(self._handle_position_update)
        
        creator_layout.addWidget(self.creator)
        main_lay.addWidget(self.creator_group)

        # --- BIBLIOTECA DE EFEITOS SALVOS ---
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
        
        self.refresh_list()

    def _handle_position_update(self, eid, x, y):
        """
        Lógica inteligente de posição:
        1. Se for preview, apenas atualiza os campos numéricos no criador.
        2. Se for um efeito salvo, grava a nova posição permanentemente no config.json.
        """
        if eid == "preview":
            if hasattr(self.creator, "visual_module"):
                self.creator.visual_module.update_position_fields(x, y)
        
        elif eid in self.profile["custom_effects"]:
            # Atualiza os dados na memória
            self.profile["custom_effects"][eid]["x"] = x
            self.profile["custom_effects"][eid]["y"] = y
            # Salva no arquivo para que na próxima execução ele apareça aqui
            self.cfg.save()

    def preview_effect(self, data):
        """Executa o teste do efeito com as configurações atuais do criador."""
        self.overlay.play_effect(
            effect_id="preview", # Identificador para o preview
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
        """Adiciona ou atualiza um efeito e registra o atalho de teclado."""
        eid = data.pop("id")
        data["type"] = self._determine_effect_type(data)
        
        # Limpa o atalho antigo se estiver editando para evitar conflitos
        if eid in self.profile["custom_effects"]:
            self.hotkeys.remove_custom_hotkey(eid)

        # Salva os novos dados
        self.profile["custom_effects"][eid] = data
        
        # Registra o novo atalho no sistema global
        if data.get("hotkey"):
            self.hotkeys.register_custom_effect(eid, data["hotkey"], data)
        
        self.cfg.save() 
        self.refresh_list()
        
        # Foca na aba correspondente ao tipo salvo
        tab_idx = {"visual": 0, "audio": 1, "combo": 2}.get(data["type"], 0)
        self.tabs.setCurrentIndex(tab_idx)

    def _determine_effect_type(self, data):
        """Classifica o efeito com base nos arquivos anexados."""
        has_v = bool(data.get("visual"))
        has_a = bool(data.get("audio"))
        if has_v and has_a: return "combo"
        return "audio" if has_a else "visual"

    def refresh_list(self):
        """Limpa e reconstrói a grade de cards da biblioteca."""
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
            card.clicked_edit.connect(lambda e=eid, data=d: self.edit_existing_effect(e, data))
            
            row, col = divmod(counts[t], 3)
            self.grids[t].addWidget(card, row, col)
            counts[t] += 1

    def edit_existing_effect(self, eid, data):
        """Carrega os dados de um efeito salvo de volta para o editor superior."""
        if hasattr(self.creator, "load_effect"):
            # O EffectCreator deve lidar com a exibição do caminho do áudio existente
            self.creator.load_effect(eid, data)
            # Rola a tela para cima para facilitar a edição
            self.main_scroll.verticalScrollBar().setValue(0)

    def remove_effect(self, eid):
        """Remove o efeito e seu atalho global."""
        if QMessageBox.question(self, "Confirmar", "Deseja excluir este efeito?") == QMessageBox.Yes:
            self.hotkeys.remove_custom_hotkey(eid)
            if eid in self.profile["custom_effects"]:
                del self.profile["custom_effects"][eid]
                self.cfg.save()
                self.refresh_list()