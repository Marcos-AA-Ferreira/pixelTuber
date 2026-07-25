# ui/styles/theme.py
import os

class ThemeManager:
    # --- Geometria e Medidas Fixas ---
    CANVAS_SIZE = 1024       
    BASE_AVATAR_SIZE = 512   

    # --- Paleta de Cores: Tema Escuro (Padrão) ---
    DARK_THEME = {
        "@BG_DARK": "#1e1e1e",
        "@BG_LIST": "#121212",
        "@BG_CARD": "#252525",
        "@BG_PREVIEW": "#1a1a1a",
        "@BG_HOVER": "#333333",
        
        "@ACCENT": "#58a6ff",
        "@ACCENT_GREEN": "#00ff7f",
        "@ACCENT_GREEN_DARK": "#008f4f",
        "@DANGER": "#ff4d4d",
        "@SUCCESS": "#0078d7",
        
        "@TEXT_PRIMARY": "#dcdcdc",
        "@TEXT_MUTED": "#888888",
        
        "@DEFAULT_ROUNDING": "6px",
        "@CARD_ROUNDING": "4px"
    }

    @staticmethod
    def apply_theme(app, theme_name="dark"):
        """Lê o main.qss, injeta as variáveis do tema atual e aplica globalmente."""
        
        # Escolhe a paleta (pronto para adicionar LIGHT_THEME no futuro)
        palette = ThemeManager.DARK_THEME
        
        # Caminho relativo para encontrar o main.qss na mesma pasta
        qss_path = os.path.join(os.path.dirname(__file__), "main.qss")
        
        if not os.path.exists(qss_path):
            print(f"Aviso: Arquivo {qss_path} não encontrado.")
            return

        with open(qss_path, "r", encoding="utf-8") as f:
            qss_content = f.read()

        # Motor de Injeção: Troca os marcadores (ex: @ACCENT) pelas cores reais Hexadecimais
        for marcador, cor in palette.items():
            qss_content = qss_content.replace(marcador, cor)

        # Aplica o estilo dinâmico na aplicação inteira de uma só vez
        app.setStyleSheet(qss_content)