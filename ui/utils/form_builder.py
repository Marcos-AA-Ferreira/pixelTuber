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

    def build_from_schema(self, schema_list, data_source, event_callback):
        """
        Constrói dinamicamente os widgets baseados em uma lista de dicionários (schema).
        
        :param schema_list: Lista de dicionários com as propriedades do widget.
        :param data_source: Dicionário atual das configurações OU Função Getter.
        :param event_callback: Função genérica para tratar alterações.
        """
        for field in schema_list:
            field_type = field.get("type")
            key = field.get("key")
            title = field.get("title", "")
            
            # 🚀 A CORREÇÃO ESTÁ AQUI: Verifica de forma inteligente o tipo da fonte de dados
            if callable(data_source):
                # Se for uma função (como no settings_tab), executa a função
                current_val = data_source(key)
            else:
                # Se for um dicionário (como no audio_tab), usa o .get()
                current_val = data_source.get(key)
                
            # Se não achou nada em nenhum dos dois casos, usa o default do schema
            if current_val is None:
                current_val = field.get("default")

            # Cria um callback isolado para evitar o problema de late binding em loops
            cb = lambda val, k=key: event_callback(k, val)

            if field_type == "slider":
                pass # Reservado caso use o QSlider nativo depois

            elif field_type == "custom_slider":
                from ui.widgets.labeled_slider import LabeledSlider
                slider = LabeledSlider(
                    title=title,
                    min_val=field.get("min_val", 0),
                    max_val=field.get("max_val", 100),
                    default_val=current_val,
                    step=field.get("step", 1),
                    unit=field.get("unit", ""),
                    decimals=field.get("decimals", 0),
                    ticks=field.get("ticks")
                )
                slider.valueChanged.connect(cb)
                self.add_custom_widget(slider)

            elif field_type == "switch":
                self.add_checkbox(title, bool(current_val), cb)

            elif field_type == "combobox":
                self.add_combobox(
                    label_text=title,
                    items=field.get("options", []),
                    current_text=current_val,
                    callback=cb,
                    extra_widget=field.get("extra_widget")
                )
                
            elif field_type == "lineedit":
                self.add_lineedit(title, current_val, field.get("placeholder", ""), cb)