# ui/tabs/avatar_tab.py
import os
import uuid
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
                             QCheckBox, QPushButton, QFileDialog, QGroupBox, 
                             QScrollArea, QFrame, QLineEdit, QComboBox, 
                             QInputDialog, QMessageBox, QStackedWidget)
from PySide6.QtCore import Qt

from core.event_bus import EventBus

from ui.widgets.labeled_slider import LabeledSlider
from ui.utils.form_builder import FormBuilder
from ui.schemas.avatar_schema import ( AVATAR_GENERAL_SCHEMA, AVATAR_TRANSFORM_SCHEMA, AVATAR_ANIMATION_SCHEMA )

class AvatarTab(QWidget):
    def __init__(self, config_manager):
        super().__init__()
        self.cfg = config_manager
        self.bus = EventBus.instance()
        self.profile = config_manager.data
        self.path_labels = {}

        if "animations" not in self.profile:
            self.profile["animations"] = {"main_set": "default", "sets": {"default": {}}}

        self._init_ui()
        self.refresh_sprite_paths()
        self.refresh_extras_ui()
        self.connect_bus_signals()

    # =================================================================
    # 1. DATA-DRIVEN UI HELPER METHODS
    # =================================================================
    def _get_setting_value(self, key: str):
        """Lê o valor da chave no ConfigManager interpretando o ponto (ex: render.scale)."""
        if "." in key:
            domain, subkey = key.split(".", 1)
            # O slider precisa de valores entre 0 e 100 (int), mas o JSON salva entre 0.0 e 1.0 (float)
            val = self.cfg.data.get(domain, {}).get(subkey)
            if key == "render.scale" and val is not None:
                return int(val * 100)
            return val
            
        return self.cfg.data.get(key)

    def _on_setting_changed(self, key: str, value):
        """Atualiza a chave no ConfigManager, salva e notifica o sistema."""
        # Se for o slider de escala, converte de volta de 100 para 1.0
        if key == "render.scale":
            value = value / 100.0

        if "." in key:
            domain, subkey = key.split(".", 1)
            self.cfg.data.setdefault(domain, {})[subkey] = value
        else:
            self.cfg.data[key] = value

        self.cfg.save()

        # Se a alteração for de escala ou visual, notifica a janela de renderização
        if "scale" in key or "flip_h" in key:
            self.bus.request_geometry_update.emit()

    # =================================================================
    # 2. ESTRUTURA DE LAYOUT PRINCIPAL
    # =================================================================
    def _init_ui(self):
        """Estrutura base da janela de scroll."""
        layout_principal = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setSpacing(15)

        # 1. Botões de ação da janela (Mantidos via método limpo)
        self._setup_window_actions()

        # 2. Constrói as seções declarativas (Data-Driven via FormBuilder)
        self._setup_sections(self.main_layout)

        # 3. Chama os métodos originais que já anexam os grupos ao layout internamente
        self._setup_wardrobe_section()
        self._setup_sprites_section()
        self._setup_extras_section()

        self.main_layout.addStretch()

        scroll.setWidget(container)
        layout_principal.addWidget(scroll)

    def _setup_window_actions(self):
        """Monta APENAS os botões de controle, sem os sliders antigos."""
        win_group = QGroupBox("🎮 CONTROLE DO AVATAR")
        layout = QVBoxLayout(win_group)
        
        btns = QHBoxLayout()
        self.btn_visibility = QPushButton("👁️ VISÍVEL")
        self.btn_visibility.setCheckable(True)
        self.btn_visibility.clicked.connect(self.toggle_visibility)
        
        self.btn_minimize = QPushButton("🗕 MINIMIZAR")
        self.btn_minimize.clicked.connect(self.toggle_minimize_render)
        
        self.btn_mute = QPushButton("🎤 MUDO (M)")
        self.btn_mute.setObjectName("BtnMute")
        self.btn_mute.setCheckable(True)
        self.btn_mute.clicked.connect(self.toggle_mute_direct)
        
        btns.addWidget(self.btn_visibility)
        btns.addWidget(self.btn_minimize)
        btns.addWidget(self.btn_mute)
        layout.addLayout(btns)
        
        self.main_layout.addWidget(win_group)

    def connect_bus_signals(self):
        """Escuta retornos de outros módulos via EventBus."""
        if hasattr(self.bus, 'audio_mute_updated'):
            self.bus.audio_mute_updated.connect(self._sync_mute_button)

    # =================================================================
    # 3. CONSTRUTOR DE SEÇÕES DECLARATIVO (ADICIONAR)
    # =================================================================
    def _setup_sections(self, target_layout):
        """Cria as caixas de formulário a partir dos schemas importados."""
        
        # --- Grupo 1: Informações Gerais ---
        gen_group = QGroupBox("👤 INFORMAÇÕES DO AVATAR")
        FormBuilder(QVBoxLayout(gen_group)).build_from_schema(
            AVATAR_GENERAL_SCHEMA, 
            self._get_setting_value, 
            self._on_setting_changed
        )
        target_layout.addWidget(gen_group)

        # --- Grupo 2: Transformação e Posicionamento ---
        trans_group = QGroupBox("📐 TRANSFORMAÇÃO E POSICIONAMENTO")
        FormBuilder(QVBoxLayout(trans_group)).build_from_schema(
            AVATAR_TRANSFORM_SCHEMA, 
            self._get_setting_value, 
            self._on_setting_changed
        )
        target_layout.addWidget(trans_group)

        # --- Grupo 3: Reprodução e FPS ---
        anim_group = QGroupBox("🎬 REPRODUÇÃO E FPS")
        FormBuilder(QVBoxLayout(anim_group)).build_from_schema(
            AVATAR_ANIMATION_SCHEMA, 
            self._get_setting_value, 
            self._on_setting_changed
        )
        target_layout.addWidget(anim_group)

    def _setup_wardrobe_section(self):
        wardrobe_group = QGroupBox("👕 GUARDA-ROUPA (SKINS)")
        layout = QVBoxLayout(wardrobe_group)
        
        h_top = QHBoxLayout()
        self.combo_wardrobe = QComboBox()
        self.combo_wardrobe.addItems(self.profile["animations"].get("sets", {}).keys())
        current_main = self.profile["animations"].get("main_set", "default")
        self.combo_wardrobe.setCurrentText(current_main)
        self.combo_wardrobe.currentTextChanged.connect(self.refresh_sprite_paths)
        
        self.btn_equip = QPushButton("👕 EQUIPAR SELECIONADO")
        self.btn_equip.clicked.connect(self.equip_selected_set)
        
        h_top.addWidget(self.combo_wardrobe, stretch=1)
        h_top.addWidget(self.btn_equip)
        layout.addLayout(h_top)
        
        h_actions = QHBoxLayout()
        btn_new = QPushButton("➕ Nova Skin")
        btn_new.clicked.connect(self.create_new_set)
        
        btn_import = QPushButton("📂 Importar Pasta")
        btn_import.clicked.connect(self.import_folder_set)
        
        btn_del = QPushButton("🗑️ Excluir")
        btn_del.clicked.connect(self.delete_selected_set)
        
        h_actions.addWidget(btn_new)
        h_actions.addWidget(btn_import)
        h_actions.addWidget(btn_del)
        layout.addLayout(h_actions)
        
        self.main_layout.addWidget(wardrobe_group)

    def _setup_sprites_section(self):
        sprite_group = QGroupBox("🎭 EDITAR ANIMAÇÕES (SKIN SELECIONADA)")
        layout = QVBoxLayout(sprite_group)
        
        # Seletor de Modo
        mode_lay = QHBoxLayout()
        mode_lay.addWidget(QLabel("Modo do Avatar:"))
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Avatar Inteiro (Legado)", "Cabeça e Corpo Separados"])
        self.combo_mode.currentTextChanged.connect(self.change_avatar_mode)
        mode_lay.addWidget(self.combo_mode, stretch=1)
        layout.addLayout(mode_lay)

        # Sistema de Abas Empilhadas
        self.sprites_stack = QStackedWidget()

        # Página 1: Inteiro
        page_full = QWidget()
        lay_full = QVBoxLayout(page_full)
        lay_full.setContentsMargins(0, 10, 0, 0)
        self._build_sprite_list(lay_full, "full", [
            ("Mudo", "mute", "🔇"), ("Baixo", "low", "🔈"), 
            ("Médio", "med", "🔉"), ("Alto", "high", "🔊"), ("Muito Alto", "very_high", "🔊🔊")
        ])
        self.sprites_stack.addWidget(page_full)

        # Página 2: Separado
        page_split = QWidget()
        lay_split = QVBoxLayout(page_split)
        lay_split.setContentsMargins(0, 10, 0, 0)
        
        lay_split.addWidget(QLabel("<b>CABEÇA (Reage à Voz):</b>"))
        self._build_sprite_list(lay_split, "head", [
            ("Mudo", "mute", "🔇"), ("Baixo", "low", "🔈"), 
            ("Médio", "med", "🔉"), ("Alto", "high", "🔊"), ("Muito Alto", "very_high", "🔊🔊")
        ])
        
        lay_split.addWidget(QLabel("<b>CORPO (Base):</b>"))
        self._build_sprite_list(lay_split, "body", [
            ("Parado (Idle)", "idle", "🧍"), ("Falando (Speaking)", "speaking", "🗣️")
        ])
        self.sprites_stack.addWidget(page_split)

        layout.addWidget(self.sprites_stack)
        self.main_layout.addWidget(sprite_group)

    def _build_sprite_list(self, parent_layout, layer, states):
        """Construtor dinâmico de botões de sprite."""
        for label, key, icon in states:
            h = QHBoxLayout()
            btn_load = QPushButton(f"{icon} {label}")
            btn_load.setFixedWidth(160)
            btn_load.clicked.connect(lambda chk=False, l=layer, st=key: self.set_gif(l, st))
            
            lbl_path = QLabel("Vazio")
            self.path_labels[f"{layer}_{key}"] = lbl_path
            
            btn_clear = QPushButton("🗑️")
            btn_clear.setFixedSize(30, 30)
            btn_clear.clicked.connect(lambda chk=False, l=layer, st=key: self.clear_gif(l, st))
            
            h.addWidget(btn_load)
            h.addWidget(lbl_path)
            h.addStretch()
            h.addWidget(btn_clear)
            parent_layout.addLayout(h)

    def _setup_extras_section(self):
        extras_group = QGroupBox("➕ ACESSÓRIOS E LAYERS")
        self.layout_extras = QVBoxLayout(extras_group)
        
        self.btn_add_extra = QPushButton("➕ ADICIONAR NOVO ACESSÓRIO")
        self.btn_add_extra.clicked.connect(self.add_layer)
        self.layout_extras.addWidget(self.btn_add_extra)

        self.scroll_extras_content = QWidget()
        self.layout_extras_list = QVBoxLayout(self.scroll_extras_content)
        self.layout_extras.addWidget(self.scroll_extras_content)
        
        self.main_layout.addWidget(extras_group)


    # ================================================================
    # 2. ATUALIZADORES E FEEDBACK DA UI
    # ================================================================

    def update_ui(self):
        """Atualiza a aparência dos botões com base no estado atual."""
        current_set = self.combo_wardrobe.currentText()
        is_editing_active = (current_set == self.profile["animations"].get("main_set"))
        
        if is_editing_active:
            self.btn_equip.setText("✅ EQUIPADO")
            self.btn_equip.setEnabled(False)
        else:
            self.btn_equip.setText("👕 EQUIPAR SELECIONADO")
            self.btn_equip.setEnabled(True)

    def refresh_sprite_paths(self, _=None):
        """Lê o JSON e atualiza todos os textos com os caminhos das imagens."""
        current_set = self.combo_wardrobe.currentText()
        if not current_set or current_set not in self.profile["animations"]["sets"]:
            return
            
        anim_set = self.profile["animations"]["sets"][current_set]
        
        mode = anim_set.get("mode", "full")
        self.combo_mode.blockSignals(True)
        idx = 1 if mode == "split" else 0
        self.combo_mode.setCurrentIndex(idx)
        self.sprites_stack.setCurrentIndex(idx)
        self.combo_mode.blockSignals(False)

        # Full e Head
        for key in ["mute", "low", "med", "high", "very_high"]:
            path_full = anim_set.get("full", {}).get(key, anim_set.get(key, ""))
            self._update_lbl(f"full_{key}", path_full)
            path_head = anim_set.get("head", {}).get(key, "")
            self._update_lbl(f"head_{key}", path_head)

        # Body
        for key in ["idle", "speaking"]:
            path_body = anim_set.get("body", {}).get(key, "")
            self._update_lbl(f"body_{key}", path_body)

        self.update_ui()

    def _update_lbl(self, dict_key, path):
        lbl = self.path_labels.get(dict_key)
        if lbl:
            lbl.setText(os.path.basename(path) if path else "Vazio")

    def refresh_extras_ui(self):
        """Limpa e recria a lista visual de acessórios."""
        while self.layout_extras_list.count():
            item = self.layout_extras_list.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        for l_id, config in self.cfg.data.get("aux_layers", {}).items():
            self.layout_extras_list.addWidget(self._create_accessory_card(l_id, config))

    def _create_accessory_card(self, l_id, c):
        """Cria o bloco individual para configurar cada acessório."""
        card = QFrame()
        v = QVBoxLayout(card)

        # Cabeçalho do Card
        h_top = QHBoxLayout()
        filename = os.path.basename(c.get("path", "Item"))
        h_top.addWidget(QLabel(f"<b>{filename.split('.')[0].upper()}</b>"))
        
        btn_del = QPushButton("🗑️")
        btn_del.setFixedSize(28, 28)
        btn_del.clicked.connect(lambda: self.delete_layer(l_id))
        h_top.addWidget(btn_del)
        v.addLayout(h_top)

        # Atalhos e Z-Index
        h_row = QHBoxLayout()
        h_row.addWidget(QLabel("Atalho:"))
        hk = QLineEdit(c.get("hotkey", ""))
        hk.setFixedWidth(70)
        hk.editingFinished.connect(lambda: self.update_hotkey(l_id, hk.text()))
        h_row.addWidget(hk)
        h_row.addStretch()

        h_row.addWidget(QLabel("Z:"))
        btn_z_down = QPushButton("<")
        btn_z_down.setFixedSize(22, 22)
        lbl_z_val = QLabel(str(c.get("z_index", 1)))
        btn_z_up = QPushButton(">")
        btn_z_up.setFixedSize(22, 22)

        btn_z_down.clicked.connect(lambda: self.change_z_index(l_id, lbl_z_val, -1))
        btn_z_up.clicked.connect(lambda: self.change_z_index(l_id, lbl_z_val, 1))

        h_row.addWidget(btn_z_down)
        h_row.addWidget(lbl_z_val)
        h_row.addWidget(btn_z_up)
        v.addLayout(h_row)

        # Escala
        v.addWidget(QLabel("Escala do Item:"))
        s_sld = QSlider(Qt.Horizontal)
        s_sld.setRange(5, 300)
        s_sld.setValue(int(c.get("scale", 1.0) * 100))
        s_sld.valueChanged.connect(lambda val: self.update_extra_val(l_id, "scale", val/100.0))
        v.addWidget(s_sld)

        # Opções Rápidas
        h_opts = QHBoxLayout()
        for key, txt in [("visible", "Ativo"), ("locked", "Travar"), ("flip_h", "Espelhar")]:
            cb = QCheckBox(txt)
            cb.setChecked(c.get(key, False))
            cb.toggled.connect(lambda val, k=key: self.update_extra_val(l_id, k, val))
            h_opts.addWidget(cb)
        v.addLayout(h_opts)
        return card

    def _sync_mute_button(self, is_muted):
        self.btn_mute.blockSignals(True)
        self.btn_mute.setChecked(is_muted)
        self.btn_mute.blockSignals(False)


    # ================================================================
    # 3. LÓGICA DE NEGÓCIO: GUARDA-ROUPA E SKINS
    # ================================================================

    def equip_selected_set(self):
        selected = self.combo_wardrobe.currentText()
        if selected:
            self.bus.request_animation_set_change.emit(selected)
            self.update_ui()

    def create_new_set(self):
        name, ok = QInputDialog.getText(self, "Nova Skin", "Nome do novo Avatar/Skin:")
        if ok and name and name.strip():
            name = name.strip()
            sets = self.cfg.get_all_sets()
            if name not in sets:
                sets[name] = {"mute": "", "low": "", "med": "", "high": "", "very_high": ""}
                self.cfg.set_animation_config("sets", sets)
                self.combo_wardrobe.addItem(name)
                self.combo_wardrobe.setCurrentText(name)

    def import_folder_set(self):
        # NOTA: No futuro, mover esta heurística para o AnimationManager
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta do Avatar")
        if not folder: return
        
        sets = self.cfg.get_all_sets()
        set_name = os.path.basename(folder)
        
        if set_name in sets:
            set_name += f"_{uuid.uuid4().hex[:4]}"
        
        new_set = {"mute": "", "low": "", "med": "", "high": "", "very_high": ""}
        files = [f for f in os.listdir(folder) if f.lower().endswith(('.gif', '.png', '.jpg', '.jpeg', '.webp'))]
        
        for f in files:
            fname = f.lower()
            path = os.path.join(folder, f)
            if "mute" in fname or "nf" in fname or "fechad" in fname:
                new_set["mute"] = path
            elif "low" in fname or "- f" in fname or "fala" in fname or "abert" in fname:
                new_set["low"] = path
        
        if not new_set["mute"] and files:
            new_set["mute"] = os.path.join(folder, files[0])
            
        sets[set_name] = new_set
        self.cfg.set_animation_config("sets", sets)
        
        self.combo_wardrobe.addItem(set_name)
        self.combo_wardrobe.setCurrentText(set_name)
        self.equip_selected_set()
        QMessageBox.information(self, "Sucesso", f"Avatar '{set_name}' importado!")

    def delete_selected_set(self):
        selected = self.combo_wardrobe.currentText()
        sets = self.cfg.get_all_sets()
        
        if selected == "default" or len(sets) <= 1:
            QMessageBox.warning(self, "Aviso", "Você não pode deletar a skin principal ou única.")
            return
            
        ans = QMessageBox.question(self, "Confirmação", f"Deletar a skin '{selected}'?")
        if ans == QMessageBox.Yes:
            del sets[selected]
            self.cfg.set_animation_config("sets", sets)
            
            if self.cfg.get_active_set() == selected:
                self.bus.request_animation_set_change.emit("default")
                
            self.combo_wardrobe.removeItem(self.combo_wardrobe.findText(selected))
            self.equip_selected_set()


    # ================================================================
    # 4. LÓGICA DE NEGÓCIO: EDIÇÃO DE ANIMAÇÕES
    # ================================================================

    def change_avatar_mode(self, mode_text):
        current_set = self.combo_wardrobe.currentText()
        if not current_set: return

        new_mode = "split" if "Separados" in mode_text else "full"
        self.profile["animations"]["sets"][current_set]["mode"] = new_mode
        self.cfg.save()

        self.sprites_stack.setCurrentIndex(1 if new_mode == "split" else 0)

        if current_set == self.cfg.get_active_set():
             self.bus.request_animation_set_change.emit(current_set)

    def set_gif(self, layer, state):
        p, _ = QFileDialog.getOpenFileName(self, "Escolher Sprite", "", "Imagens (*.gif *.png)")
        if p:
            self._set_sprite_path(layer, state, p)

    def clear_gif(self, layer, state):
        self._set_sprite_path(layer, state, "")

    def _set_sprite_path(self, layer, state, path):
        current_set = self.combo_wardrobe.currentText()
        if not current_set: return

        anim_set = self.profile["animations"]["sets"][current_set]

        if layer == "full":
            anim_set[state] = path 
        else:
            if layer not in anim_set:
                anim_set[layer] = {}
            anim_set[layer][state] = path

        self.cfg.save()
        self.refresh_sprite_paths()
        
        if current_set == self.cfg.get_active_set():
             self.bus.request_animation_set_change.emit(current_set)


    # ================================================================
    # 5. LÓGICA DE NEGÓCIO: ACESSÓRIOS (LAYERS)
    # ================================================================

    def add_layer(self):
        p, _ = QFileDialog.getOpenFileName(self, "Novo Acessório", "", "Imagens (*.gif *.png *.jpg)")
        if p:
            uid = f"item_{uuid.uuid4().hex[:4]}"
            self.cfg.data.setdefault("aux_layers", {})[uid] = {
                "path": p, "rel_x": 0, "rel_y": 0, "scale": 1.0, 
                "rotation": 0, "locked": False, "visible": True, "z_index": 1
            }
            self.refresh_extras_ui()
            self.bus.request_geometry_update.emit()
            self.cfg.save()

    def delete_layer(self, l_id):
        if l_id in self.cfg.data["aux_layers"]:
            del self.cfg.data["aux_layers"][l_id]
            self.refresh_extras_ui()
            self.bus.request_geometry_update.emit()
            self.cfg.save()

    def update_extra_val(self, l_id, key, val):
        self.cfg.data["aux_layers"][l_id][key] = val
        self.bus.request_geometry_update.emit()
        self.cfg.save()

    def change_z_index(self, l_id, label, delta):
        current = self.cfg.data["aux_layers"][l_id].get("z_index", 1)
        new_val = max(-50, min(50, current + delta))
        label.setText(str(new_val))
        self.update_extra_val(l_id, "z_index", new_val)

    def update_hotkey(self, l_id, key_str):
        self.cfg.data["aux_layers"][l_id]["hotkey"] = key_str.strip().lower()
        self.cfg.save()
        self.bus.request_hotkeys_reload.emit()


    # ================================================================
    # 6. COMANDOS DIRETOS (CONTROLES DE JANELA)
    # ================================================================

    def toggle_lock(self, checked):
        self.profile.setdefault("render", {})["locked"] = checked
        self.cfg.save()

    def toggle_visibility(self, checked):
        self.bus.request_avatar_visibility_toggle.emit(not checked)

    def toggle_minimize_render(self):
        self.bus.request_avatar_minimize_toggle.emit()

    def toggle_mute_direct(self, checked):
        self.bus.request_mic_mute_toggle.emit(checked)