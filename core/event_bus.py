# core/event_bus.py
from PySide6.QtCore import QObject, Signal

class EventBus(QObject):
    """
    Central de comunicação global da aplicação.
    Qualquer parte do código pode emitir ou escutar estes sinais.
    """
    _instance = None

    def __init__(self):
        super().__init__()

    @classmethod
    def instance(cls):
        # Cria a instância apenas se ela ainda não existir
        if cls._instance is None:
            cls._instance = EventBus()
        return cls._instance

    # ==========================================
    # DEFINIÇÃO DOS SINAIS GLOBAIS
    # ==========================================
    
    # --- Trilha Sonora (Background Manager) ---
    request_music_change = Signal(str)
    request_music_play_pause = Signal()
    request_music_next = Signal()
    request_music_prev = Signal()
    request_music_remove = Signal()

    # --- Efeitos Visuais e Sonoros ---
    request_play_effect = Signal(dict)
    request_stop_all_effects = Signal()

    # --- Configurações de UI ---
    request_toggle_lock = Signal()

    # --- Sinais do Overlay / Interface ---
    effect_position_updated = Signal(dict)

    # --- Atualizações do Fundo (UI -> Manager) ---
    request_bg_image_change = Signal(str)
    request_bg_image_remove = Signal()
    request_bg_visual_update = Signal(dict) # Envia opacity, blur, layer
    request_bg_audio_update = Signal(dict)  # Envia volume, muted, loop

    # --- Sinais Reversos (Manager -> UI) ---
    bg_visual_changed = Signal(dict)
    bg_music_changed = Signal(str)
    
    # (Mantenha o restante dos seus sinais aqui...)