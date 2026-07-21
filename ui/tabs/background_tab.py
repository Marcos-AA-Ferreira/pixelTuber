# ui/tabs/background_tab.py
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                             QFileDialog, QHBoxLayout, QComboBox, 
                             QFrame, QCheckBox, QGroupBox, QScrollArea, QStyle, QStyleOptionSlider, QSlider)
from PySide6.QtCore import Qt, QTime
from PySide6.QtGui import QPixmap

from ui.tabs.background_tab_component.music_toast import MusicToast
from ui.widgets.labeled_slider import LabeledSlider
from ui.styles.theme import Theme

from core.utils import validate_path
from core.event_bus import EventBus

class ClickableSlider(QSlider):
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
        self.setStyleSheet(Theme.MAIN_TAB_STYLE + Theme.GROUP_BOX + Theme.BUTTON_BASE)
        self.init_ui()
        self.connect_events_and_signals()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)

        # ==========================================
        # 1. AMBIENTE VISUAL E RENDERIZAÇÃO
        # ==========================================
        bg_group = QGroupBox("🖼️ AMBIENTE VISUAL E RENDERIZAÇÃO")
        bg_layout = QVBoxLayout(bg_group)
        bg_layout.setSpacing(15)
        
        self.preview_label = QLabel("Sem Fundo")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedSize(220, 110)
        self.preview_label.setStyleSheet(Theme.PREVIEW_BOX)
        self.preview_label.setScaledContents(True)
        
        preview_container = QHBoxLayout()
        preview_container.addStretch()
        preview_container.addWidget(self.preview_label)
        preview_container.addStretch()
        bg_layout.addLayout(preview_container)

        bg_btn_row = QHBoxLayout()
        self.btn_sel = QPushButton("🖼️ ESCOLHER IMAGEM DE FUNDO")
        self.btn_sel.setStyleSheet(Theme.BUTTON_PRIMARY)
        self.btn_rem = QPushButton("🗑️")
        self.btn_rem.setStyleSheet(Theme.BUTTON_DANGER)
        self.btn_rem.setFixedWidth(40)
        
        bg_btn_row.addWidget(self.btn_sel)
        bg_btn_row.addWidget(self.btn_rem)
        bg_layout.addLayout(bg_btn_row)

        render_frame = QFrame()
        render_frame.setStyleSheet("QFrame { border-top: 1px solid #30363d; margin-top: 10px; padding-top: 10px; }")
        render_lay = QVBoxLayout(render_frame)
        
        render_lay.addWidget(QLabel("Profundidade da Camada:"))
        self.combo_layer = QComboBox()
        self.combo_layer.addItems(["⬇️ Fundo (Atrás do Avatar)", "🟦 Normal", "⬆️ Sobrepor (Frente do Avatar)"])
        self.combo_layer.setCurrentIndex(self.cfg.data.get("bg_layer_level", 0))
        render_lay.addWidget(self.combo_layer)

        self.slider_alpha = LabeledSlider("Nível de Opacidade:", min_val=0, max_val=100, default_val=self.cfg.data.get("bg_opacity", 100), value_format="{v}%")
        render_lay.addWidget(self.slider_alpha)

        self.slider_blur = LabeledSlider("Intensidade do Desfoque:", min_val=0, max_val=50, default_val=self.cfg.data.get("bg_blur", 0), value_format="{v} px")
        render_lay.addWidget(self.slider_blur)
        
        bg_layout.addWidget(render_frame)
        layout.addWidget(bg_group)

        # ==========================================
        # 2. TRILHA SONORA E NOTIFICAÇÃO (BGM)
        # ==========================================
        audio_group = QGroupBox("🎵 TRILHA SONORA E NOTIFICAÇÃO")
        audio_layout = QVBoxLayout(audio_group)
        
        pos_row = QHBoxLayout()
        pos_row.addWidget(QLabel("Posição da Notificação (Toast):"))
        self.pos_combo = QComboBox()
        self.pos_combo.addItems(["Canto Inferior Direito", "Canto Superior Direito", "Canto Inferior Esquerdo", "Canto Superior Esquerdo"])
        self.pos_combo.setCurrentText(self.cfg.data.get("system", {}).get("toast_position", "Canto Inferior Direito"))
        pos_row.addWidget(self.pos_combo)
        audio_layout.addLayout(pos_row)
        
        self.lbl_music_info = QLabel("Nenhuma trilha")
        self.lbl_music_info.setStyleSheet(Theme.MUSIC_INFO)
        self.lbl_music_info.setWordWrap(True)
        audio_layout.addWidget(self.lbl_music_info)

        self.slider_progress = ClickableSlider(Qt.Horizontal)
        self.slider_progress.setStyleSheet(Theme.PROGRESS_SLIDER)
        audio_layout.addWidget(self.slider_progress)

        self.lbl_time = QLabel("00:00 / 00:00")
        self.lbl_time.setAlignment(Qt.AlignRight)
        self.lbl_time.setStyleSheet(Theme.TIME_LABEL)
        audio_layout.addWidget(self.lbl_time)

        music_nav_row = QHBoxLayout()
        self.btn_prev = QPushButton("⏮️")
        self.btn_prev.setFixedWidth(45)
        self.btn_play_pause = QPushButton("⏯️")
        self.btn_play_pause.setFixedWidth(60)
        self.btn_next = QPushButton("⏭️")
        self.btn_next.setFixedWidth(45)
        
        music_nav_row.addStretch()
        music_nav_row.addWidget(self.btn_prev)
        music_nav_row.addWidget(self.btn_play_pause)
        music_nav_row.addWidget(self.btn_next)
        music_nav_row.addStretch()
        audio_layout.addLayout(music_nav_row)

        music_ctrl_row = QHBoxLayout()
        self.check_loop = QCheckBox("🔂 Loop Automático")
        self.check_loop.setChecked(self.cfg.data.get("bg_music_loop", True))
        music_ctrl_row.addWidget(self.check_loop)
        music_ctrl_row.addStretch()
        audio_layout.addLayout(music_ctrl_row)

        music_actions = QHBoxLayout()
        self.btn_music_sel = QPushButton("🎼 ESCOLHER MÚSICA")
        self.btn_music_stop = QPushButton("🛑 PARAR")
        music_actions.addWidget(self.btn_music_sel)
        music_actions.addWidget(self.btn_music_stop)
        audio_layout.addLayout(music_actions)

        vol_row = QHBoxLayout()
        self.slider_music_vol = LabeledSlider("Volume Principal:", min_val=0, max_val=100, default_val=self.cfg.data.get("bg_music_vol", 50), value_format="{v}%")
        self.check_mute = QCheckBox("🔇 Mudo")
        self.check_mute.setChecked(self.cfg.data.get("bg_music_muted", False))
        
        vol_row.addWidget(self.slider_music_vol, stretch=1)
        vol_row.addWidget(self.check_mute)
        audio_layout.addLayout(vol_row)
        
        layout.addWidget(audio_group)
        scroll.setWidget(container)
        layout_principal.addWidget(scroll)

    def connect_events_and_signals(self):
        # Controles Visuais
        self.btn_sel.clicked.connect(self._on_choose_bg_clicked)
        self.btn_rem.clicked.connect(self.bus.request_bg_image_remove.emit)
        self.combo_layer.currentIndexChanged.connect(self._dispatch_visual_update)
        self.slider_alpha.valueChanged.connect(self._dispatch_visual_update)
        self.slider_blur.valueChanged.connect(self._dispatch_visual_update)
        
        # Controles de Trilha Sonora
        self.btn_music_sel.clicked.connect(self._on_choose_music_clicked)
        self.btn_music_stop.clicked.connect(self.bus.request_music_remove.emit)
        self.btn_next.clicked.connect(self.bus.request_music_next.emit)
        self.btn_prev.clicked.connect(self.bus.request_music_prev.emit)
        self.btn_play_pause.clicked.connect(self.toggle_play_pause)
        
        # Sliders e Áudio
        self.slider_music_vol.valueChanged.connect(self._dispatch_audio_update)
        self.check_mute.stateChanged.connect(self._dispatch_audio_update)
        self.check_loop.stateChanged.connect(self._dispatch_audio_update)
        self.pos_combo.currentTextChanged.connect(self._on_toast_position_changed)
        
        # Toast Reações
        self.toast.btn_play.clicked.connect(self.toggle_play_pause)
        self.toast.btn_next.clicked.connect(self.bus.request_music_next.emit)

        # Sinais Reversos do Manager
        self.bus.bg_visual_changed.connect(self._on_visual_changed)
        self.bus.bg_music_changed.connect(self._on_music_changed)
        
        # Escuta o estado do Player de fundo
        self.bus.bg_player_position_updated.connect(self._on_player_position_changed)
        self.bus.bg_player_duration_updated.connect(lambda duration: self.slider_progress.setRange(0, duration))
        self.bus.bg_player_metadata_updated.connect(self._lazy_metadata_update)
        self.bus.bg_player_state_changed.connect(self._on_player_state_changed)
        
        # Envia a navegação na barra de tempo pro player
        self.slider_progress.sliderMoved.connect(self.bus.request_bg_player_set_position.emit)

    def _dispatch_visual_update(self):
        self.bus.request_bg_visual_update.emit({
            "bg_opacity": self.slider_alpha.value(),
            "bg_blur": self.slider_blur.value(),
            "bg_layer_level": self.combo_layer.currentIndex()
        })

    def _dispatch_audio_update(self):
        self.bus.request_bg_audio_update.emit({
            "volume": self.slider_music_vol.value(),
            "muted": self.check_mute.isChecked(),
            "loop": self.check_loop.isChecked()
        })

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
        self.lbl_music_info.setText(f"🎶 {title}")
        self.trigger_toast_notification()

    def _lazy_metadata_update(self, title):
        if title:
            self.lbl_music_info.setText(f"🎶 {title}")
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
        target_pos = pos_map.get(self.pos_combo.currentText(), "bottom_right")
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