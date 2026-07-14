# ui/widgets/file_picker.py
import os
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFileDialog
from PySide6.QtCore import Signal

class FilePickerWidget(QWidget):
    # Sinal emitido sempre que um novo arquivo é escolhido com sucesso
    fileSelected = Signal(str)

    def __init__(self, button_text="SELECIONAR ARQUIVO", dialog_title="Selecionar Arquivo", file_filter="Todos (*.*)", parent=None):
        super().__init__(parent)
        self.dialog_title = dialog_title
        self.file_filter = file_filter
        self.current_path = ""

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.btn = QPushButton(f"📂 {button_text}")
        self.btn.clicked.connect(self.open_dialog)
        layout.addWidget(self.btn)

    def open_dialog(self):
        """Abre a janela nativa de seleção e avisa a interface se algo for escolhido."""
        path, _ = QFileDialog.getOpenFileName(self, self.dialog_title, "", self.file_filter)
        if path:
            self.set_path(path)
            self.fileSelected.emit(path)

    def set_path(self, path):
        """Atualiza a interface do botão de acordo com o arquivo selecionado (ou limpa se vazio)."""
        self.current_path = path
        if path:
            short_name = os.path.basename(path)[:15]
            self.btn.setText(f"✅ {short_name}...")
            self.btn.setStyleSheet("background: #1b4d2e; color: #85e89d; border-color: #238636;")
        else:
            # Reseta para o padrão se enviar string vazia
            text_original = self.btn.text().replace("✅ ", "").replace("...", "").strip()
            if "📂" not in text_original:
                 text_original = f"📂 {text_original}"
            self.btn.setText(text_original)
            self.btn.setStyleSheet("")

    def get_path(self):
        return self.current_path