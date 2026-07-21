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
    
    # --- UI -> Manager (A UI pede para o Manager mudar algo) ---
    request_audio_gain_change = Signal(float)
    request_audio_noise_gate_change = Signal(float)
    request_audio_hold_time_change = Signal(int)
    request_audio_ducking_toggle = Signal(bool)
    request_audio_threshold_change = Signal(str, float)
    request_visualizer_style_change = Signal(str)
    request_audio_device_change = Signal(int)
    request_refresh_devices = Signal()

    # --- Manager -> UI (O Manager avisa a UI que algo atualizou) ---
    audio_volume_updated = Signal(float)
    audio_processed_updated = Signal(float, list)
    audio_devices_updated = Signal(list)

    # --- UI -> Manager (Comandos do Avatar) ---
    request_geometry_update = Signal()
    request_animation_set_change = Signal(str)

    # --- Novos comandos de Controle e UI ---
    request_avatar_visibility_toggle = Signal(bool)
    request_avatar_minimize_toggle = Signal()
    request_mic_mute_toggle = Signal(bool)
    request_hotkeys_reload = Signal()
    
    # --- Estado (Manager avisando a UI) ---
    audio_mute_updated = Signal(bool)

    # --- UI -> Manager (Configurações Gerais e Atalhos) ---
    request_render_on_top_toggle = Signal(bool)
    request_chroma_key_update = Signal()
    request_register_effect_hotkey = Signal(str, str, dict) # eid, hotkey, data
    request_remove_effect_hotkey = Signal(str)              # eid
    
    # --- UI -> Manager (Controle de Tempo da Música) ---
    request_bg_player_set_position = Signal(int)
    
    # --- Manager -> UI (Status do Player de Fundo) ---
    bg_player_position_updated = Signal(int)
    bg_player_duration_updated = Signal(int)
    bg_player_metadata_updated = Signal(str)
    bg_player_state_changed = Signal(bool) # Avisa se está tocando ou pausado