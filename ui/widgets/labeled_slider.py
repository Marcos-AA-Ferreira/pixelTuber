from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider
from PySide6.QtCore import Qt, Signal

class LabeledSlider(QWidget):
    """
    Widget padronizado para controles de faixa (Zoom, Volume, Ganho, etc.)
    Com suporte a marcadores de valor em tempo real e ticks de referência.
    """
    valueChanged = Signal(float)  # Emite o valor real (float ou int)

    def __init__(
        self,
        title: str,
        min_val: float,
        max_val: float,
        default_val: float,
        step: float = 1.0,
        unit: str = "",
        decimals: int = 0,
        ticks: list[tuple[str, float]] | None = None,
        parent: QWidget | None = None
    ):
        super().__init__(parent)
        self.setObjectName("LabeledSliderContainer")

        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.unit = unit
        self.decimals = decimals
        self.factor = 10 ** decimals  # Para converter float em int no QSlider

        # Layout Principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 8)
        layout.setSpacing(4)

        # 1. Cabeçalho: Título e Badge com Valor Atual (Marcador)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_title = QLabel(title)
        self.lbl_title.setObjectName("SliderTitleLabel")

        self.lbl_value_badge = QLabel()
        self.lbl_value_badge.setObjectName("SliderValueBadge")

        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_value_badge)
        layout.addLayout(header_layout)

        # 2. QSlider Estilizado
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setObjectName("CustomSlider")
        self.slider.setRange(int(min_val * self.factor), int(max_val * self.factor))
        self.slider.setSingleStep(int(step * self.factor))
        self.slider.setValue(int(default_val * self.factor))
        self.slider.setCursor(Qt.CursorShape.PointingHandCursor)

        self.slider.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.slider)

        # 3. Marcadores/Ticks numéricos abaixo da barra (Opcional)
        if ticks:
            ticks_layout = QHBoxLayout()
            ticks_layout.setContentsMargins(2, 0, 2, 0)
            
            for idx, (label, val) in enumerate(ticks):
                lbl_tick = QLabel(label)
                lbl_tick.setObjectName("SliderTickLabel")
                if idx == 0:
                    lbl_tick.setAlignment(Qt.AlignmentFlag.AlignLeft)
                elif idx == len(ticks) - 1:
                    lbl_tick.setAlignment(Qt.AlignmentFlag.AlignRight)
                else:
                    lbl_tick.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                ticks_layout.addWidget(lbl_tick, 1 if idx != 0 and idx != len(ticks)-1 else 0)
            
            layout.addLayout(ticks_layout)

        # Define valor inicial na badge
        self.update_badge(default_val)

    def _on_value_changed(self, raw_val: int):
        real_val = raw_val / self.factor
        self.update_badge(real_val)
        self.valueChanged.emit(real_val)

    def update_badge(self, val: float):
        if self.decimals == 0:
            formatted_val = f"{int(val)}{self.unit}"
        else:
            formatted_val = f"{val:.{self.decimals}f}{self.unit}"
            
        # Adiciona sinal '+' em ganhos positivos
        if "dB" in self.unit and val > 0:
            formatted_val = f"+{formatted_val}"

        self.lbl_value_badge.setText(formatted_val)

    def value(self) -> float:
        return self.slider.value() / self.factor

    def setValue(self, val: float):
        self.slider.setValue(int(val * self.factor))