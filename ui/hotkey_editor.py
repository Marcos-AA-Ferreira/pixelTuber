from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt
import keyboard

class HotkeyEditor(QWidget):
    def __init__(self, config_manager, hotkey_manager):
        super().__init__()
        self.cfg = config_manager
        self.hk_manager = hotkey_manager
        self.is_recording = None # Guarda qual atalho estamos gravando

        self.setWindowTitle("Configurar Teclas de Atalho")
        self.resize(350, 200)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Clique no botão e pressione a nova tecla:</b>"))

        # Atalho: Travar Posição
        self.btn_lock = QPushButton()
        self.btn_lock.clicked.connect(lambda: self.start_recording("toggle_lock"))
        
        # Atalho: Próximo Personagem/Set
        self.btn_next = QPushButton()
        self.btn_next.clicked.connect(lambda: self.start_recording("next_set"))

        layout.addLayout(self._create_row("Travar Avatar:", self.btn_lock))
        layout.addLayout(self._create_row("Próximo Sprite:", self.btn_next))

        self.btn_next_music = QPushButton()
        self.btn_next_music.clicked.connect(lambda: self.start_recording("next_music"))

        self.btn_prev_music = QPushButton()
        self.btn_prev_music.clicked.connect(lambda: self.start_recording("prev_music"))

        layout.addLayout(self._create_row("Próxima Música:", self.btn_next_music))
        layout.addLayout(self._create_row("Música Anterior:", self.btn_prev_music))
        
        self.refresh_labels()

    def _create_row(self, text, btn):
        row = QHBoxLayout()
        row.addWidget(QLabel(text))
        row.addWidget(btn)
        return row

    def refresh_labels(self):
        hks = self.cfg.data.get("hotkeys", {})
        self.btn_lock.setText(hks.get("toggle_lock", "Não definido").upper())
        self.btn_next.setText(hks.get("next_set", "Não definido").upper())
        self.btn_next_music.setText(hks.get("next_music", "Não definido").upper())
        self.btn_prev_music.setText(hks.get("prev_music", "Não definido").upper())

    def start_recording(self, key_type):
        self.is_recording = key_type
    
        # Altera APENAS o botão correspondente à ação selecionada
        if key_type == "toggle_lock":
            self.btn_lock.setText("Pressione uma tecla...")
        elif key_type == "next_set":
            self.btn_next.setText("Pressione uma tecla...")
        elif key_type == "next_music":
            self.btn_next_music.setText("Pressione uma tecla...")
        elif key_type == "prev_music":
            self.btn_prev_music.setText("Pressione uma tecla...")

    # --- VEJA AS MUDANÇAS EXATAS EXECUTADAS NESTE MÉTODO ABAIXO ---
    def keyPressEvent(self, event):
        if self.is_recording:
            # Captura a tecla pressionada usando o keyboard
            new_key = keyboard.read_hotkey(suppress=False)
            
            # 1. Proteção com setdefault (evita crash se o JSON estiver vazio)
            self.cfg.data.setdefault("hotkeys", {})[self.is_recording] = new_key
            
            # 2. Persistência imediata (grava a alteração no disco rígido)
            self.cfg.save() 
            
            # 3. Recarrega os listeners no HotkeyManager para aplicar a nova tecla na hora
            if hasattr(self.hk_manager, 'load_hotkeys'):
                self.hk_manager.load_hotkeys()
            else:
                self.hk_manager.setup_defaults()
            
            # Limpa o estado de gravação e atualiza os textos dos botões
            self.is_recording = None
            self.refresh_labels()