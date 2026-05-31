class Theme:
    # --- Geometria e Medidas ---
    CANVAS_SIZE = 1024       
    BASE_AVATAR_SIZE = 512   
    DEFAULT_ROUNDING = "6px"
    CARD_ROUNDING = "4px"

    # --- Cores Principais ---
    BG_DARK = "#1e1e1e"
    BG_LIST = "#121212"
    BG_CARD = "#252525"
    BG_PREVIEW = "#1a1a1a"
    BG_HOVER = "#333333"
    
    ACCENT = "#58a6ff"
    ACCENT_GREEN = "#00ff7f"
    ACCENT_GREEN_DARK = "#008f4f"
    DANGER = "#ff4d4d"
    SUCCESS = "#0078d7"
    
    TEXT_PRIMARY = "#dcdcdc"
    TEXT_MUTED = "#888888"
    
    # --- Estilos de Widgets (QSS) ---

    MAIN_TAB_STYLE = f"""
        QWidget {{ background-color: {BG_DARK}; color: {TEXT_PRIMARY}; }}
        QScrollArea {{ border: none; background-color: transparent; }}
        QLineEdit {{ background: {BG_LIST}; color: #00ff00; border: 1px solid #444; padding: 4px; border-radius: 3px; }}
        QSpinBox {{ background: {BG_LIST}; color: white; border: 1px solid #444; padding: 2px; border-radius: 3px; }}
        QComboBox {{ background: {BG_LIST}; color: white; border: 1px solid #444; border-radius: 3px; padding: 2px; }}
        QLabel {{ color: {TEXT_PRIMARY}; }}
        QCheckBox {{ spacing: 8px; }}
        QCheckBox::indicator {{ width: 18px; height: 18px; }}
    """

    GROUP_BOX = f"""
        QGroupBox {{ 
            font-weight: bold; border: 1px solid #333; 
            border-radius: 8px; margin-top: 15px; padding-top: 15px;
            color: {ACCENT};
        }}
    """

    # --- Botões ---
    BUTTON_BASE = f"""
        QPushButton {{ 
            background-color: #2d2d2d; border: 1px solid #444; 
            padding: 8px; border-radius: {DEFAULT_ROUNDING}; font-weight: bold; 
        }}
        QPushButton:hover {{ background-color: {BG_HOVER}; border-color: {ACCENT}; }}
        QPushButton:checked {{ background-color: {SUCCESS}; color: white; }}
    """

    BUTTON_PRIMARY = f"""
        QPushButton {{
            background-color: {SUCCESS}; color: white; border: none;
            padding: 8px; border-radius: {DEFAULT_ROUNDING}; font-weight: bold;
        }}
        QPushButton:hover {{ background-color: {ACCENT}; }}
    """

    BUTTON_DANGER = f"""
        QPushButton {{
            background-color: {BG_CARD};
            color: {DANGER};
            border: 1px solid #444;
            padding: 8px;
            border-radius: {DEFAULT_ROUNDING};
            font-weight: bold;
        }}
        QPushButton:hover {{ background-color: {DANGER}; color: white; }}
    """

    BUTTON_REMOVE = f"""
        QPushButton {{ 
            background-color: transparent; border: 1px solid #444; 
            color: {DANGER}; border-radius: 4px; font-size: 14px;
        }}
        QPushButton:hover {{ background-color: {DANGER}; color: white; border-color: {DANGER}; }}
    """

    BUTTON_MUTE_ACTIVE = f"""
        QPushButton#BtnMute:checked {{ background-color: {DANGER}; color: white; }}
    """

    # Novo estilo para os botões de navegação Z (|<| |>|)
    Z_NAV_BUTTON = f"""
        QPushButton {{
            background-color: #333;
            color: {ACCENT};
            border: 1px solid #444;
            border-radius: 3px;
            font-weight: bold;
            font-size: 14px;
            padding: 0px;
        }}
        QPushButton:hover {{
            background-color: {ACCENT};
            color: white;
        }}
        QPushButton:pressed {{
            background-color: #222;
        }}
    """

    # Novo estilo para o número da camada
    Z_DISPLAY = f"""
        QLabel {{
            background-color: {BG_LIST};
            color: white;
            border: 1px solid #444;
            border-radius: 3px;
            padding: 2px 8px;
            font-family: 'Consolas', monospace;
            font-weight: bold;
            min-width: 25px;
        }}
    """

    # --- Componentes de Interface ---
    ACCESSORY_CARD = f"""
        QFrame {{ 
            background: {BG_CARD}; border-radius: {CARD_ROUNDING}; 
            padding: 10px; border: 1px solid #333; 
        }}
    """

    SPIN_BOX_Z = f"""
        QSpinBox {{ 
            background: {BG_LIST}; color: white; border: none; 
            font-weight: bold; font-size: 14px; padding: 2px;
        }}
    """

    PREVIEW_BOX = f"""
        QLabel {{
            background-color: {BG_PREVIEW}; 
            border: 2px solid #333; 
            border-radius: {DEFAULT_ROUNDING};
        }}
    """

    TIME_LABEL = f"""
        font-family: 'Consolas', monospace; 
        font-size: 11px; 
        color: {TEXT_MUTED};
    """

    MUSIC_INFO = f"""
        color: {ACCENT_GREEN}; 
        font-weight: bold; 
        font-size: 12px;
    """

    PROGRESS_SLIDER = f"""
        QSlider::groove:horizontal {{ 
            background: #333; 
            height: 6px; 
            border-radius: 3px; 
        }}
        QSlider::handle:horizontal {{ 
            background: {ACCENT_GREEN}; 
            width: 14px; 
            height: 14px; 
            margin: -4px 0; 
            border-radius: 7px; 
        }}
        QSlider::sub-page:horizontal {{ 
            background: {ACCENT_GREEN_DARK}; 
            border-radius: 3px; 
        }}
    """