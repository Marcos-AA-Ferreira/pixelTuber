from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QScrollArea, 
                             QGridLayout, QMessageBox, QFrame, QGroupBox, QPushButton)
from PySide6.QtCore import Qt
from .effects_tab_component.effect_creator import EffectCreator
from .effects_tab_component.effect_card import EffectCard

from core.event_bus import EventBus

class EffectsTab(QWidget):
    def __init__(self, config_manager):
        super().__init__()
        self.bus = EventBus.instance()
        self.cfg = config_manager
        
        self.profile = self.cfg.data.get("profile", {})
        if "custom_effects" not in self.profile:
            self.profile["custom_effects"] = {}
            
        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(15, 15, 15, 15)
        layout_principal.setSpacing(15)

        # --- BOTÃO PRINCIPAL (NOVA JANELA) ---
        self.btn_new = QPushButton("➕ CRIAR NOVO EFEITO")
        self.btn_new.setObjectName("BtnNewEffect")
        self.btn_new.clicked.connect(lambda: self.open_creator())
        layout_principal.addWidget(self.btn_new)
        
        # --- ÁREA DE SCROLL DA BIBLIOTECA ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        self.main_layout = QVBoxLayout(scroll_content)
        
        # Grids por tipo de efeito
        self.grids = {}
        self.sections = {}
        
        for t_key, t_name in [("visual", "🖼️ Efeitos Visuais"), ("audio", "🎵 Efeitos Sonoros"), ("combo", "⚡ Efeitos Combinados")]:
            group = QGroupBox(t_name)
            self.grids[t_key] = QGridLayout()
            group.setLayout(self.grids[t_key])
            self.main_layout.addWidget(group)
            self.sections[t_key] = group

        scroll.setWidget(scroll_content)
        layout_principal.addWidget(scroll)
        
        self.refresh_list()

    def open_creator(self, effect_id=None, effect_data=None):
        # 1. CORREÇÃO DA JANELA: Passando 'self' como parent 
        # Isso força o modal a ficar travado na frente do app principal
        self.creator_modal = EffectCreator(self) 
        
        # 2. Conecta os sinais do modal para a aba
        self.creator_modal.effect_created.connect(self.add_new_effect)
        
        # 3. CORREÇÃO DO TESTE: Escuta o pedido de teste e repassa
        self.creator_modal.test_requested.connect(self._play_preview_effect)
        
        # 4. Injeção de dados para edição
        if effect_id and effect_data:
            if hasattr(self.creator_modal, 'load_effect'):
                self.creator_modal.load_effect(effect_id, effect_data)
                
        # 5. Exibe a janela
        self.creator_modal.exec()

    def _play_preview_effect(self, data):
        """Monta o pacote padronizado e despacha pelo EventBus."""
        
        # Mapeamos as chaves 'visual' e 'audio' do formulário para o formato
        # exato que o EffectManager e o FullScreenOverlay esperam ('visual_path' e 'audio_path')
        payload = {
            "effect_id": "preview_temp",
            "visual_path": data.get('visual', ''),
            "audio_path": data.get('audio', ''),
            "duration": data.get('duration', 4000),
            "scale": data.get('scale', 1.0),
            "opacity": data.get('opacity', 1.0),
            "x": data.get('x', 500),
            "y": data.get('y', 15),
            "audio_start": data.get('audio_start', 0.0),
            "audio_end": data.get('audio_end', 0.0)
        }
        
        # Emite passando APENAS o dicionário 
        if hasattr(self.bus, 'request_play_effect'):
            self.bus.request_play_effect.emit(payload)

    def refresh_list(self):
        self.profile = self.cfg.data.get("profile", {})
        custom_effects = self.profile.get("custom_effects", {})

        for t in self.grids:
            grid = self.grids[t]
            while grid.count():
                item = grid.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        counts = {"visual": 0, "audio": 0, "combo": 0}

        for eid, d in custom_effects.items():
            t = d.get("type", "visual")
            if t not in self.grids:
                t = "visual"

            card = EffectCard(eid, d)
            card.clicked_delete.connect(self.remove_effect)
            card.clicked_edit.connect(lambda e=eid, data=d: self.open_creator(e, data))
            
            row, col = divmod(counts[t], 4) 
            self.grids[t].addWidget(card, row, col)
            counts[t] += 1

    def add_new_effect(self, data):
        eid = data.pop("id")
        data["type"] = self._determine_effect_type(data)
        
        # 1. Garante que as chaves existem de forma conectada na memória principal
        profile = self.cfg.data.setdefault("profile", {})
        custom_effects = profile.setdefault("custom_effects", {})
        
        # 2. Atualiza os atalhos
        if eid in custom_effects:
            self.bus.request_remove_effect_hotkey.emit(eid)
            
        custom_effects[eid] = data

        if data.get("hotkey"):
            self.bus.request_register_effect_hotkey.emit(eid, data["hotkey"], data)
            
        # 3. Salva e atualiza
        self.cfg.save()
        self.refresh_list()
        
        # Vai para a aba correta
        tab_idx = {"visual": 0, "audio": 1, "combo": 2}.get(data["type"], 0)
        self.tabs.setCurrentIndex(tab_idx)

    def remove_effect(self, eid):
        if QMessageBox.question(self, "Confirmar", "Deseja realmente excluir este efeito?", 
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            if eid in self.profile["custom_effects"]:
                del self.profile["custom_effects"][eid]
                self.bus.request_remove_effect_hotkey.emit(eid)
                self.cfg.save()
                self.refresh_list()

    def _determine_effect_type(self, data):
        has_v = bool(data.get("visual"))
        has_a = bool(data.get("audio"))
        if has_v and has_a:
            return "combo"
        elif has_a:
            return "audio"
        return "visual"