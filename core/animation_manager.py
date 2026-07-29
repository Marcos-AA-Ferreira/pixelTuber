# core/animation_manager.py
import time
import os
import uuid
from core.utils import validate_path

class AnimationManager:
    # Hierarquia linear de intensidade sonora para lógica de comparação e decaimento
    STATES_ORDER = ["mute", "low", "med", "high", "very_high"]

    def __init__(self, config_manager, render_window):
        self.cfg = config_manager
        self.render = render_window
        self.last_state = "mute"
        self.last_change_time = 0.0
        self.current_rendered_path = ""  # Impede o reset contínuo do frame zero do GIF

    # ================================================================
    # LÓGICA DE ANIMAÇÃO (LIP-SYNC)
    # ================================================================

    def _determine_voice_state(self, volume):
        """
        Calcula o estado da animação ("mute", "low", "med", "high", "very_high")
        com base no volume recebido do microfone em relação ao noise gate.
        """
        # Pega o limite de ruído configurado (se não achar, assume 0.02)
        # Ajuste a forma de buscar o config caso seu get_audio_config seja diferente
        gate = self.cfg.data.get("audio", {}).get("noise_gate", 0.02)
        
        # Se o volume for menor que o limite, está em silêncio
        if volume < gate:
            return "mute"
            
        # Calcula o quão alto a pessoa está falando além do ruído de fundo
        active_vol = volume - gate
        
        # Define os limites para cada intensidade de fala
        if active_vol < 0.1:
            return "low"
        elif active_vol < 0.3:
            return "med"
        elif active_vol < 0.6:
            return "high"
        else:
            return "very_high"

    def update(self, vol):
        anim_cfg = self.cfg.data.get("animations", {})
        active_set_name = anim_cfg.get("main_set", "default")
        active_set = anim_cfg.get("sets", {}).get(active_set_name, {})

        # Verifica o modo (se não existir, assume o legado "full")
        mode = active_set.get("mode", "full") 
        
        # Determine o estado baseado no volume (ex: "mute", "low", "med", etc.)
        # Assumindo que você já tem um método que faz isso:
        state = self._determine_voice_state(vol) 

        if mode == "full":
            # --- MODO AVATAR INTEIRO ---
            self.render.body_label.hide()
            self.render.head_label.hide()
            self.render.main_label.show()

            # Tenta pegar no formato novo, se não achar, usa o antigo para não quebrar skins velhas
            path = active_set.get("full", {}).get(state, active_set.get(state, ""))
            self.render.set_layer_media(self.render.main_label, path)

        elif mode == "split":
            # --- MODO CABEÇA/CORPO SEPARADOS ---
            # Limpa o contêiner base e mostra as camadas internas
            self.render.set_layer_media(self.render.main_label, "")
            self.render.body_label.show()
            self.render.head_label.show()

            # A cabeça reage ao microfone normalmente
            head_path = active_set.get("head", {}).get(state, "")
            
            # O corpo pode ter uma lógica mais simples (idle ou speaking)
            # ou até reagir ao pulo/movimento no futuro
            is_speaking = vol > self.cfg.get_audio_config("noise_gate", 0.02)
            body_state = "speaking" if is_speaking else "idle"
            body_path = active_set.get("body", {}).get(body_state, "")

            self.render.set_layer_media(self.render.head_label, head_path)
            self.render.set_layer_media(self.render.body_label, body_path)

    def get_current_path(self, vol):
        """
        Analisa o volume e devolve a animação correspondente com 
        decaimento suave para um fechamento de boca orgânico.
        """
        th = self.cfg.get_audio_config("thresholds", {"low": 0.05, "med": 0.2, "high": 0.5, "very_high": 0.8})
        mode = self.cfg.get_audio_config("mode", "smooth")
        hold_time = self.cfg.get_audio_config("hold_time", 0.1)

        # 1. Determinação do Estado Alvo (Raw)
        target_state = "mute"
        if vol >= th.get("very_high", 0.8):   target_state = "very_high"
        elif vol >= th.get("high", 0.5):     target_state = "high"
        elif vol >= th.get("med", 0.2):      target_state = "med"
        elif vol >= th.get("low", 0.05):     target_state = "low"

        # 2. Algoritmo Smooth (Decaimento Escalonado)
        if mode == "standard":
            self.last_state = target_state
        else:
            idx_last = self.STATES_ORDER.index(self.last_state)
            idx_target = self.STATES_ORDER.index(target_state)

            current_time = time.time()
            if idx_target > idx_last:
                # Voz aumentou: Abre a boca na hora (Ataque imediato)
                self.last_state = target_state
                self.last_change_time = current_time
            elif idx_target < idx_last:
                # Voz diminuiu: Desce apenas um nível por ciclo de retenção (Relaxamento)
                if (current_time - self.last_change_time) > hold_time:
                    self.last_state = self.STATES_ORDER[idx_last - 1]
                    self.last_change_time = current_time

        # 3. Resgate Seguro com Cascata de Recuo (Fallback Dinâmico)
        active_set_name = self.cfg.get_active_set()
        anim_set = self.cfg.get_all_sets().get(active_set_name, {})

        check_idx = self.STATES_ORDER.index(self.last_state)
        while check_idx >= 0:
            state_to_try = self.STATES_ORDER[check_idx]
            path = anim_set.get(state_to_try, "")
            if validate_path(path):
                return path
            check_idx -= 1

        # Proteção máxima para não deixar a tela vazia
        return anim_set.get("mute", "")

    # ================================================================
    # GERENCIAMENTO DE DADOS (DESACOPLADOS DA UI)
    # ================================================================

    def set_active_set(self, set_name):
        """Define o set selecionado como ativo e atualiza a janela de renderização."""
        # ✅ Delega para a Fonte de Verdade
        self.cfg.set_animation_config("main_set", set_name) 

        mute_path = self.cfg.get_all_sets().get(set_name, {}).get("mute", "")
        if hasattr(self.render, 'set_animation'):
            self.render.set_animation(mute_path)
            self.current_rendered_path = mute_path

    def create_new_set(self, name):
        """Cria um novo espaço em branco para um avatar."""
        sets = self.cfg.get_all_sets()
        
        if name not in sets:
            sets[name] = {"mute": "", "low": "", "med": "", "high": "", "very_high": ""}
            self.cfg.set_animation_config("sets", sets) # Salva automaticamente
            return True
            
        return False

    def import_folder_set(self, folder_path):
        """Lógica de heurística para importar pastas."""
        sets = self.cfg.get_all_sets()
        set_name = os.path.basename(folder_path)
        
        if set_name in sets:
            set_name += f"_{uuid.uuid4().hex[:4]}"
        
        new_set = {"mute": "", "low": "", "med": "", "high": "", "very_high": ""}
        files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.gif', '.png', '.jpg', '.jpeg', '.webp'))]
        
        for f in files:
            fname = f.lower()
            path = os.path.join(folder_path, f)
            if "mute" in fname or "nf" in fname or "fechad" in fname:
                new_set["mute"] = path
            elif "low" in fname or "- f" in fname or "fala" in fname or "abert" in fname:
                new_set["low"] = path
        
        if not new_set["mute"] and files:
            new_set["mute"] = os.path.join(folder_path, files[0])

        sets[set_name] = new_set
        self.cfg.set_animation_config("sets", sets)
        
        return set_name

    def delete_set(self, set_name):
        """Deleta uma skin, impedindo de apagar se for a única."""
        sets = self.cfg.get_all_sets()
        
        if set_name == "default" or len(sets) <= 1:
            return False
            
        del sets[set_name]
        self.cfg.set_animation_config("sets", sets) # Atualiza a fonte de verdade
        
        # Se a skin apagada era a que estava em uso, reseta para default
        if self.cfg.get_active_set() == set_name:
            self.set_active_set("default")
            
        return True

    def update_sprite(self, set_name, state, path):
        """Atualiza ou limpa um sprite específico e atualiza a tela se necessário."""
        # ✅ Delega para a Fonte de Verdade
        self.cfg.update_sprite_in_set(set_name, state, path)

        if set_name == self.cfg.get_active_set():
            if getattr(self.render, "current_state", None) == state:
                if hasattr(self.render, 'set_animation'):
                    self.render.set_animation(path)
                    self.current_rendered_path = path