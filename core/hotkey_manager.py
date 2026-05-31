import keyboard
import os
from PySide6.QtCore import QObject
from core.utils import validate_path

class HotkeyManager:
    """
    Escuta atalhos globais do teclado e dispara ações nos outros managers.
    Funciona mesmo com o programa em segundo plano.
    """
    def __init__(self, config_manager, render_window, overlay_window):
        self.cfg = config_manager
        self.render = render_window
        self.overlay = overlay_window
        
        # Guarda os IDs dos hooks ativos para podermos removê-los individualmente
        self.active_hooks = {}

    def setup_defaults(self):
        """Lê o arquivo de configuração e registra todos os atalhos."""
        self.stop_all()
        
        hotkeys_cfg = self.cfg.data.get("hotkeys", {})
        
        # 1. Atalhos de Sistema (Renderização)
        if hotkeys_cfg.get("toggle_lock"):
            keyboard.add_hotkey(hotkeys_cfg["toggle_lock"], self._toggle_render_lock)
            
        if hotkeys_cfg.get("next_set"):
            keyboard.add_hotkey(hotkeys_cfg["next_set"], self._next_animation_set)

        # 2. Atalhos de Acessórios (Camadas Auxiliares)
        layers = self.cfg.data.get("aux_layers", {})
        for l_id, config in layers.items():
            hk = config.get("hotkey")
            if hk:
                # Usamos um closure (lambda com default arg) para capturar o ID correto
                keyboard.add_hotkey(hk, lambda i=l_id: self._toggle_layer(i))

        # 3. Atalhos para Efeitos Customizados
        effects = self.cfg.data.get("custom_effects", {})
        for e_id, data in effects.items():
            hk = data.get("hotkey")
            if hk:
                self.register_custom_effect(e_id, hk, data)

    def register_custom_effect(self, eid, key_combo, effect_data):
        """Registra uma tecla para disparar um efeito visual/sonoro."""
        # Garante que não existam duplicatas para o mesmo ID antes de registrar
        self.remove_custom_hotkey(eid)

        def trigger():
            # Tenta disparar via Overlay (que gerencia o tempo e o widget visual)
            # Nota: Se o efeito for apenas áudio, o play_custom_effect da Overlay
            # ou o play_effect do EffectManager deve tratar.
            self.overlay.play_custom_effect(effect_data)

        try:
            keyboard.add_hotkey(key_combo, trigger, suppress=False)
            self.active_hooks[eid] = key_combo
        except Exception as e:
            print(f"Erro ao registrar hotkey {key_combo} para o efeito {eid}: {e}")

    def remove_custom_hotkey(self, eid):
        """
        Remove um atalho específico do sistema.
        (Renomeado de unregister_hook para corrigir o AttributeError)
        """
        if eid in self.active_hooks:
            try:
                hotkey_string = self.active_hooks[eid]
                keyboard.remove_hotkey(hotkey_string)
                del self.active_hooks[eid]
            except Exception as e:
                print(f"Erro ao remover atalho {eid}: {e}")

    # --- Métodos de Ação Interna ---

    def _toggle_render_lock(self):
        """Alterna a trava de movimento da janela do avatar."""
        render_cfg = self.cfg.data.get("render", {})
        current = render_cfg.get("locked", False)
        render_cfg["locked"] = not current
        self.cfg.save() # Salva a alteração de estado
        
        # Opcional: Notificar a janela de renderização aqui se necessário

    def _next_animation_set(self):
        """Troca para o próximo conjunto de GIFs."""
        anim_cfg = self.cfg.data.get("animations", {})
        sets = list(anim_cfg.get("sets", {}).keys())
        if not sets: return
        
        current = anim_cfg.get("main_set", "default")
        try:
            next_idx = (sets.index(current) + 1) % len(sets)
            anim_cfg["main_set"] = sets[next_idx]
            self.cfg.save()
        except ValueError:
            anim_cfg["main_set"] = sets[0]

    def _toggle_layer(self, l_id):
        """Liga/Desliga a visibilidade de um acessório."""
        layers = self.cfg.data.get("aux_layers", {})
        if l_id in layers:
            current = layers[l_id].get("visible", True)
            layers[l_id]["visible"] = not current
            self.cfg.save()

    def stop_all(self):
        """Remove todos os atalhos globais."""
        try:
            keyboard.unhook_all()
            self.active_hooks = {}
        except:
            pass