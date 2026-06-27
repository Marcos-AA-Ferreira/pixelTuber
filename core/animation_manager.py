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

    def update(self, vol):
        """
        Recebe o volume atual, decide qual é o sprite/GIF correto (lip-sync),
        aplica o decaimento e atualiza diretamente a janela de renderização.
        """
        path = self.get_current_path(vol)
        
        # Só atualiza a janela se o caminho mudou, evitando reiniciar o GIF do frame zero a cada frame
        if path and path != self.current_rendered_path:
            if hasattr(self.render, 'set_animation'):
                self.render.set_animation(path)
                self.current_rendered_path = path
            elif hasattr(self.render, 'load_image'):
                self.render.load_image(path)
                self.current_rendered_path = path

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
        return anim_set.get("mute", "")

    # ================================================================
    # GERENCIAMENTO DE DADOS (DESACOPLADOS DA UI)
    # ================================================================

    def set_active_set(self, set_name):
        """Define o set selecionado como ativo e atualiza a janela de renderização."""
        self.cfg.data["animations"]["main_set"] = set_name
        self.cfg.save()

        mute_path = self.cfg.data["animations"].get("sets", {}).get(set_name, {}).get("mute", "")
        if hasattr(self.render, 'set_animation'):
            self.render.set_animation(mute_path)
            self.current_rendered_path = mute_path

    def create_new_set(self, name):
        """Cria um novo espaço em branco para um avatar."""
        if name not in self.cfg.data["animations"]["sets"]:
            self.cfg.data["animations"]["sets"][name] = {
                "mute": "", "low": "", "med": "", "high": "", "very_high": ""
            }
            self.cfg.save()
            return True
        return False

    def import_folder_set(self, folder_path):
        """Lógica de heurística para importar pastas."""
        set_name = os.path.basename(folder_path)
        if set_name in self.cfg.data["animations"]["sets"]:
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

        self.cfg.data["animations"]["sets"][set_name] = new_set
        self.cfg.save()
        return set_name

    def delete_set(self, set_name):
        """Deleta uma skin, impedindo de apagar se for a única."""
        sets = self.cfg.data["animations"]["sets"]
        if set_name == "default" or len(sets) <= 1:
            return False
            
        del sets[set_name]
        
        if self.cfg.data["animations"].get("main_set") == set_name:
            self.set_active_set("default")
        else:
            self.cfg.save()
        return True

    def update_sprite(self, set_name, state, path):
        """Atualiza ou limpa um sprite específico e atualiza a tela se necessário."""
        self.cfg.data["animations"]["sets"][set_name][state] = path
        self.cfg.save()
        
        if set_name == self.cfg.data["animations"].get("main_set"):
            if getattr(self.render, "current_state", None) == state:
                if hasattr(self.render, 'set_animation'):
                    self.render.set_animation(path)
                    self.current_rendered_path = path