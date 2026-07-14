import os
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog
from PySide6.QtCore import Qt, QUrl, QTimer, Signal
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from ui.widgets.file_picker import FilePickerWidget

# Tenta importar o novo trimmer minimalista
try:
    from .audio_trimmer import AudioTrimmer
except ImportError:
    from audio_trimmer import AudioTrimmer

class AudioSection(QFrame):
    duration_loaded = Signal(float)

    def __init__(self):
        super().__init__()
        self.path_a = ""
        self.val_start = 0.0
        self.val_end = 0.0
        self.pending_load = None # Armazena tempos de corte enquanto o arquivo carrega
        
        # --- CONFIGURAÇÃO DO PLAYER (PYSIDE6) ---
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(1.0) 
        
        self.meta_player = QMediaPlayer()
        self.meta_player.setAudioOutput(self.audio_output)
        self.meta_player.durationChanged.connect(self.on_meta_loaded)
        
        self.init_ui()

    def init_ui(self):
        self.setObjectName("AudioGroup")
        
        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        
        header = QHBoxLayout()
        header.addWidget(QLabel("🎚️ CONTROLO DE ÁUDIO"))
        header.addStretch()
        lay.addLayout(header)
        
        row = QHBoxLayout()
        self.file_picker = FilePickerWidget("SELECIONAR FICHEIRO", "Abrir Áudio", "Som (*.mp3 *.wav *.ogg)")
        self.file_picker.fileSelected.connect(self._on_audio_selected)
        
        self.btn_preview = QPushButton("▶️ OUVIR SELEÇÃO")
        self.btn_preview.clicked.connect(self.preview_cut)
        self.btn_preview.setEnabled(False) 
        
        row.addWidget(self.file_picker)
        row.addWidget(self.btn_preview)
        lay.addLayout(row)

        self.trimmer = AudioTrimmer()
        self.trimmer.valuesChanged.connect(self.update_times)
        lay.addWidget(self.trimmer)

    def _on_audio_selected(self, path):
        """Recebe o caminho do componente e avança com a lógica."""
        self.pending_load = None # Seleção manual, resetamos carregamento pendente
        self._load_file(path)

    def _load_file(self, p):
        """Lógica interna para carregar o arquivo e atualizar a UI."""
        self.path_a = p
        self.file_picker.set_path(p) # ✅ O widget cuida da estética do botão!

        file_url = QUrl.fromLocalFile(os.path.abspath(p))
        self.meta_player.setSource(file_url)

    # --- NOVO MÉTODO: FIX PARA O ATTRIBUTE ERROR ---
    def load_data(self, path, start, end):
        """Carrega os dados salvos de um efeito para edição."""
        if not path or not os.path.exists(path):
            self.reset()
            return

        # Guardamos os tempos para aplicar quando o sinal durationChanged disparar
        self.pending_load = (start, end)
        self._load_file(path)

    def on_meta_loaded(self, duration_ms):
        """Atualiza a barra quando o áudio termina de carregar ou é editado."""
        dur = duration_ms / 1000.0
        if dur > 0:
            self.trimmer.set_duration(dur)
            
            # Se for uma edição (load_data), usamos os valores salvos
            if self.pending_load:
                s, e = self.pending_load
                self.val_start = s
                # Proteção: se o áudio for menor que o salvo anteriormente
                self.val_end = e if e <= dur else dur
                # Sincroniza visualmente a barra (se o trimmer suportar set_values)
                if hasattr(self.trimmer, 'set_values'):
                    self.trimmer.set_values(self.val_start, self.val_end)
                self.pending_load = None
            else:
                # Se for um novo arquivo, começa do zero ao fim
                self.val_start = 0.0
                self.val_end = dur
            
            self.btn_preview.setEnabled(True)
            self.duration_loaded.emit(dur)

    def update_times(self, s, e):
        self.val_start, self.val_end = s, e

    def preview_cut(self):
        if not self.path_a: return
        if self.meta_player.playbackState() == QMediaPlayer.PlayingState:
            self.meta_player.stop()
        
        start_ms = int(self.val_start * 1000)
        self.meta_player.setPosition(start_ms)
        self.meta_player.play()
        
        duration_to_play_ms = int((self.val_end - self.val_start) * 1000)
        QTimer.singleShot(max(100, duration_to_play_ms), self.meta_player.stop)

    def get_data(self):
        return {
            "audio": self.path_a,
            "audio_start": round(self.val_start, 2),
            "audio_end": round(self.val_end, 2)
        }

    def reset(self):
        self.path_a = ""
        self.pending_load = None
        self.file_picker.set_path("")
        self.btn_preview.setEnabled(False)
        self.trimmer.set_duration(0)