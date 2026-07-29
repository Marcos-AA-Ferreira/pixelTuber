# ui/tabs/background_tab.py
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFileDialog, QFrame, QGroupBox, 
                               QScrollArea, QSlider, QStyleOptionSlider, QStyle)
from PySide6.QtCore import Qt, QTime
from PySide6.QtGui import QPixmap

from ui.tabs.background_tab_component.music_toast import MusicToast
from ui.utils.form_builder import FormBuilder
from core.utils import validate_path
from core.event_bus import EventBus

class ClickableSlider(QSlider):
    """Barra de progresso clicável para avançar a música"""
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            sr = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
            if not sr.contains(event.pos()):
                new_val = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), event.pos().x(), self.width())
                self.setValue(new_val)
                self.sliderMoved.emit(new_val)
        super().mousePressEvent(event)

class BackgroundTab(QWidget):
    def __init__(self, config_manager):
        super().__init__()
        self.bus = EventBus.instance()
        self.cfg = config_manager
        self.toast = MusicToast(None)
        
        # Mapeamento do Combobox de Camadas
        self.layer_options = ["⬇️ Fundo (Atrás do Avatar)", "🟦 Normal", "⬆️ Sobrepor (Frente do Avatar)"]
        
        self.init_ui()
        self.connect_events_and_signals()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setSpacing(20)

        self._setup_visual_section()
        self._setup_audio_section()
        
        self.layout.addStretch()
        scroll.setWidget(container)
        layout_principal.addWidget(scroll)

    # =================================================================
    # DATA-DRIVEN UI + CUSTOM UI (HÍBRIDO)
    # =================================================================

    def _setup_visual_section(self):
        bg_group = QGroupBox("🖼️ AMBIENTE VISUAL E RENDERIZAÇÃO")
        bg_layout = QVBoxLayout(bg_group)
        bg_layout.setSpacing(15)
        
        # --- UI Customizada (Preview da Imagem) ---
        self.preview_label = QLabel("Sem Fundo")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedSize(220, 110)
        self.preview_label.setScaledContents(True)
        
        preview_container = QHBoxLayout()
        preview_container.addStretch()
        preview_container.addWidget(self.preview_label)
        preview_container.addStretch()
        bg_layout.addLayout(preview_container)

        bg_btn_row = QHBoxLayout()
        self.btn_sel = QPushButton("🖼️ ESCOLHER IMAGEM DE FUNDO")
        self.btn_rem = QPushButton("🗑️")
        self.btn_rem.setFixedWidth(40)
        bg_btn_row.addWidget(self.btn_sel)
        bg_btn_row.addWidget(self.btn_rem)
        bg_layout.addLayout(bg_btn_row)

        # --- UI Data-Driven (Configurações da Imagem) ---
        render_frame = QFrame()
        render_frame.setObjectName("SeparatorFrame")
        builder_render = FormBuilder(QVBoxLayout(render_frame))
        
        schema_visual = [
            {"type": "combobox", "key": "bg_layer_level", "title": "Profundidade da Camada:", "options": self.layer_options, "default": self.layer_options[0]},
            {"type": "custom_slider", "key": "bg_opacity", "title": "Nível de Opacidade:", "min_val": 0, "max_val": 100, "default": 100, "unit": "%"},
            {"type": "custom_slider", "key": "bg_blur", "title": "Intensidade do Desfoque:", "min_val": 0, "max_val": 50, "default": 0, "unit": " px"}
        ]
        builder_render.build_from_schema(schema_visual, self._get_setting_value, self._on_setting_changed)
        
        bg_layout.addWidget(render_frame)
        self.layout.addWidget(bg_group)

    def _setup_audio_section(self):
        audio_group = QGroupBox("🎵 TRILHA SONORA E NOTIFICAÇÃO")
        audio_layout = QVBoxLayout(audio_group)
        builder_audio = FormBuilder(audio_layout)
        
        # --- UI Data-Driven (Posição do Toast) ---
        schema_top = [
            {"type": "combobox", "key": "system.toast_position", "title": "Posição da Notificação (Toast):", "options": ["Canto Inferior Direito", "Canto Superior Direito", "Canto Inferior Esquerdo", "Canto Superior Esquerdo"], "default": "Canto Inferior Direito"}
        ]
        builder_audio.build_from_schema(schema_top, self._get_setting_value, self._on_setting_changed)

        # --- UI Customizada (Player de Música) ---
        self.lbl_music_info = QLabel("Nenhuma trilha")
        self.lbl_music_info.setWordWrap(True)
        builder_audio._add_row("Faixa Atual:", self.lbl_music_info)
        
        self.slider_progress = ClickableSlider(Qt.Horizontal)
        builder_audio._add_row("Progresso:", self.slider_progress)
        
        self.lbl_time = QLabel("00:00 / 00:00")
        self.lbl_time.setAlignment(Qt.AlignRight)
        audio_layout.addWidget(self.lbl_time)
        
        music_nav_row = QHBoxLayout()
        self.btn_music_sel = QPushButton("🎵 ESCOLHER MÚSICA")
        self.btn_music_stop = QPushButton("🛑 PARAR")
        self.btn_prev = QPushButton("⏮️")
        self.btn_play_pause = QPushButton("⏯️")
        self.btn_next = QPushButton("⏭️")
        
        for btn in [self.btn_prev, self.btn_next]: btn.setFixedWidth(45)
        self.btn_play_pause.setFixedWidth(60)
        
        music_nav_row.addWidget(self.btn_music_sel)
        music_nav_row.addWidget(self.btn_music_stop)
        music_nav_row.addStretch()
        music_nav_row.addWidget(self.btn_prev)
        music_nav_row.addWidget(self.btn_play_pause)
        music_nav_row.addWidget(self.btn_next)
        audio_layout.addLayout(music_nav_row)

        # --- UI Data-Driven (Volume e Loop) ---
        schema_bottom = [
            {"type": "switch", "key": "bg_music_loop", "title": "🔂 Loop Automático", "default": True},
            {"type": "custom_slider", "key": "bg_music_vol", "title": "Volume Principal:", "min_val": 0, "max_val": 100, "default": 50, "unit": "%"},
            {"type": "switch", "key": "bg_music_muted", "title": "🔇 Mudo", "default": False}
        ]
        builder_audio.build_from_schema(schema_bottom, self._get_setting_value, self._on_setting_changed)
        
        self.layout.addWidget(audio_group)

    # =================================================================
    # ROTEADORES DE DADOS (GETTERS & SETTERS)
    # =================================================================

    def _get_setting_value(self, key: str):
        """Busca o valor atual para preencher os formulários"""
        if key.startswith("system."):
            return self.cfg.data.get("system", {}).get(key.split(".")[1])
            
        if key == "bg_layer_level":
            idx = self.cfg.data.get("bg_layer_level", 0)
            return self.layer_options[idx] if idx < len(self.layer_options) else self.layer_options[0]
            
        return self.cfg.data.get(key)

    def _on_setting_changed(self, key: str, value):
        """Recebe alterações do form e salva automaticamente"""
        if key.startswith("system."):
            self.cfg.data.setdefault("system", {})[key.split(".")[1]] = value
            self.cfg.save()
            return
            
        if key == "bg_layer_level":
            value = self.layer_options.index(value) if value in self.layer_options else 0
            
        self.cfg.data[key] = value
        self.cfg.save()
        
        # Dispara atualizações reais para o sistema
        if key in ["bg_opacity", "bg_blur", "bg_layer_level"]:
            self._dispatch_visual_update()
        elif key in ["bg_music_vol", "bg_music_muted", "bg_music_loop"]:
            self._dispatch_audio_update()

    def _dispatch_visual_update(self):
        self.bus.request_bg_visual_update.emit({
            "bg_opacity": self.cfg.data.get("bg_opacity", 100),
            "bg_blur": self.cfg.data.get("bg_blur", 0),
            "bg_layer_level": self.cfg.data.get("bg_layer_level", 0)
        })

    def _dispatch_audio_update(self):
        self.bus.request_bg_audio_update.emit({
            "volume": self.cfg.data.get("bg_music_vol", 50),
            "muted": self.cfg.data.get("bg_music_muted", False),
            "loop": self.cfg.data.get("bg_music_loop", True)
        })

    # =================================================================
    # CONEXÕES E CALLBACKS CUSTOMIZADOS (PLAYER E BOTOES)
    # =================================================================

    def connect_events_and_signals(self):
        self.btn_sel.clicked.connect(self._on_choose_bg_clicked)
        self.btn_rem.clicked.connect(self.bus.request_bg_image_remove.emit)
        
        self.btn_music_sel.clicked.connect(self._on_choose_music_clicked)
        self.btn_music_stop.clicked.connect(self.bus.request_music_remove.emit)
        self.btn_next.clicked.connect(self.bus.request_music_next.emit)
        self.btn_prev.clicked.connect(self.bus.request_music_prev.emit)
        self.btn_play_pause.clicked.connect(self.toggle_play_pause)
        
        self.toast.btn_play.clicked.connect(self.toggle_play_pause)
        self.toast.btn_next.clicked.connect(self.bus.request_music_next.emit)

        # Sinais Reversos do Manager
        self.bus.bg_visual_changed.connect(self._on_visual_changed)
        self.bus.bg_music_changed.connect(self._on_music_changed)
        
        # Player de Fundo
        self.bus.bg_player_position_updated.connect(self._on_player_position_changed)
        self.bus.bg_player_duration_updated.connect(lambda duration: self.slider_progress.setRange(0, duration))
        self.bus.bg_player_metadata_updated.connect(self._lazy_metadata_update)
        self.bus.bg_player_state_changed.connect(self._on_player_state_changed)
        
        # Interação do usuário com a barra
        self.slider_progress.sliderMoved.connect(self.bus.request_bg_player_set_position.emit)

    def _on_choose_bg_clicked(self):
        p, _ = QFileDialog.getOpenFileName(self, "Escolher Fundo", "", "Mídia (*.png *.jpg *.gif)")
        if p: self.bus.request_bg_image_change.emit(p)

    def _on_choose_music_clicked(self):
        p, _ = QFileDialog.getOpenFileName(self, "Selecionar BGM", "", "Áudio (*.mp3 *.wav *.ogg)")
        if p: self.bus.request_bg_music_change.emit(p)

    def _on_visual_changed(self, bg_config):
        path = bg_config.get("path", "")
        if validate_path(path):
            pix = QPixmap(path)
            self.preview_label.setPixmap(pix.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.preview_label.setText("Sem Fundo")
            self.preview_label.setPixmap(QPixmap())

    def _on_music_changed(self, path):
        if not path:
            self.lbl_music_info.setText("Nenhuma trilha")
            self.toast.hide_toast()
            return
        title = os.path.basename(path).replace(".wav", "").replace(".mp3", "")
        self.lbl_music_info.setText(f"🎧 {title}")
        self.trigger_toast_notification()

    def _lazy_metadata_update(self, title):
        if title:
            self.lbl_music_info.setText(f"🎧 {title}")
            self.toast.lbl_title.setText(title[:25] + "..." if len(title) > 25 else title)

    def toggle_play_pause(self):
        self.bus.request_music_play_pause.emit()

    def _on_player_state_changed(self, is_playing):
        char = "⏸️" if is_playing else "▶️"
        self.toast.btn_play.setText(char)
        self.btn_play_pause.setText(char)

    def _on_player_position_changed(self, pos):
        if not self.slider_progress.isSliderDown():
            self.slider_progress.setValue(pos)
        duration = self.slider_progress.maximum()
        curr = QTime(0, 0).addMSecs(pos).toString("mm:ss")
        total = QTime(0, 0).addMSecs(duration).toString("mm:ss")
        self.lbl_time.setText(f"{curr} / {total}")

    def trigger_toast_notification(self):
        current_path = self.cfg.data.get("bg_music_path", "")
        if not current_path: return
        title = os.path.basename(current_path).replace(".wav", "").replace(".mp3", "")
        
        pixmap = None
        folder = os.path.dirname(current_path)
        for ext in ['jpg', 'png', 'jpeg']:
            for name in ['cover', 'folder', 'front', 'art']:
                img_path = os.path.join(folder, f"{name}.{ext}")
                if os.path.exists(img_path):
                    pixmap = QPixmap(img_path)
                    break
            if pixmap: break
            
        pos_map = {
            "Canto Inferior Direito": "bottom_right", "Canto Superior Direito": "top_right",
            "Canto Inferior Esquerdo": "bottom_left", "Canto Superior Esquerdo": "top_left"
        }
        target_pos = pos_map.get(self.cfg.data.get("system", {}).get("toast_position", ""), "bottom_right")
        self.toast.update_info(title=title, artist="Ficheiro Local", cover_pixmap=pixmap)
        self.toast.show_toast(position_name=target_pos)

    def _on_choose_bg_clicked(self):
        p, _ = QFileDialog.getOpenFileName(self, "Escolher Fundo", "", "Mídia (*.png *.jpg *.gif)")
        if p: self.bus.request_bg_image_change.emit(p)

    def _on_choose_music_clicked(self):
        p, _ = QFileDialog.getOpenFileName(self, "Selecionar BGM", "", "Áudio (*.mp3 *.wav *.ogg)")
        if p: self.bus.request_music_change.emit(p)

    def _on_toast_position_changed(self, text):
        self.cfg.data.setdefault("system", {})["toast_position"] = text
        self.cfg.save()
        self.trigger_toast_notification()

    def select_background_image(self):
        self._on_choose_bg_clicked()