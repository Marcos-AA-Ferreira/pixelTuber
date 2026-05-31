# core/animation_manager.py
import time
import os
from core.utils import validate_path

class AnimationManager:
    # Ordem de intensidade para lógica de comparação
    STATES_ORDER = ["mute", "low", "med", "high", "very_high"]

    def __init__(self, config_manager):
        self.cfg = config_manager
        self.last_state = "mute"
        self.last_change_time = 0

    def get_current_path(self, vol):
        """
        Analisa o volume atual e retorna o caminho do GIF correspondente.
        Inclui lógica de retenção (hold_time) para suavizar a transição.
        """
        data = self.cfg.data
        audio_cfg = data.get("audio", {})
        th = audio_cfg.get("thresholds", {})
        
        # Configurações de comportamento
        mode = audio_cfg.get("mode", "smooth") 
        hold_time = audio_cfg.get("hold_time", 0.1) # Segundos para manter o estado alto

        # 1. Determinação do Estado Alvo (Raw)
        target_state = "mute"
        if vol >= th.get("very_high", 0.8): target_state = "very_high"
        elif vol >= th.get("high", 0.5):    target_state = "high"
        elif vol >= th.get("med", 0.2):     target_state = "med"
        elif vol >= th.get("low", 0.05):    target_state = "low"

        # 2. Lógica de Transição (Modo Smooth vs Standard)
        if mode == "standard":
            self.last_state = target_state
        else:
            # No modo Smooth, subir de nível é instantâneo, descer requer espera
            idx_last = self.STATES_ORDER.index(self.last_state)
            idx_target = self.STATES_ORDER.index(target_state)

            if idx_target > idx_last:
                # Voz aumentou: Reage imediatamente
                self.last_state = target_state
                self.last_change_time = time.time()
            elif idx_target < idx_last:
                # Voz diminuiu: Verifica se o tempo de retenção já passou
                if (time.time() - self.last_change_time) > hold_time:
                    self.last_state = target_state
                    self.last_change_time = time.time()

        # 3. Busca do Ficheiro no Config
        # Obtém o set de animações ativo (ex: "default", "bravo", "triste")
        active_set_name = data["animations"].get("main_set", "default")
        anim_set = data["animations"]["sets"].get(active_set_name, {})
        
        path = anim_set.get(self.last_state)
        
        # Fallback: Se o caminho for inválido ou vazio, usa o estado "mute"
        if not validate_path(path):
            path = anim_set.get("mute")
            
        return path