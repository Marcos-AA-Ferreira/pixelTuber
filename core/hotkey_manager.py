# core/hotkey_manager.py
import keyboard
import os
from PySide6.QtCore import QObject
from core.utils import validate_path
from core.event_bus import EventBus # <--- Nova importação vital aqui!

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
        
        # Dicionário para guardar as ações dinâmicas enviadas pelo main.py (ex: música)
        self.registered_actions = {}

    def register_action(self, action_name, callback):
        """Permite que outros gerenciadores registrem funções para serem chamadas por atalhos."""
        self.registered_actions[action_name] = callback

    def load_hotkeys(self):
        """Alias para setup_defaults, garantindo compatibilidade com o hotkey_editor.py."""
        self.setup_defaults()

    def setup_defaults(self):
        """Lê o arquivo de configuração e registra todos os atalhos."""
        self.stop_all()
        hotkeys_cfg = self.cfg.data.get("hotkeys", {})

        # 1. Atalhos de Sistema (Renderização)
        if hotkeys_cfg.get("toggle_lock"):
            hook = keyboard.add_hotkey(hotkeys_cfg["toggle_lock"], self._toggle_render_lock)
            self.active_hooks["toggle_lock"] = hook

        if hotkeys_cfg.get("next_set"):
            hook = keyboard.add_hotkey(hotkeys_cfg["next_set"], self._next_animation_set)
            self.active_hooks["next_set"] = hook

        # 2. Atalhos de Acessórios (Camadas Auxiliares)
        layers = self.cfg.data.get("aux_layers", {})
        for l_id, config in layers.items():
            hk = config.get("hotkey")
            if hk:
                hook = keyboard.add_hotkey(hk, lambda x=l_id: self._toggle_layer(x))
                self.active_hooks[f"layer_{l_id}"] = hook

        # 3. Vincula os atalhos guardados no JSON às ações dinâmicas do main.py
        for action_name, callback in self.registered_actions.items():
            hk = hotkeys_cfg.get(action_name)
            if hk:
                hook = keyboard.add_hotkey(hk, callback)
                self.active_hooks[f"action_{action_name}"] = hook

        # 4. NOVÍSSIMO: Registra atalhos dos Efeitos Customizados (Ao iniciar o App)
        custom_effects = self.cfg.data.get("profile", {}).get("custom_effects", {})
        for eid, data in custom_effects.items():
            hk = data.get("hotkey")
            if hk:
                self.register_custom_effect(eid, hk, data)

    def register_custom_effect(self, eid: str, hotkey_str: str, effect_data: dict):
        """Registra um atalho para um efeito customizado dinamicamente."""
        self.remove_custom_hotkey(eid) # Previne atalhos duplicados se você estiver editando
        
        if not hotkey_str:
            return
            
        try:
            # Cria a função disparadora invisível que injeta os dados do efeito direto no EventBus
            callback = lambda data=effect_data: EventBus.instance().request_play_effect.emit(data)
            
            hook = keyboard.add_hotkey(hotkey_str, callback)
            self.active_hooks[eid] = hook
            print(f"Atalho {hotkey_str.upper()} ativado para o efeito {effect_data.get('name')}.")
        except Exception as e:
            print(f"Aviso: Não foi possível registrar o atalho {hotkey_str} para {eid}: {e}")

    def remove_custom_hotkey(self, eid: str):
        """Remove um atalho de efeito customizado se existir (útil ao deletar efeitos)."""
        if eid in self.active_hooks:
            try:
                keyboard.remove_hotkey(self.active_hooks[eid])
            except Exception:
                pass
            del self.active_hooks[eid]

    def stop_all(self):
        """Remove todos os atalhos globais registrados."""
        try:
            keyboard.unhook_all()
            self.active_hooks.clear()
        except Exception as e:
            print(f"Erro ao parar atalhos: {e}")

    # --- Métodos de Ação Interna (Agora Desacoplados!) ---
    def _toggle_render_lock(self):
        """Alterna a trava de movimento da janela do avatar."""
        render_cfg = self.cfg.data.get("render", {})
        current = render_cfg.get("locked", False)
        render_cfg["locked"] = not current
        self.cfg.save() 
        if hasattr(self.render, 'update_lock_state'):
            self.render.update_lock_state()

    def _next_animation_set(self):
        """Troca para o próximo conjunto de GIFs usando a nova arquitetura."""
        anim_cfg = self.cfg.data.get("animations", {})
        sets = list(anim_cfg.get("sets", {}).keys())
        if not sets: return
        
        current = anim_cfg.get("main_set", "default")
        try:
            next_idx = (sets.index(current) + 1) % len(sets)
            anim_cfg["main_set"] = sets[next_idx]
            self.cfg.save()
            # Emite um sinal em vez de tentar mudar as coisas à força!
            EventBus.instance().request_animation_set_change.emit(sets[next_idx])
        except ValueError:
            anim_cfg["main_set"] = sets[0]

    def _toggle_layer(self, l_id):
        """Liga/Desliga a visibilidade de um acessório usando sinais."""
        layer_cfg = self.cfg.data.get("aux_layers", {}).get(l_id)
        if layer_cfg:
            layer_cfg["visible"] = not layer_cfg.get("visible", True)
            self.cfg.save()
            # Avisa a RenderWindow para se atualizar!
            EventBus.instance().request_geometry_update.emit()