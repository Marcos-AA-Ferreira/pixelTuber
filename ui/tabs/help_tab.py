from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea, 
                             QFrame, QGroupBox)
from PySide6.QtCore import Qt
from ui.styles.theme import Theme

class HelpTab(QWidget):
    def __init__(self):
        super().__init__()
        
        # Aplica o estilo unificado (usando apenas o que existe no seu Theme)
        self.setStyleSheet(Theme.MAIN_TAB_STYLE + Theme.GROUP_BOX)
        
        layout_principal = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)

        # --- CABEÇALHO ---
        header = QLabel("PIXELTUBER - GUIA OFICIAL")
        header.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {Theme.ACCENT}; margin-bottom: 10px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # --- SEÇÃO: LÓGICA DE ÁUDIO ---
        audio_group = QGroupBox("🎙️ LÓGICA DE ÁUDIO")
        audio_lay = QVBoxLayout(audio_group)
        
        # Trocado TEXT_SECONDARY por TEXT_MUTED para bater com sua classe Theme
        audio_text = (
            f"<p style='color: {Theme.TEXT_PRIMARY};'>A reação do avatar depende de como o som é processado:</p>"
            "<ul>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Modo Standard:</b> Troca o sprite instantaneamente com o volume. Ideal para reações rápidas.</li>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Modo Suavizado:</b> Mantém o sprite de 'fala' por alguns milissegundos extras, "
            "evitando oscilações bruscas em volumes instáveis.</li>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Thresholds:</b> Define os degraus de volume para as animações Baixa, Média e Alta.</li>"
            "</ul>"
        )
        audio_lbl = QLabel(audio_text)
        audio_lbl.setWordWrap(True)
        audio_lbl.setTextFormat(Qt.RichText)
        audio_lay.addWidget(audio_lbl)
        layout.addWidget(audio_group)

        # --- SEÇÃO: SISTEMA DE EFEITOS ---
        effects_group = QGroupBox("🚀 SISTEMA DE EFEITOS")
        eff_lay = QVBoxLayout(effects_group)
        
        eff_text = (
            f"<p style='color: {Theme.TEXT_PRIMARY};'>Use a aba de efeitos para dar vida à sua stream:</p>"
            "<ul>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Visual:</b> GIFs ou Imagens que aparecem sobre o avatar.</li>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Áudio:</b> Efeitos sonoros (SFX) disparados individualmente ou com visuais.</li>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Combos:</b> Dispara áudio e imagem ao mesmo tempo.</li>"
            "</ul>"
        )
        eff_lbl = QLabel(eff_text)
        eff_lbl.setWordWrap(True)
        eff_lbl.setTextFormat(Qt.RichText)
        eff_lay.addWidget(eff_lbl)
        layout.addWidget(effects_group)

        # --- SEÇÃO: COMANDOS ---
        cmd_group = QGroupBox("⌨️ COMANDOS E CONTROLE")
        cmd_lay = QVBoxLayout(cmd_group)
        
        cmd_text = (
            f"<p style='color: {Theme.TEXT_PRIMARY};'>Interações diretas com a janela do avatar:</p>"
            "<ul>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Clique e Arraste:</b> Move o avatar livremente pela tela.</li>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Shift + F:</b> Atalho padrão para Travar/Destravar a posição.</li>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Tecla M:</b> Alterna o modo Mudo rapidamente.</li>"
            "</ul>"
        )
        cmd_lbl = QLabel(cmd_text)
        cmd_lbl.setWordWrap(True)
        cmd_lbl.setTextFormat(Qt.RichText)
        cmd_lay.addWidget(cmd_lbl)
        layout.addWidget(cmd_group)

        layout.addStretch()
        scroll.setWidget(container)
        layout_principal.addWidget(scroll)