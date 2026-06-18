# core/animation_manager.py
import time
import os
from core.utils import validate_path

class AnimationManager:
    # Ordem de intensidade para lógica de comparação e decaimento
    STATES_ORDER = ["mute", "low", "med", "high", "very_high"]

    def __init__(self, config_manager):
        self.cfg = config_manager
        self.last_state = "mute"
        self.last_change_time = 0

    def get_current_path(self, vol):
        """
        Analisa o volume atual e retorna o caminho do GIF correspondente.
        Inclui decaimento suave para um fechamento de boca orgânico.
        """
        data = self.cfg.data
        audio_cfg = data.get("audio", {})
        th = audio_cfg.get("thresholds", {})
        
        # Configurações de comportamento
        mode = audio_cfg.get("mode", "smooth") 
        hold_time = audio_cfg.get("hold_time", 0.1) # Tempo de retenção por degrau

        # 1. Determinação do Estado Alvo (Raw)
        target_state = "mute"
        if vol >= th.get("very_high", 0.8): target_state = "very_high"
        elif vol >= th.get("high", 0.5):    target_state = "high"
        elif vol >= th.get("med", 0.2):     target_state = "med"
        elif vol >= th.get("low", 0.05):    target_state = "low"

        # 2. Lógica de Transição
        if mode == "standard":
            self.last_state = target_state
        else:
            # Modo Smooth com Decaimento Escalonado
            idx_last = self.STATES_ORDER.index(self.last_state)
            idx_target = self.STATES_ORDER.index(target_state)

            if idx_target > idx_last:
                # Voz aumentou: Reage e abre a boca imediatamente
                self.last_state = target_state
                self.last_change_time = time.time()
            elif idx_target < idx_last:
                # Voz diminuiu: Decai gradualmente um estado de cada vez
                if (time.time() - self.last_change_time) > hold_time:
                    # Em vez de pular para o alvo, desce apenas 1 nível na escada
                    self.last_state = self.STATES_ORDER[idx_last - 1]
                    self.last_change_time = time.time()

        # 3. Busca do Ficheiro no Config
        active_set_name = data["animations"].get("main_set", "default")
        anim_set = data["animations"]["sets"].get(active_set_name, {})
        
        path = anim_set.get(self.last_state)
        
        # Fallback de segurança para estados não configurados
        if not validate_path(path):
            path = anim_set.get("mute")
            
        return path
    
    '''import time
import os
from core.utils import validate_path

class AnimationManager:
    # Hierarquia linear de intensidade sonora
    STATES_ORDER = ["mute", "low", "med", "high", "very_high"]

    def __init__(self, config_manager):
        self.cfg = config_manager
        self.last_state = "mute"
        self.last_change_time = 0.0

    def get_current_path(self, vol):
        """
        Analisa o volume e devolve a animação correspondente com 
        decaimento suave para um fechamento de boca orgânico.
        """
        data = self.cfg.data
        audio_cfg = data.get("audio", {})
        th = audio_cfg.get("thresholds", {"low": 0.05, "med": 0.2, "high": 0.5, "very_high": 0.8})
        
        mode = audio_cfg.get("mode", "smooth") 
        hold_time = audio_cfg.get("hold_time", 0.1)

        # 1. Determinação do Estado Alvo
        target_state = "mute"
        if vol >= th.get("very_high", 0.8): target_state = "very_high"
        elif vol >= th.get("high", 0.5):    target_state = "high"
        elif vol >= th.get("med", 0.2):     target_state = "med"
        elif vol >= th.get("low", 0.05):    target_state = "low"

        # 2. Algoritmo Smooth (Decaimento Escalonado)
        if mode == "standard":
            self.last_state = target_state
        else:
            idx_last = self.STATES_ORDER.index(self.last_state)
            idx_target = self.STATES_ORDER.index(target_state)

            if idx_target > idx_last:
                # Voz aumentou: Abre a boca na hora (Ataque imediato)
                self.last_state = target_state
                self.last_change_time = time.time()
            elif idx_target < idx_last:
                # Voz diminuiu: Desce apenas um nível por ciclo (Relaxamento)
                if (time.time() - self.last_change_time) > hold_time:
                    self.last_state = self.STATES_ORDER[idx_last - 1]
                    self.last_change_time = time.time()

        # 3. Resgate Seguro com Cascata de Recuo (Fallback)
        active_set_name = data.get("animations", {}).get("main_set", "default")
        anim_set = data.get("animations", {}).get("sets", {}).get(active_set_name, {})

        check_idx = self.STATES_ORDER.index(self.last_state)
        while check_idx >= 0:
            state_to_try = self.STATES_ORDER[check_idx]
            path = anim_set.get(state_to_try, "")
            if validate_path(path):
                return path
            check_idx -= 1

        # Proteção máxima para não deixar a tela vazia
        return anim_set.get("mute", "")'''