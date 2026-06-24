# ui/widgets/labeled_slider.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSlider
from PySide6.QtCore import Qt, Signal

class LabeledSlider(QWidget):
    # Agora o sinal emite diretamente o valor final (em float ou int)
    valueChanged = Signal(float)

    def __init__(self, label_text, min_val=0.0, max_val=100.0, default_val=50.0, divider=1.0, value_format="{v}", parent=None):
        super().__init__(parent)
        self.divider = float(divider)
        self.value_format = value_format
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Texto do Slider com largura fixa para alinhar perfeitamente
        self.lbl_title = QLabel(label_text)
        self.lbl_title.setMinimumWidth(180) 
        
        # 2. O Slider convertido para suportar precisão decimal
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(int(min_val * self.divider), int(max_val * self.divider))
        self.slider.setValue(int(default_val * self.divider))
        
        # 3. Texto do Valor formatado
        self.lbl_value = QLabel(self.value_format.format(v=default_val))
        self.lbl_value.setMinimumWidth(50) 
        self.lbl_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.slider.valueChanged.connect(self._on_value_changed)
        
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.slider, stretch=1)
        layout.addWidget(self.lbl_value)

    def _on_value_changed(self, raw_val):
        real_val = raw_val / self.divider
        self.lbl_value.setText(self.value_format.format(v=real_val))
        self.valueChanged.emit(real_val)

    def value(self):
        return self.slider.value() / self.divider

    def setValue(self, val):
        self.slider.setValue(int(val * self.divider))