import os
import glob
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                             QFileDialog, QHBoxLayout, QComboBox, 
                             QFrame, QCheckBox, QGroupBox, QScrollArea, QStyle, QStyleOptionSlider,
                             QGraphicsOpacityEffect)
from PySide6.QtCore import Qt, QSize, QTime, QPropertyAnimation, QTimer
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtMultimedia import QMediaMetaData, QMediaPlayer

from ui.tabs.background_tab_component.music_toast import MusicToast
from ui.widgets.labeled_slider import LabeledSlider
from ui.styles.theme import Theme
from core.utils import validate_path

# --- CLASSE AUXILIAR DE SLIDER ---
from PySide6.QtWidgets import QSlider
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


# --- ABA PRINCIPAL ---
class BackgroundTab(QWidget):
    def __init__(self, config_manager, bg_window):
        super().__init__()
        self.cfg = config_manager
        self.bg_window = bg_window
        
        # Instancia a notificação com o bg_window como parent
        self.toast = MusicToast(self.bg_window)
        # Conecta os botões da notificação
        self.toast.btn_play.clicked.connect(self.toggle_play_pause)
        self.toast.btn_next.clicked.connect(self.play_next_in_folder)
        
        self.playlist = []
        self.current_index = -1
        
        self._ensure_config_keys()
        self.setStyleSheet(Theme.MAIN_TAB_STYLE + Theme.GROUP_BOX + Theme.BUTTON_BASE)
        self.init_ui()
        self.setup_audio_connections()
        self._load_initial_playlist()

    def _ensure_config_keys(self):
        defaults = {
            "bg_path": "", "bg_opacity": 100, "bg_blur": 0, "bg_layer_level": 0,
            "bg_music_path": "", "bg_music_vol": 50, "bg_music_muted": False, "bg_music_loop": True
        }
        for key, value in defaults.items():
            self.cfg.data.setdefault(key, value)
            
        # Garante a key de posição no sistema
        self.cfg.data.setdefault("system", {}).setdefault("toast_position", "Canto Inferior Direito")

    def _load_initial_playlist(self):
        p = self.cfg.data.get("bg_music_path", "")
        if p and os.path.exists(p):
            folder = os.path.dirname(p)
            self.playlist = glob.glob(os.path.join(folder, "*.mp3")) + glob.glob(os.path.join(folder, "*.wav"))
            self.playlist.sort()
            if p in self.playlist:
                self.current_index = self.playlist.index(p)

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
        self.btn_sel.clicked.connect(self.choose_bg)
        
        self.btn_rem = QPushButton("🗑️")
        self.btn_rem.setStyleSheet(Theme.BUTTON_DANGER)
        self.btn_rem.setFixedWidth(40)
        self.btn_rem.clicked.connect(self.remove_bg)
        
        bg_btn_row.addWidget(self.btn_sel)
        bg_btn_row.addWidget(self.btn_rem)
        bg_layout.addLayout(bg_btn_row)

        render_frame = QFrame()
        render_frame.setStyleSheet("QFrame { border-top: 1px solid #30363d; margin-top: 10px; padding-top: 10px; }")
        render_lay = QVBoxLayout(render_frame)
        
        render_lay.addWidget(QLabel("Profundidade da Camada:"))
        self.combo_layer = QComboBox()
        self.combo_layer.addItems(["⬇️ Fundo (Atrás do Avatar)", "🟦 Normal", "⬆️ Sobrepor (Frente do Avatar)"])
        self.combo_layer.setCurrentIndex(self.cfg.data["bg_layer_level"])
        self.combo_layer.currentIndexChanged.connect(self.update_settings)
        render_lay.addWidget(self.combo_layer)

        # --- APLICAÇÃO DO LABELEDSLIDER ---
        self.slider_alpha = LabeledSlider("Nível de Opacidade:", min_val=0, max_val=100, default_val=self.cfg.data.get("bg_opacity", 100), value_format="{v}%")
        self.slider_alpha.valueChanged.connect(self.update_settings)
        render_lay.addWidget(self.slider_alpha)

        self.slider_blur = LabeledSlider("Intensidade do Desfoque:", min_val=0, max_val=50, default_val=self.cfg.data.get("bg_blur", 0), value_format="{v} px")
        self.slider_blur.valueChanged.connect(self.update_settings)
        render_lay.addWidget(self.slider_blur)
        
        bg_layout.addWidget(render_frame)
        layout.addWidget(bg_group)

        # ==========================================
        # 2. TRILHA SONORA E NOTIFICAÇÃO (BGM)
        # ==========================================
        audio_group = QGroupBox("🎵 TRILHA SONORA E NOTIFICAÇÃO")
        audio_layout = QVBoxLayout(audio_group)
        
        # Controle de Posição da Notificação
        pos_row = QHBoxLayout()
        pos_row.addWidget(QLabel("Posição da Notificação (Toast):"))
        self.pos_combo = QComboBox()
        self.pos_combo.addItems(["Canto Inferior Direito", "Canto Superior Direito", "Canto Inferior Esquerdo", "Canto Superior Esquerdo"])
        
        saved_pos = self.cfg.data.get("system", {}).get("toast_position", "Canto Inferior Direito")
        self.pos_combo.setCurrentText(saved_pos)
        self.pos_combo.currentTextChanged.connect(self.update_toast_position)
        
        pos_row.addWidget(self.pos_combo)
        audio_layout.addLayout(pos_row)
        
        # Info da Música
        self.lbl_music_info = QLabel("Nenhuma trilha")
        self.lbl_music_info.setStyleSheet(Theme.MUSIC_INFO)
        self.lbl_music_info.setWordWrap(True)
        audio_layout.addWidget(self.lbl_music_info)

        self.slider_progress = ClickableSlider(Qt.Horizontal)
        self.slider_progress.setStyleSheet(Theme.PROGRESS_SLIDER)
        self.slider_progress.sliderMoved.connect(self.seek_music)
        audio_layout.addWidget(self.slider_progress)

        self.lbl_time = QLabel("00:00 / 00:00")
        self.lbl_time.setAlignment(Qt.AlignRight)
        self.lbl_time.setStyleSheet(Theme.TIME_LABEL)
        audio_layout.addWidget(self.lbl_time)

        music_nav_row = QHBoxLayout()
        self.btn_prev = QPushButton("⏮️")
        self.btn_prev.setFixedWidth(45)
        self.btn_prev.clicked.connect(self.play_prev_in_folder)
        
        self.btn_play_pause = QPushButton("⏯️")
        self.btn_play_pause.setFixedWidth(60)
        self.btn_play_pause.clicked.connect(self.toggle_play_pause)
        
        self.btn_next = QPushButton("⏭️")
        self.btn_next.setFixedWidth(45)
        self.btn_next.clicked.connect(self.play_next_in_folder)
        
        music_nav_row.addStretch()
        music_nav_row.addWidget(self.btn_prev)
        music_nav_row.addWidget(self.btn_play_pause)
        music_nav_row.addWidget(self.btn_next)
        music_nav_row.addStretch()
        audio_layout.addLayout(music_nav_row)

        music_ctrl_row = QHBoxLayout()
        self.check_loop = QCheckBox("🔂 Loop Automático")
        self.check_loop.setChecked(self.cfg.data["bg_music_loop"])
        self.check_loop.stateChanged.connect(self.update_settings)
        music_ctrl_row.addWidget(self.check_loop)
        music_ctrl_row.addStretch()
        audio_layout.addLayout(music_ctrl_row)

        music_actions = QHBoxLayout()
        self.btn_music_sel = QPushButton("🎼 ESCOLHER MÚSICA")
        self.btn_music_sel.clicked.connect(self.choose_music)
        self.btn_music_stop = QPushButton("🛑 PARAR")
        self.btn_music_stop.clicked.connect(self.remove_music)
        music_actions.addWidget(self.btn_music_sel)
        music_actions.addWidget(self.btn_music_stop)
        audio_layout.addLayout(music_actions)

        vol_row = QHBoxLayout()
        
        # --- APLICAÇÃO DO LABELEDSLIDER ---
        self.slider_music_vol = LabeledSlider("Volume Principal:", min_val=0, max_val=100, default_val=self.cfg.data.get("bg_music_vol", 50), value_format="{v}%")
        self.slider_music_vol.valueChanged.connect(self.update_settings)
        
        self.check_mute = QCheckBox("🔇 Mudo")
        self.check_mute.setChecked(self.cfg.data["bg_music_muted"])
        self.check_mute.stateChanged.connect(self.update_settings)
        
        vol_row.addWidget(self.slider_music_vol, stretch=1)
        vol_row.addWidget(self.check_mute)
        audio_layout.addLayout(vol_row)
        
        layout.addWidget(audio_group)

        scroll.setWidget(container)
        layout_principal.addWidget(scroll)

        self.update_settings()

    def update_toast_position(self, text):
        self.cfg.data.setdefault("system", {})["toast_position"] = text
        self.cfg.save()
        self.trigger_toast_notification()

    def update_settings(self, _=None): # O parâmetro '_' ignora o valor recebido do slider
        bg_config = {
            "path": self.cfg.data["bg_path"],
            "width": self.bg_window.width(),
            "height": self.bg_window.height(),
            "opacity": self.slider_alpha.value(),
            "blur": self.slider_blur.value(),
            "audio_path": self.cfg.data["bg_music_path"],
            "volume": self.slider_music_vol.value(),
            "muted": self.check_mute.isChecked(),
            "loop": self.check_loop.isChecked()
        }

        self.cfg.data.update({
            "bg_opacity": bg_config["opacity"],
            "bg_blur": bg_config["blur"],
            "bg_layer_level": self.combo_layer.currentIndex(),
            "bg_music_vol": bg_config["volume"],
            "bg_music_muted": bg_config["muted"],
            "bg_music_loop": bg_config["loop"]
        })
        self.cfg.save()

        self.bg_window.set_layer_level(self.combo_layer.currentIndex())
        self.bg_window.update_background(bg_config) 
        self._update_local_preview(bg_config["path"])

    def _update_local_preview(self, path):
        if validate_path(path):
            pix = QPixmap(path)
            self.preview_label.setPixmap(pix.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.preview_label.setText("Sem Fundo")
            self.preview_label.setPixmap(QPixmap())

    def setup_audio_connections(self):
        player = self.bg_window.audio.player
        player.positionChanged.connect(self.update_position)
        player.durationChanged.connect(self.update_duration)
        player.metaDataChanged.connect(self._lazy_metadata_update)

    def update_position(self, pos):
        if not self.slider_progress.isSliderDown():
            self.slider_progress.setValue(pos)
        curr = QTime(0, 0).addMSecs(pos).toString("mm:ss")
        total = QTime(0, 0).addMSecs(self.bg_window.audio.player.duration()).toString("mm:ss")
        self.lbl_time.setText(f"{curr} / {total}")

    def seek_music(self, position):
        if hasattr(self.bg_window, 'audio') and self.bg_window.audio.player:
            self.bg_window.audio.player.setPosition(position)

    def update_duration(self, dur):
        self.slider_progress.setRange(0, dur)

    def extract_cover_art(self, file_path):
        folder = os.path.dirname(file_path)
        for ext in ['jpg', 'png', 'jpeg']:
            for name in ['cover', 'folder', 'front', 'art']:
                img_path = os.path.join(folder, f"{name}.{ext}")
                if os.path.exists(img_path):
                    return QPixmap(img_path)
        return None

    def trigger_toast_notification(self):
        current_path = self.cfg.data.get("bg_music_path", "")
        if not current_path: return
        
        filename = os.path.basename(current_path)
        title = filename.replace(".wav", "").replace(".mp3", "")
        artist = "Ficheiro Local"
        
        pixmap = self.extract_cover_art(current_path)
        
        pos_text = self.cfg.data.get("system", {}).get("toast_position", "Canto Inferior Direito")
        pos_map = {
            "Canto Inferior Direito": "bottom_right",
            "Canto Superior Direito": "top_right",
            "Canto Inferior Esquerdo": "bottom_left",
            "Canto Superior Esquerdo": "top_left"
        }
        target_pos = pos_map.get(pos_text, "bottom_right")
        
        self.lbl_music_info.setText(f"🎶 {title}")
        self.toast.update_info(title=title, artist=artist, cover_pixmap=pixmap)
        self.toast.show_toast(position_name=target_pos)

    def _lazy_metadata_update(self):
        meta = self.bg_window.audio.player.metaData()
        title = meta.value(QMediaMetaData.Key.Title)
        
        if title:
            self.lbl_music_info.setText(f"🎶 {title}")
            self.toast.lbl_title.setText(title[:25] + "..." if len(title) > 25 else title)

    def toggle_play_pause(self):
        player = self.bg_window.audio.player
        if player.playbackState() == QMediaPlayer.PlayingState:
            player.pause()
            self.toast.btn_play.setText("▶️")
            self.btn_play_pause.setText("▶️")
        else:
            player.play()
            self.toast.btn_play.setText("⏸️")
            self.btn_play_pause.setText("⏸️")

    def choose_music(self):
        p, _ = QFileDialog.getOpenFileName(self, "Selecionar BGM", "", "Áudio (*.mp3 *.wav *.ogg)")
        if p:
            self.cfg.data["bg_music_path"] = p
            folder = os.path.dirname(p)
            self.playlist = glob.glob(os.path.join(folder, "*.mp3")) + glob.glob(os.path.join(folder, "*.wav"))
            self.playlist.sort()
            if p in self.playlist:
                self.current_index = self.playlist.index(p)
            self.update_settings()
            self.trigger_toast_notification() 

    def play_next_in_folder(self):
        if not self.playlist: return
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.cfg.data["bg_music_path"] = self.playlist[self.current_index]
        self.update_settings()
        self.trigger_toast_notification() 

    def play_prev_in_folder(self):
        if not self.playlist: return
        self.current_index = (self.current_index - 1) % len(self.playlist)
        self.cfg.data["bg_music_path"] = self.playlist[self.current_index]
        self.update_settings()
        self.trigger_toast_notification() 

    def remove_music(self):
        self.cfg.data["bg_music_path"] = ""
        self.update_settings()
        self.lbl_music_info.setText("Nenhuma trilha")
        self.toast.hide_toast()

    def choose_bg(self):
        p, _ = QFileDialog.getOpenFileName(self, "Escolher Fundo", "", "Mídia (*.png *.jpg *.gif)")
        if p:
            self.cfg.data["bg_path"] = p
            self.update_settings()

    def remove_bg(self):
        self.cfg.data["bg_path"] = ""
        self.update_settings()