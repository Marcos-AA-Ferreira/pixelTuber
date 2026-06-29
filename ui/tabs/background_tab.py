# ui/tabs/background_tab.py
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                             QFileDialog, QHBoxLayout, QComboBox, 
                             QFrame, QCheckBox, QGroupBox, QScrollArea, QStyle, QStyleOptionSlider, QSlider)
from PySide6.QtCore import Qt, QTime
from PySide6.QtGui import QPixmap
from PySide6.QtMultimedia import QMediaMetaData, QMediaPlayer

from ui.tabs.background_tab_component.music_toast import MusicToast
from ui.widgets.labeled_slider import LabeledSlider
from ui.styles.theme import Theme
from core.utils import validate_path
from core.background_manager import BackgroundManager  # Importa o gerenciador

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
    def __init__(self, config_manager, bg_window):
        super().__init__()
        self.cfg = config_manager
        self.bg_window = bg_window
        
        # Instancia o Gerenciador de Lógica
        self.mgr = BackgroundManager(config_manager, bg_window)
        
        # Instancia a Notificação Flutuante
        self.toast = MusicToast(self.bg_window)
        
        self.setStyleSheet(Theme.MAIN_TAB_STYLE + Theme.GROUP_BOX + Theme.BUTTON_BASE)
        
        self.init_ui()
        self.connect_events_and_signals()
        
        # Sincroniza o estado inicial da UI disparando a atualização do gerenciador
        self.mgr._apply_background_to_window()

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
        """Centraliza todos os binds de botões e escutas de Sinais."""
        # --- UI Interações -> Repassa para o Gerenciador ---
        self.btn_sel.clicked.connect(self._on_choose_bg_clicked)
        self.btn_rem.clicked.connect(self.mgr.remove_background_image)
        
        # Sliders Visuais
        self.combo_layer.currentIndexChanged.connect(self._dispatch_visual_update)
        self.slider_alpha.valueChanged.connect(self._dispatch_visual_update)
        self.slider_blur.valueChanged.connect(self._dispatch_visual_update)
        
        # Controles de Trilha Sonora
        self.btn_music_sel.clicked.connect(self._on_choose_music_clicked)
        self.btn_music_stop.clicked.connect(self.mgr.remove_music)
        self.btn_next.clicked.connect(self.mgr.play_next)
        self.btn_prev.clicked.connect(self.mgr.play_prev)
        self.btn_play_pause.clicked.connect(self.toggle_play_pause)
        
        # Sliders de Áudio / Checkboxes
        self.slider_music_vol.valueChanged.connect(self._dispatch_audio_update)
        self.check_mute.stateChanged.connect(self._dispatch_audio_update)
        self.check_loop.stateChanged.connect(self._dispatch_audio_update)
        
        # Configurações de Posição do Toast
        self.pos_combo.currentTextChanged.connect(self._on_toast_position_changed)
        
        # Sincroniza botões do Toast de volta à ação
        self.toast.btn_play.clicked.connect(self.toggle_play_pause)
        self.toast.btn_next.clicked.connect(self.mgr.play_next)

        # --- Gerenciador -> Atualiza a UI (Escuta os Sinais) ---
        self.mgr.visualChanged.connect(self._on_visual_changed)
        self.mgr.musicChanged.connect(self._on_music_changed)
        
        # Conexões Nativas do Player de Áudio do Sistema
        if self.bg_window and hasattr(self.bg_window, 'audio') and self.bg_window.audio.player:
            player = self.bg_window.audio.player
            player.positionChanged.connect(self._on_player_position_changed)
            player.durationChanged.connect(lambda duration: self.slider_progress.setRange(0, duration))
            player.metaDataChanged.connect(self._lazy_metadata_update)
            self.slider_progress.sliderMoved.connect(player.setPosition)

    # --- SLOTS DE DISPACHO (UI -> MGR) ---
    
    def _dispatch_visual_update(self):
        self.mgr.update_visual_settings(
            opacity=self.slider_alpha.value(),
            blur=self.slider_blur.value(),
            layer_level=self.combo_layer.currentIndex()
        )

    def _dispatch_audio_update(self):
        self.mgr.update_audio_settings(
            volume=self.slider_music_vol.value(),
            muted=self.check_mute.isChecked(),
            loop=self.check_loop.isChecked()
        )

    def _on_choose_bg_clicked(self):
        p, _ = QFileDialog.getOpenFileName(self, "Escolher Fundo", "", "Mídia (*.png *.jpg *.gif)")
        if p: self.mgr.set_background_image(p)

    def _on_choose_music_clicked(self):
        p, _ = QFileDialog.getOpenFileName(self, "Selecionar BGM", "", "Áudio (*.mp3 *.wav *.ogg)")
        if p: self.mgr.set_music(p)

    def _on_toast_position_changed(self, text):
        self.cfg.data.setdefault("system", {})["toast_position"] = text
        self.cfg.save()
        self.trigger_toast_notification()

    # --- SLOTS DE ATUALIZAÇÃO DA UI (MGR -> UI) ---

    def _on_visual_changed(self, bg_config):
        """Atualiza estritamente os componentes visuais locais baseados no Model."""
        path = bg_config["path"]
        if validate_path(path):
            pix = QPixmap(path)
            self.preview_label.setPixmap(pix.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.preview_label.setText("Sem Fundo")
            self.preview_label.setPixmap(QPixmap())

    def _on_music_changed(self, path):
        """Reage à mudança de música atualizando textos e notificações."""
        if not path:
            self.lbl_music_info.setText("Nenhuma trilha")
            self.toast.hide_toast()
            return
            
        title = os.path.basename(path).replace(".wav", "").replace(".mp3", "")
        self.lbl_music_info.setText(f"🎶 {title}")
        self.trigger_toast_notification()

    def _on_player_position_changed(self, pos):
        if not self.slider_progress.isSliderDown():
            self.slider_progress.setValue(pos)
        
        duration = self.bg_window.audio.player.duration() if self.bg_window and hasattr(self.bg_window, 'audio') else 0
        curr = QTime(0, 0).addMSecs(pos).toString("mm:ss")
        total = QTime(0, 0).addMSecs(duration).toString("mm:ss")
        self.lbl_time.setText(f"{curr} / {total}")

    def _lazy_metadata_update(self):
        if self.bg_window and hasattr(self.bg_window, 'audio') and self.bg_window.audio.player:
            meta = self.bg_window.audio.player.metaData()
            title = meta.value(QMediaMetaData.Key.Title)
            if title:
                self.lbl_music_info.setText(f"🎶 {title}")
                self.toast.lbl_title.setText(title[:25] + "..." if len(title) > 25 else title)

    # --- INTERAÇÕES DIRETAS DO PLAYER ---

    def toggle_play_pause(self):
        if not (self.bg_window and hasattr(self.bg_window, 'audio') and self.bg_window.audio.player): return
        player = self.bg_window.audio.player
        
        if player.playbackState() == QMediaPlayer.PlayingState:
            player.pause()
            char = "▶️"
        else:
            player.play()
            char = "⏸️"
            
        self.toast.btn_play.setText(char)
        self.btn_play_pause.setText(char)

    def trigger_toast_notification(self):
        current_path = self.cfg.data.get("bg_music_path", "")
        if not current_path: return
        
        title = os.path.basename(current_path).replace(".wav", "").replace(".mp3", "")
        
        # Procura capa na pasta
        pixmap = None
        folder = os.path.dirname(current_path)
        for ext in ['jpg', 'png', 'jpeg']:
            for name in ['cover', 'folder', 'front', 'art']:
                img_path = os.path.join(folder, f"{name}.{ext}")
                if os.path.exists(img_path):
                    pixmap = QPixmap(img_path)
                    break
        
        pos_map = {
            "Canto Inferior Direito": "bottom_right", "Canto Superior Direito": "top_right",
            "Canto Inferior Esquerdo": "bottom_left", "Canto Superior Esquerdo": "top_left"
        }
        target_pos = pos_map.get(self.pos_combo.currentText(), "bottom_right")
        
        self.toast.update_info(title=title, artist="Ficheiro Local", cover_pixmap=pixmap)
        self.toast.show_toast(position_name=target_pos)

    def select_background_image(self):
        """Mapeamento externo legado."""
        self._on_choose_bg_clicked()