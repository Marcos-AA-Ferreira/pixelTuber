import os
import glob
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                             QFileDialog, QHBoxLayout, QSlider, QComboBox, 
                             QFrame, QCheckBox, QGroupBox, QScrollArea, QStyle, QStyleOptionSlider)
from PySide6.QtCore import Qt, QSize, QTime
from PySide6.QtGui import QPixmap
from PySide6.QtMultimedia import QMediaMetaData, QMediaPlayer

from ui.styles.theme import Theme
from core.utils import validate_path

# Classe auxiliar para permitir o clique direto na barra de progresso
class ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            sr = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
            
            if not sr.contains(event.pos()):
                new_val = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), event.pos().x(), self.width())
                self.setValue(new_val)
                self.sliderMoved.emit(new_val) # Dispara o sinal de seek
        super().mousePressEvent(event)

class BackgroundTab(QWidget):
    def __init__(self, config_manager, bg_window):
        super().__init__()
        self.cfg = config_manager
        self.bg_window = bg_window
        
        # Estado Interno da Playlist
        self.playlist = []
        self.current_index = -1
        
        # 1. Garantir chaves de configuração (Defaults)
        self._ensure_config_keys()
            
        # 2. Aplicar Estilo Geral
        self.setStyleSheet(Theme.MAIN_TAB_STYLE + Theme.GROUP_BOX + 
                           Theme.BUTTON_BASE)
        
        # 3. Construir Interface
        self.init_ui()
        
        # 4. Conectar Sinais de Áudio
        self.setup_audio_connections()
        
        # 5. Carregar playlist inicial se houver música salva
        self._load_initial_playlist()

    def _ensure_config_keys(self):
        defaults = {
            "bg_path": "", "bg_opacity": 100, "bg_blur": 0, "bg_layer_level": 0,
            "bg_music_path": "", "bg_music_vol": 50, "bg_music_muted": False, "bg_music_loop": True
        }
        for key, value in defaults.items():
            self.cfg.data.setdefault(key, value)

    def _load_initial_playlist(self):
        """Carrega a lista de músicas da pasta do arquivo atual."""
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
        layout.setSpacing(15)

        # --- SEÇÃO 1: VISUAL DO FUNDO ---
        bg_group = QGroupBox("🖼️ AMBIENTE VISUAL")
        bg_layout = QVBoxLayout(bg_group)
        
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
        self.btn_sel = QPushButton("🖼️ ESCOLHER IMAGEM")
        self.btn_sel.setStyleSheet(Theme.BUTTON_PRIMARY)
        self.btn_sel.clicked.connect(self.choose_bg)
        
        self.btn_rem = QPushButton("🗑️")
        self.btn_rem.setStyleSheet(Theme.BUTTON_DANGER)
        self.btn_rem.setFixedWidth(40)
        self.btn_rem.clicked.connect(self.remove_bg)
        
        bg_btn_row.addWidget(self.btn_sel)
        bg_btn_row.addWidget(self.btn_rem)
        bg_layout.addLayout(bg_btn_row)
        layout.addWidget(bg_group)

        # --- SEÇÃO 2: TRILHA SONORA (BGM) ---
        audio_group = QGroupBox("🎵 TRILHA SONORA")
        audio_layout = QVBoxLayout(audio_group)
        
        self.lbl_music_info = QLabel("Nenhuma trilha")
        self.lbl_music_info.setStyleSheet(Theme.MUSIC_INFO)
        self.lbl_music_info.setWordWrap(True)
        audio_layout.addWidget(self.lbl_music_info)

        # Alterado para usar o ClickableSlider
        self.slider_progress = ClickableSlider(Qt.Horizontal)
        self.slider_progress.setStyleSheet(Theme.PROGRESS_SLIDER)
        self.slider_progress.sliderMoved.connect(self.seek_music)
        audio_layout.addWidget(self.slider_progress)

        self.lbl_time = QLabel("00:00 / 00:00")
        self.lbl_time.setAlignment(Qt.AlignRight)
        self.lbl_time.setStyleSheet(Theme.TIME_LABEL)
        audio_layout.addWidget(self.lbl_time)

        # BOTÕES DE CONTROLE (Anterior, Play, Próximo)
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
        self.check_loop = QCheckBox("🔂 LOOP")
        self.check_loop.setChecked(self.cfg.data["bg_music_loop"])
        self.check_loop.stateChanged.connect(self.update_settings)
        
        music_ctrl_row.addWidget(self.check_loop)
        music_ctrl_row.addStretch()
        audio_layout.addLayout(music_ctrl_row)

        music_actions = QHBoxLayout()
        self.btn_music_sel = QPushButton("🎼 SELECIONAR")
        self.btn_music_sel.clicked.connect(self.choose_music)
        self.btn_music_stop = QPushButton("🛑 PARAR")
        self.btn_music_stop.clicked.connect(self.remove_music)
        music_actions.addWidget(self.btn_music_sel)
        music_actions.addWidget(self.btn_music_stop)
        audio_layout.addLayout(music_actions)

        vol_row = QHBoxLayout()
        self.slider_music_vol = QSlider(Qt.Horizontal)
        self.slider_music_vol.setRange(0, 100)
        self.slider_music_vol.setValue(self.cfg.data["bg_music_vol"])
        self.slider_music_vol.valueChanged.connect(self.update_settings)
        
        self.check_mute = QCheckBox("🔇")
        self.check_mute.setChecked(self.cfg.data["bg_music_muted"])
        self.check_mute.stateChanged.connect(self.update_settings)
        
        vol_row.addWidget(QLabel("VOL:"))
        vol_row.addWidget(self.slider_music_vol)
        vol_row.addWidget(self.check_mute)
        audio_layout.addLayout(vol_row)
        layout.addWidget(audio_group)

        # --- SEÇÃO 3: RENDERIZAÇÃO E CAMADAS ---
        render_group = QGroupBox("⚙️ RENDERIZAÇÃO")
        render_layout = QVBoxLayout(render_group)
        
        render_layout.addWidget(QLabel("Nível da Camada:"))
        self.combo_layer = QComboBox()
        self.combo_layer.addItems(["⬇️ Fundo (Atrás)", "🟦 Normal", "⬆️ Sobrepor (Frente)"])
        self.combo_layer.setCurrentIndex(self.cfg.data["bg_layer_level"])
        self.combo_layer.currentIndexChanged.connect(self.update_settings)
        render_layout.addWidget(self.combo_layer)

        self.slider_alpha = self.create_slider(0, 100, "bg_opacity", 100, render_layout, "Opacidade:")
        self.slider_blur = self.create_slider(0, 50, "bg_blur", 0, render_layout, "Nível de Desfoque:")
        layout.addWidget(render_group)

        scroll.setWidget(container)
        layout_principal.addWidget(scroll)

        # Inicialização Final
        self.update_settings()

    def update_settings(self):
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
        player.metaDataChanged.connect(self.update_metadata)

    def update_position(self, pos):
        if not self.slider_progress.isSliderDown():
            self.slider_progress.setValue(pos)
        curr = QTime(0, 0).addMSecs(pos).toString("mm:ss")
        total = QTime(0, 0).addMSecs(self.bg_window.audio.player.duration()).toString("mm:ss")
        self.lbl_time.setText(f"{curr} / {total}")

    def update_duration(self, dur):
        self.slider_progress.setRange(0, dur)

    def seek_music(self, pos):
        self.bg_window.audio.player.setPosition(pos)

    def update_metadata(self):
        meta = self.bg_window.audio.player.metaData()
        title = meta.value(QMediaMetaData.Key.Title)
        if title:
            self.lbl_music_info.setText(f"🎶 {title}")
        else:
            fname = os.path.basename(self.cfg.data.get("bg_music_path", ""))
            self.lbl_music_info.setText(f"📄 {fname}" if fname else "Nenhuma música")

    def toggle_play_pause(self):
        player = self.bg_window.audio.player
        if player.playbackState() == QMediaPlayer.PlayingState:
            player.pause()
        else:
            player.play()

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

    def play_next_in_folder(self):
        if not self.playlist: return
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.cfg.data["bg_music_path"] = self.playlist[self.current_index]
        self.update_settings()

    def play_prev_in_folder(self):
        if not self.playlist: return
        self.current_index = (self.current_index - 1) % len(self.playlist)
        self.cfg.data["bg_music_path"] = self.playlist[self.current_index]
        self.update_settings()

    def remove_music(self):
        self.cfg.data["bg_music_path"] = ""
        self.update_settings()

    def choose_bg(self):
        p, _ = QFileDialog.getOpenFileName(self, "Escolher Fundo", "", "Mídia (*.png *.jpg *.gif)")
        if p:
            self.cfg.data["bg_path"] = p
            self.update_settings()

    def remove_bg(self):
        self.cfg.data["bg_path"] = ""
        self.update_settings()

    def create_slider(self, min_v, max_v, key, default, layout, label):
        layout.addWidget(QLabel(label))
        s = QSlider(Qt.Horizontal)
        s.setRange(min_v, max_v)
        s.setValue(self.cfg.data.get(key, default))
        s.valueChanged.connect(self.update_settings)
        layout.addWidget(s)
        return s