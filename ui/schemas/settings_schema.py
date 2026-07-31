# src/ui/schemas/settings_schema.py

SYSTEM_SCHEMA = [
    {
        "type": "combobox", 
        "key": "system.fps_limit", 
        "title": "Limite de FPS (Desempenho):", 
        "options": ["30 FPS", "60 FPS", "120 FPS"], 
        "default": "60 FPS"
    },
    {
        "type": "combobox", 
        "key": "render.chroma_key", 
        "title": "Fundo do Avatar (Chroma Key):", 
        "options": ["Transparente (Padrão)", "Verde Chroma (#00FF00)", "Magenta (#FF00FF)"], 
        "default": "Transparente (Padrão)"
    },
    {
        "type": "switch", 
        "key": "system.minimize_to_tray", 
        "title": "Minimizar para a Bandeja (System Tray) ao invés de fechar", 
        "default": False
    }
]

HOTKEYS_SCHEMA = [
    {
        "type": "lineedit", 
        "key": "hotkeys.toggle_lock", 
        "title": "Travar/Destravar Movimento:", 
        "placeholder": "ex: f10 ou shift+k"
    },
    {
        "type": "lineedit", 
        "key": "hotkeys.next_set", 
        "title": "Próximo Set de Animação:", 
        "placeholder": "ex: f10 ou shift+k"
    }
]

WINDOW_SCHEMA = [
    {
        "type": "switch", 
        "key": "render.always_on_top", 
        "title": "Janela do Avatar sempre no topo (Overlay)", 
        "default": True
    }
]