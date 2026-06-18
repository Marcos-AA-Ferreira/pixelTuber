from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea, 
                             QFrame, QGroupBox)
from PySide6.QtCore import Qt
from ui.styles.theme import Theme

class HelpTab(QWidget):
    def __init__(self):
        super().__init__()
        
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

        # --- SEÇÃO: INTEGRAÇÃO OBS E SISTEMA ---
        obs_group = QGroupBox("⚙️ INTEGRAÇÃO OBS E SISTEMA")
        obs_lay = QVBoxLayout(obs_group)
        
        obs_text = (
            f"<p style='color: {Theme.TEXT_PRIMARY};'>Configurações para otimizar sua experiência de transmissão:</p>"
            "<ul>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Fundo Chroma Key:</b> Se a captura transparente do OBS der problemas (bordas pretas ou fantasmas), altere o fundo do Avatar para 'Verde Chroma' e aplique o Filtro de Chroma Key diretamente no OBS.</li>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Limite de FPS:</b> Jogos pesados podem competir por CPU. Se o seu avatar travar, baixe o limite para 30 FPS. Se quiser máxima fluidez e tiver um PC forte, use 60 FPS ou 120 FPS.</li>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Bandeja do Sistema:</b> Ao ativar 'Minimizar para a Bandeja', fechar o painel não encerra o aplicativo. Ele continuará funcionando oculto perto do relógio do Windows. Dê um duplo clique no ícone para reabrir o painel.</li>"
            "</ul>"
        )
        obs_lbl = QLabel(obs_text)
        obs_lbl.setWordWrap(True)
        obs_lbl.setTextFormat(Qt.RichText)
        obs_lay.addWidget(obs_lbl)
        layout.addWidget(obs_group)

        # --- SEÇÃO: LÓGICA DE ÁUDIO ---
        audio_group = QGroupBox("🎙️ LÓGICA DE ÁUDIO")
        audio_lay = QVBoxLayout(audio_group)
        
        audio_text = (
            f"<p style='color: {Theme.TEXT_PRIMARY};'>A reação do avatar depende de como o som é processado:</p>"
            "<ul>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Modo Standard:</b> Troca o sprite instantaneamente com o volume. Ideal para reações rápidas.</li>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Modo Suavizado:</b> Mantém o sprite de 'fala' por alguns milissegundos extras, evitando oscilações bruscas.</li>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Thresholds:</b> Define os degraus de volume para as animações Baixa, Média e Alta.</li>"
            "</ul>"
        )
        audio_lbl = QLabel(audio_text)
        audio_lbl.setWordWrap(True)
        audio_lbl.setTextFormat(Qt.RichText)
        audio_lay.addWidget(audio_lbl)
        layout.addWidget(audio_group)

        # --- SEÇÃO: VISUALIZADOR DE ÁUDIO (ATUALIZADO) ---
        visualizer_group = QGroupBox("📊 INDICADORES DE ÁUDIO")
        visualizer_lay = QVBoxLayout(visualizer_group)
        
        visualizer_text = (
            f"<p style='color: {Theme.TEXT_PRIMARY};'>Equalizador gráfico em tempo real acoplado ao seu avatar:</p>"
            "<ul>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Estilo Clássico:</b> Barras de espectro tradicionais que sobem a partir da base conforme a intensidade da voz.</li>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Neon Simétrico:</b> As barras expandem-se a partir do centro, gerando um efeito espelhado e moderno.</li>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Onda Contínua:</b> Uma linha fluida e dinâmica que conecta as frequências sonoras.</li>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Pontos de Energia:</b> Partículas circulares que saltam e deixam um rastro suave conforme a intensidade da voz.</li>"
            "</ul>"
        )
        visualizer_lbl = QLabel(visualizer_text)
        visualizer_lbl.setWordWrap(True)
        visualizer_lbl.setTextFormat(Qt.RichText)
        visualizer_lay.addWidget(visualizer_lbl)
        layout.addWidget(visualizer_group)

        # --- SEÇÃO: ACESSÓRIOS (NOVO) ---
        acc_group = QGroupBox("🎩 ACESSÓRIOS E GUARDA-ROUPA")
        acc_lay = QVBoxLayout(acc_group)
        
        acc_text = (
            f"<p style='color: {Theme.TEXT_PRIMARY};'>Controlos avançados para personalizar o avatar:</p>"
            "<ul>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Z-Index (Profundidade):</b> Define se um item fica na frente ou atrás do avatar. Valores maiores ficam por cima, valores negativos ficam por trás.</li>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Opacidade:</b> Permite criar elementos semi-transparentes (como óculos escuros ou efeitos de aura).</li>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Travar Posição:</b> Fixa o acessório em relação ao centro do avatar, fazendo com que o item se mova junto com o personagem pela tela.</li>"
            "</ul>"
        )
        acc_lbl = QLabel(acc_text)
        acc_lbl.setWordWrap(True)
        acc_lbl.setTextFormat(Qt.RichText)
        acc_lay.addWidget(acc_lbl)
        layout.addWidget(acc_group)

        # --- SEÇÃO: SISTEMA DE EFEITOS (ATUALIZADO) ---
        effects_group = QGroupBox("🚀 SISTEMA DE EFEITOS")
        eff_lay = QVBoxLayout(effects_group)
        
        eff_text = (
            f"<p style='color: {Theme.TEXT_PRIMARY};'>Use a janela flutuante para dar vida à sua stream:</p>"
            "<ul>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Recorte de Áudio:</b> Utilize a barra de progresso verde para definir exatamente onde o som deve começar e terminar, sem precisar editar o ficheiro original.</li>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Testar Visual:</b> Clique no botão com o ícone de olho para pré-visualizar o efeito na tela antes de guardá-lo.</li>"
            f"<li style='color: {Theme.TEXT_MUTED};'><b>Combos:</b> Dispare áudio e imagem simultaneamente pressionando o atalho configurado.</li>"
            "</ul>"
        )
        eff_lbl = QLabel(eff_text)
        eff_lbl.setWordWrap(True)
        eff_lbl.setTextFormat(Qt.RichText)
        eff_lay.addWidget(eff_lbl)
        layout.addWidget(effects_group)

        # --- SEÇÃO: COMANDOS ---
        cmd_group = QGroupBox("⌨️ COMANDOS E CONTROLO")
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