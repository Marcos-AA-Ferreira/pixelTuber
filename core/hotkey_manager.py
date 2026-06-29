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
        
        # 🟢 NOVO: Dicionário para guardar as ações dinâmicas enviadas pelo main.py (ex: música)
        self.registered_actions = {}

    # 🟢 NOVO: Método que o main.py tenta chamar para registar funções
    def register_action(self, action_name, callback):
        """Permite que outros gerenciadores registrem funções para serem chamadas por atalhos."""
        self.registered_actions[action_name] = callback

    # 🟢 NOVO: Método exigido pelo hotkey_editor.py para recarregar atalhos em tempo real
    def load_hotkeys(self):
        """Alias para setup_defaults, garantindo compatibilidade com o hotkey_editor.py."""
        self.setup_defaults()

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
                keyboard.add_hotkey(hk, lambda x=l_id: self._toggle_layer(x))

        # 🟢 NOVO: 3. Vincula os atalhos guardados no JSON às ações dinâmicas do main.py
        for action_name, callback in self.registered_actions.items():
            hk = hotkeys_cfg.get(action_name)
            if hk:
                keyboard.add_hotkey(hk, callback)

    def stop_all(self):
        """Remove todos os atalhos globais registrados."""
        try:
            keyboard.unhook_all()
        except Exception as e:
            print(f"Erro ao parar atalhos: {e}")

    # --- Métodos de Ação Interna (Mantenha as suas implementações originais aqui) ---

    def _toggle_render_lock(self):
        """Alterna a trava de movimento da janela do avatar."""
        render_cfg = self.cfg.data.get("render", {})
        current = render_cfg.get("locked", False)
        render_cfg["locked"] = not current
        self.cfg.save() # Salva a alteração de estado
        
        if hasattr(self.render, 'update_lock_state'):
            self.render.update_lock_state()

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
        # Mantenha aqui o resto do seu código original que manipula a opacidade/visibilidade do acessório
        pass