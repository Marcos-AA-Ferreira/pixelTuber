import os
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog
from PySide6.QtCore import Qt, QUrl, QTimer, Signal
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

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
        self.setStyleSheet("""
            #AudioGroup { 
                background: #1e1e1e; 
                border-radius: 10px; 
                padding: 15px; 
                border: 1px solid #333; 
            }
            QLabel { color: #888; font-size: 11px; font-weight: bold; }
            QPushButton { 
                padding: 8px 15px; 
                border-radius: 6px; 
                background: #2d2d2d; 
                color: #ddd; 
                border: 1px solid #444; 
                font-size: 11px;
            }
            QPushButton:hover { background: #3d3d3d; border-color: #555; }
        """)
        
        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        
        header = QHBoxLayout()
        header.addWidget(QLabel("🎚️ CONTROLO DE ÁUDIO"))
        header.addStretch()
        lay.addLayout(header)
        
        row = QHBoxLayout()
        self.btn_a = QPushButton("📂 SELECIONAR FICHEIRO")
        self.btn_a.clicked.connect(self.sel_a)
        
        self.btn_preview = QPushButton("▶️ OUVIR SELEÇÃO")
        self.btn_preview.clicked.connect(self.preview_cut)
        self.btn_preview.setEnabled(False) 
        
        row.addWidget(self.btn_a)
        row.addWidget(self.btn_preview)
        lay.addLayout(row)

        self.trimmer = AudioTrimmer()
        self.trimmer.valuesChanged.connect(self.update_times)
        lay.addWidget(self.trimmer)

    def sel_a(self):
        p, _ = QFileDialog.getOpenFileName(self, "Abrir Áudio", "", "Som (*.mp3 *.wav *.ogg)")
        if p:
            self.pending_load = None # Seleção manual, resetamos carregamento pendente
            self._load_file(p)

    def _load_file(self, p):
        """Lógica interna para carregar o arquivo e atualizar a UI."""
        self.path_a = p
        self.btn_a.setText(f"✅ {os.path.basename(p)[:20]}...")
        self.btn_a.setStyleSheet("background: #1b4d2e; color: #85e89d; border-color: #238636;")
        
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
        self.btn_a.setText("📂 SELECIONAR FICHEIRO")
        self.btn_a.setStyleSheet("")
        self.btn_preview.setEnabled(False)
        self.trimmer.set_duration(0)