import os
import uuid
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
                             QCheckBox, QPushButton, QFileDialog, QGroupBox, 
                             QScrollArea, QFrame, QLineEdit, QSpinBox,
                             QComboBox, QInputDialog, QMessageBox)
from PySide6.QtCore import Qt
from ui.styles.theme import Theme

class AvatarTab(QWidget):
    def __init__(self, config_manager, render, audio, hotkeys):
        super().__init__()
        self.cfg = config_manager
        self.render = render
        self.audio = audio 
        self.hotkeys = hotkeys
        self.profile = config_manager.data
        self.path_labels = {}

        # Garante que a estrutura de sets existe no profile
        if "animations" not in self.profile:
            self.profile["animations"] = {"main_set": "default", "sets": {"default": {}}}

        # Aplica o estilo unificado
        self.setStyleSheet(
            Theme.MAIN_TAB_STYLE + 
            Theme.GROUP_BOX + 
            Theme.BUTTON_BASE + 
            Theme.BUTTON_MUTE_ACTIVE + 
            Theme.SPIN_BOX_Z
        )

        layout_principal = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        self.main_layout = QVBoxLayout(container)
        
        self._setup_window_controls()
        self._setup_wardrobe_section()  # NOVA SEÇÃO: Guarda-Roupa
        self._setup_sprites_section()
        self._setup_extras_section()

        scroll.setWidget(container)
        layout_principal.addWidget(scroll)

    def _setup_window_controls(self):
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

        h_scale = QHBoxLayout()
        h_scale.addWidget(QLabel("Escala Geral (Zoom):"))
        self.lbl_scale_pct = QLabel("100%") 
        h_scale.addStretch()
        h_scale.addWidget(self.lbl_scale_pct)
        layout.addLayout(h_scale)

        self.scale_sld = QSlider(Qt.Horizontal)
        self.scale_sld.setRange(10, 400)
        current_scale = self.profile["render"].get("scale", 1.0)
        self.scale_sld.setValue(int(current_scale * 100))
        self.lbl_scale_pct.setText(f"{self.scale_sld.value()}%")
        self.scale_sld.valueChanged.connect(self.update_scale)
        layout.addWidget(self.scale_sld)
        
        self.lock_check = QCheckBox("🔒 Travar Posição na Tela")
        self.lock_check.setChecked(self.profile["render"].get("locked", False))
        self.lock_check.toggled.connect(self.toggle_lock)
        layout.addWidget(self.lock_check)
        
        self.main_layout.addWidget(win_group)

    def update_scale(self, v):
        self.lbl_scale_pct.setText(f"{v}%")
        self.profile["render"]["scale"] = v / 100.0
        self.render.update_geometry()
        self.cfg.save()

    # ================================================================
    # SISTEMA DE GUARDA-ROUPA (WARDROBE)
    # ================================================================
    def _setup_wardrobe_section(self):
        wardrobe_group = QGroupBox("👗 GUARDA-ROUPA (SKINS)")
        layout = QVBoxLayout(wardrobe_group)

        # Combo Box de Seleção e Botão Equipar
        h_top = QHBoxLayout()
        self.combo_wardrobe = QComboBox()
        self.combo_wardrobe.addItems(self.profile["animations"]["sets"].keys())
        current_main = self.profile["animations"].get("main_set", "default")
        self.combo_wardrobe.setCurrentText(current_main)
        self.combo_wardrobe.currentTextChanged.connect(self.refresh_sprite_paths)
        
        self.btn_equip = QPushButton("👕 EQUIPAR SELECIONADO")
        self.btn_equip.clicked.connect(self.equip_selected_set)
        
        h_top.addWidget(self.combo_wardrobe, stretch=1)
        h_top.addWidget(self.btn_equip)
        layout.addLayout(h_top)

        # Botões de Gestão (Novo, Importar Pasta, Excluir)
        h_actions = QHBoxLayout()
        
        btn_new = QPushButton("➕ Novo")
        btn_new.clicked.connect(self.create_new_set)
        
        btn_import = QPushButton("📂 Importar Pasta")
        btn_import.clicked.connect(self.import_folder_set)
        
        btn_del = QPushButton("🗑️ Excluir")
        btn_del.setStyleSheet(Theme.BUTTON_REMOVE)
        btn_del.clicked.connect(self.delete_selected_set)
        
        h_actions.addWidget(btn_new)
        h_actions.addWidget(btn_import)
        h_actions.addWidget(btn_del)
        layout.addLayout(h_actions)

        self.main_layout.addWidget(wardrobe_group)

    def equip_selected_set(self):
        """Define o set selecionado como o avatar ativo no momento."""
        selected = self.combo_wardrobe.currentText()
        if not selected: return
        
        self.profile["animations"]["main_set"] = selected
        self.cfg.save()
        
        # Força o RenderWindow a atualizar imediatamente a imagem
        mute_path = self.profile["animations"]["sets"][selected].get("mute", "")
        self.render.set_animation(mute_path)

    def create_new_set(self):
        """Cria um novo espaço em branco para um avatar."""
        name, ok = QInputDialog.getText(self, "Nova Skin", "Nome do novo Avatar/Skin:")
        if ok and name:
            name = name.strip()
            if name not in self.profile["animations"]["sets"]:
                self.profile["animations"]["sets"][name] = {
                    "mute": "", "low": "", "med": "", "high": "", "very_high": ""
                }
                self.cfg.save()
                self.combo_wardrobe.addItem(name)
                self.combo_wardrobe.setCurrentText(name)

    def import_folder_set(self):
        """Sistema inteligente que lê uma pasta e auto-preenche Mute e Fala."""
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta do Avatar")
        if not folder: return

        set_name = os.path.basename(folder)
        if set_name in self.profile["animations"]["sets"]:
            set_name += f"_{uuid.uuid4().hex[:4]}" # Evita sobrescrever nomes iguais
        
        new_set = {"mute": "", "low": "", "med": "", "high": "", "very_high": ""}
        
        # Heurística para achar as imagens com base no padrão do usuário (NF = Não Fala, F = Fala)
        files = [f for f in os.listdir(folder) if f.lower().endswith(('.gif', '.png'))]
        for f in files:
            fname = f.lower()
            path = os.path.join(folder, f)
            # Padrões para Mudo
            if "mute" in fname or "nf" in fname or "fechad" in fname:
                new_set["mute"] = path
            # Padrões para Fala
            elif "low" in fname or "- f" in fname or "fala" in fname or "abert" in fname:
                new_set["low"] = path
        
        # Prevenção: Se achou imagens mas o mute ficou vazio, pega a primeira
        if not new_set["mute"] and files:
            new_set["mute"] = os.path.join(folder, files[0])

        self.profile["animations"]["sets"][set_name] = new_set
        self.cfg.save()
        
        self.combo_wardrobe.addItem(set_name)
        self.combo_wardrobe.setCurrentText(set_name)
        self.equip_selected_set()
        QMessageBox.information(self, "Sucesso", f"Avatar '{set_name}' importado com sucesso!")

    def delete_selected_set(self):
        """Remove a skin selecionada (bloqueia se for a única ou a padrão)."""
        selected = self.combo_wardrobe.currentText()
        if selected == "default" or len(self.profile["animations"]["sets"]) <= 1:
            QMessageBox.warning(self, "Aviso", "Você não pode deletar a skin principal ou única.")
            return
            
        ans = QMessageBox.question(self, "Confirmação", f"Deletar a skin '{selected}'?")
        if ans == QMessageBox.Yes:
            del self.profile["animations"]["sets"][selected]
            # Se deletou a equipada, volta pra default
            if self.profile["animations"].get("main_set") == selected:
                self.profile["animations"]["main_set"] = "default"
            
            self.cfg.save()
            self.combo_wardrobe.removeItem(self.combo_wardrobe.findText(selected))
            self.equip_selected_set()

    # ================================================================
    # ESTADOS DE ANIMAÇÃO (EDITA O QUE ESTÁ SELECIONADO NO GUARDA-ROUPA)
    # ================================================================
    def _setup_sprites_section(self):
        sprite_group = QGroupBox("🎭 EDITAR ANIMAÇÕES (SKIN SELECIONADA)")
        layout = QVBoxLayout(sprite_group)
        
        states = [("Mudo", "mute", "🔇"), ("Baixo", "low", "🔈"), 
                  ("Médio", "med", "🔉"), ("Alto", "high", "🔊")]

        for label, key, icon in states:
            h = QHBoxLayout()
            btn_load = QPushButton(f"{icon} {label}")
            btn_load.setFixedWidth(110)
            btn_load.clicked.connect(lambda chk=False, st=key: self.set_gif(st))
            
            lbl_path = QLabel("Vazio")
            self.path_labels[key] = lbl_path
            
            btn_clear = QPushButton("🗑️")
            btn_clear.setStyleSheet(Theme.BUTTON_REMOVE)
            btn_clear.setFixedSize(30, 30)
            btn_clear.clicked.connect(lambda chk=False, st=key: self.clear_gif(st))
            
            h.addWidget(btn_load)
            h.addWidget(lbl_path)
            h.addStretch()
            h.addWidget(btn_clear)
            layout.addLayout(h)

        self.main_layout.addWidget(sprite_group)
        self.refresh_sprite_paths()

    def refresh_sprite_paths(self, _=None):
        """Atualiza as labels de texto com base no Avatar atualmente selecionado na combo box."""
        current_set = self.combo_wardrobe.currentText()
        if not current_set or current_set not in self.profile["animations"]["sets"]: 
            return
            
        anim_set = self.profile["animations"]["sets"][current_set]
        
        for key, lbl in self.path_labels.items():
            path = anim_set.get(key, "")
            if path:
                lbl.setText(os.path.basename(path))
                lbl.setStyleSheet(f"color: {Theme.ACCENT_GREEN};")
            else:
                lbl.setText("Vazio")
                lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED};")

    def clear_gif(self, state):
        current_set = self.combo_wardrobe.currentText()
        if not current_set: return
        
        self.profile["animations"]["sets"][current_set][state] = ""
        self.refresh_sprite_paths()
        self.cfg.save()
        
        # Se estiver limpando a skin ativamente em uso
        if current_set == self.profile["animations"].get("main_set"):
            self.render.set_animation("")

    def set_gif(self, state):
        current_set = self.combo_wardrobe.currentText()
        if not current_set: return
        
        p, _ = QFileDialog.getOpenFileName(self, "Escolher Sprite", "", "Imagens (*.gif *.png)")
        if p:
            self.profile["animations"]["sets"][current_set][state] = p
            self.refresh_sprite_paths()
            self.cfg.save()
            
            # Se editou a skin que está na tela agora, atualiza o render
            if current_set == self.profile["animations"].get("main_set") and self.render.current_state == state:
                self.render.set_animation(p)

    def _setup_extras_section(self):
        extras_group = QGroupBox("➕ ACESSÓRIOS")
        self.extras_layout = QVBoxLayout(extras_group)
        
        self.btn_add_extra = QPushButton("➕ ADICIONAR NOVO ACESSÓRIO")
        self.btn_add_extra.setStyleSheet(Theme.BUTTON_PRIMARY)
        self.btn_add_extra.clicked.connect(self.add_layer)
        self.extras_layout.addWidget(self.btn_add_extra)

        self.layers_container = QWidget()
        self.layers_layout = QVBoxLayout(self.layers_container)
        self.extras_layout.addWidget(self.layers_container)
        self.main_layout.addWidget(extras_group)
        self.refresh_extras_ui()

    def update_ui(self):
        if self.btn_mute.isChecked() != self.audio.muted:
            self.btn_mute.blockSignals(True)
            self.btn_mute.setChecked(self.audio.muted)
            self.btn_mute.blockSignals(False)

        current_state = getattr(self.render, "current_state", None)
        current_set = self.combo_wardrobe.currentText()
        is_editing_active = (current_set == self.profile["animations"].get("main_set"))
        
        for key, lbl in self.path_labels.items():
            path = self.profile["animations"]["sets"].get(current_set, {}).get(key, "")
            if not path:
                lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED};")
                continue
                
            # Brilha a label se a skin estiver equipada e no exato estado atual de voz
            if is_editing_active and key == current_state:
                lbl.setStyleSheet(f"color: {Theme.ACCENT}; font-weight: bold;")
            else:
                lbl.setStyleSheet(f"color: {Theme.ACCENT_GREEN}; font-weight: normal;")
                
        # Gerencia o estado visual do botão "Equipar"
        if is_editing_active:
            self.btn_equip.setText("✅ EQUIPADO")
            self.btn_equip.setEnabled(False)
            self.btn_equip.setStyleSheet(Theme.BUTTON_BASE)
        else:
            self.btn_equip.setText("👕 EQUIPAR SELECIONADO")
            self.btn_equip.setEnabled(True)
            self.btn_equip.setStyleSheet(Theme.BUTTON_PRIMARY)

    def refresh_extras_ui(self):
        while self.layers_layout.count():
            item = self.layers_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        for l_id, config in self.cfg.data.get("aux_layers", {}).items():
            card = self._create_accessory_card(l_id, config)
            self.layers_layout.addWidget(card)

    def _create_accessory_card(self, l_id, c):
        card = QFrame()
        card.setStyleSheet(Theme.ACCESSORY_CARD)
        v = QVBoxLayout(card)

        h_top = QHBoxLayout()
        filename = os.path.basename(c.get("path", "Item"))
        name = filename.split('.')[0] if '.' in filename else filename
        h_top.addWidget(QLabel(f"<b>{name.upper()}</b>"))
        
        btn_del = QPushButton("🗑️")
        btn_del.setStyleSheet(Theme.BUTTON_REMOVE)
        btn_del.setFixedSize(28, 28)
        btn_del.clicked.connect(lambda: self.delete_layer(l_id))
        h_top.addWidget(btn_del)
        v.addLayout(h_top)

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
        btn_z_down.setStyleSheet(Theme.Z_NAV_BUTTON)
        
        lbl_z_val = QLabel(str(c.get("z_index", 1)))
        lbl_z_val.setAlignment(Qt.AlignCenter)
        lbl_z_val.setStyleSheet(Theme.Z_DISPLAY)
        
        btn_z_up = QPushButton(">")
        btn_z_up.setFixedSize(22, 22)
        btn_z_up.setStyleSheet(Theme.Z_NAV_BUTTON)

        btn_z_down.clicked.connect(lambda: self.change_z_index(l_id, lbl_z_val, -1))
        btn_z_up.clicked.connect(lambda: self.change_z_index(l_id, lbl_z_val, 1))

        h_row.addWidget(btn_z_down)
        h_row.addWidget(lbl_z_val)
        h_row.addWidget(btn_z_up)

        v.addLayout(h_row)

        v.addWidget(QLabel("Escala do Item:"))
        s_sld = QSlider(Qt.Horizontal)
        s_sld.setRange(5, 300)
        s_sld.setValue(int(c.get("scale", 1.0) * 100))
        s_sld.valueChanged.connect(lambda val: self.update_extra_val(l_id, "scale", val/100.0))
        v.addWidget(s_sld)

        h_opts = QHBoxLayout()
        for key, txt in [("visible", "Ativo"), ("locked", "Travar"), ("flip_h", "Espelhar")]:
            cb = QCheckBox(txt)
            cb.setChecked(c.get(key, False))
            cb.toggled.connect(lambda val, k=key: self.update_extra_val(l_id, k, val))
            h_opts.addWidget(cb)
        v.addLayout(h_opts)
        return card

    def change_z_index(self, l_id, label, delta):
        current = self.cfg.data["aux_layers"][l_id].get("z_index", 1)
        new_val = max(-50, min(50, current + delta))
        label.setText(str(new_val))
        self.update_extra_val(l_id, "z_index", new_val)

    def update_extra_val(self, l_id, key, val):
        self.cfg.data["aux_layers"][l_id][key] = val
        self.render.update_geometry()
        self.cfg.save()

    def add_layer(self):
        p, _ = QFileDialog.getOpenFileName(self, "Novo Acessório", "", "Imagens (*.gif *.png *.jpg)")
        if p:
            uid = f"item_{uuid.uuid4().hex[:4]}"
            self.cfg.data.setdefault("aux_layers", {})[uid] = {
                "path": p, "rel_x": 0, "rel_y": 0, "scale": 1.0, 
                "rotation": 0, "locked": False, "visible": True, "z_index": 1
            }
            self.refresh_extras_ui()
            self.render.update_geometry()
            self.cfg.save()

    def delete_layer(self, l_id):
        if l_id in self.cfg.data["aux_layers"]:
            del self.cfg.data["aux_layers"][l_id]
            self.refresh_extras_ui()
            self.render.update_geometry()
            self.cfg.save()

    def toggle_visibility(self, checked):
        self.render.setVisible(not checked)

    def toggle_minimize_render(self):
        if self.render.isMinimized(): self.render.showNormal()
        else: self.render.showMinimized()

    def toggle_mute_direct(self, checked):
        self.audio.muted = checked

    def toggle_lock(self, v):
        self.profile["render"]["locked"] = v
        self.cfg.save()

    def update_hotkey(self, l_id, key_str):
        self.cfg.data["aux_layers"][l_id]["hotkey"] = key_str.strip().lower()
        self.hotkeys.setup_defaults()
        self.cfg.save()