# ui/utils/form_builder.py
from PySide6.QtWidgets import QLabel, QSlider, QComboBox, QCheckBox, QHBoxLayout, QLineEdit
from PySide6.QtCore import Qt

class FormBuilder:
    def __init__(self, parent_layout):
        """
        Recebe o layout principal (ex: QVBoxLayout) onde os controles serão adicionados.
        """
        self.parent_layout = parent_layout
        self.label_width = 150  # Mantém todos os textos perfeitamente alinhados

    def _add_row(self, label_text, widget):
        """Função interna para montar a linha com texto e widget."""
        row_layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setMinimumWidth(self.label_width)
        
        row_layout.addWidget(label)
        row_layout.addWidget(widget)
        self.parent_layout.addLayout(row_layout)

    def add_slider(self, label_text, min_val, max_val, current_val, callback):
        """Cria um slider, conecta a função e adiciona à tela."""
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(current_val)
        slider.valueChanged.connect(callback)
        
        self._add_row(label_text, slider)
        return slider

    def add_combobox(self, label_text, items, current_text, callback, extra_widget=None):
        """Cria um dropdown (combo), conecta a função e permite um widget extra ao lado."""
        combo = QComboBox()
        combo.addItems(items)
        combo.setCurrentText(current_text)
        combo.currentTextChanged.connect(callback)
        
        row_layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setMinimumWidth(self.label_width)
        
        row_layout.addWidget(label)
        
        # Se houver um botão extra, não esticamos o combo ao máximo
        if extra_widget:
            row_layout.addWidget(combo)
            row_layout.addWidget(extra_widget)
        else:
            row_layout.addWidget(combo, stretch=1)
            
        self.parent_layout.addLayout(row_layout)
        return combo

    def add_checkbox(self, label_text, is_checked, callback):
        """Cria uma caixa de seleção, conecta a função e adiciona à tela."""
        checkbox = QCheckBox(label_text)
        checkbox.setChecked(is_checked)
        checkbox.toggled.connect(callback)
        
        # Checkbox não precisa de um label separado
        self.parent_layout.addWidget(checkbox) 
        return checkbox

    def add_lineedit(self, label_text, current_text, placeholder, callback):
        """Cria um campo de texto, conecta a função e adiciona à tela."""
        edit = QLineEdit()
        edit.setFixedWidth(120)
        edit.setAlignment(Qt.AlignCenter)
        edit.setText(current_text)
        edit.setPlaceholderText(placeholder)
        edit.textChanged.connect(callback)
        
        self._add_row(label_text, edit)
        return edit

    def add_custom_widget(self, widget):
        """Adiciona um componente customizado (como o LabeledSlider) diretamente ao layout."""
        self.parent_layout.addWidget(widget)
        return widget