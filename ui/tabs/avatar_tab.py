import os
import uuid
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
                             QCheckBox, QPushButton, QFileDialog, QGroupBox, 
                             QScrollArea, QFrame, QLineEdit, QSpinBox)
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

        # Aplica o estilo unificado vindo do Theme integral
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

    def _setup_sprites_section(self):
        sprite_group = QGroupBox("🎭 ESTADOS DE ANIMAÇÃO")
        layout = QVBoxLayout(sprite_group)
        
        states = [("Mudo", "mute", "🔇"), ("Baixo", "low", "🔈"), 
                  ("Médio", "med", "🔉"), ("Alto", "high", "🔊")]

        for label, key, icon in states:
            h = QHBoxLayout()
            btn_load = QPushButton(f"{icon} {label}")
            btn_load.setFixedWidth(110)
            btn_load.clicked.connect(lambda chk=False, st=key: self.set_gif(st))
            
            lbl_path = QLabel("Vazio")
            path = self.profile["animations"]["sets"]["default"].get(key)
            if path:
                lbl_path.setText(os.path.basename(path))
                lbl_path.setStyleSheet(f"color: {Theme.ACCENT_GREEN};")
            
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
        for key, lbl in self.path_labels.items():
            path = self.profile["animations"]["sets"]["default"].get(key)
            if not path:
                lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED};")
                continue
            if key == current_state:
                lbl.setStyleSheet(f"color: {Theme.ACCENT}; font-weight: bold;")
            else:
                lbl.setStyleSheet(f"color: {Theme.ACCENT_GREEN}; font-weight: normal;")

    def clear_gif(self, state):
        self.profile["animations"]["sets"]["default"][state] = ""
        self.path_labels[state].setText("Vazio")
        self.path_labels[state].setStyleSheet(f"color: {Theme.TEXT_MUTED};")
        self.render.set_animation("")
        self.cfg.save()

    def set_gif(self, state):
        p, _ = QFileDialog.getOpenFileName(self, "Escolher Sprite", "", "GIF (*.gif)")
        if p:
            self.profile["animations"]["sets"]["default"][state] = p
            self.path_labels[state].setText(os.path.basename(p))
            self.path_labels[state].setStyleSheet(f"color: {Theme.ACCENT_GREEN};")
            self.cfg.save()
            if self.render.current_state == state:
                self.render.set_animation(p)

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

        # --- SELETOR Z CUSTOMIZADO |<| num |>| ---
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

        # Conexões para os botões de navegação
        btn_z_down.clicked.connect(lambda: self.change_z_index(l_id, lbl_z_val, -1))
        btn_z_up.clicked.connect(lambda: self.change_z_index(l_id, lbl_z_val, 1))

        h_row.addWidget(btn_z_down)
        h_row.addWidget(lbl_z_val)
        h_row.addWidget(btn_z_up)
        # -----------------------------------------

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
        """Função auxiliar para o seletor |<| num |>|"""
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