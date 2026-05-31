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

    def start_recording(self, key_type):
        self.is_recording = key_type
        if key_type == "toggle_lock": self.btn_lock.setText("Pressione uma tecla...")
        else: self.btn_next.setText("Pressione uma tecla...")

    def keyPressEvent(self, event):
        if self.is_recording:
            # Captura a tecla pressionada usando o keyboard
            new_key = keyboard.read_hotkey(suppress=False)
            
            # Atualiza no config e no sistema
            self.cfg.data["hotkeys"][self.is_recording] = new_key
            self.hk_manager.setup_defaults() # Reinicia os listeners
            
            self.is_recording = None
            self.refresh_labels()