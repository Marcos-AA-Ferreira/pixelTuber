# ui/schemas/avatar_schema.py

AVATAR_GENERAL_SCHEMA = [
    {
        "type": "lineedit",
        "key": "avatar.name",
        "title": "Nome do Avatar:",
        "placeholder": "ex: Avatar Principal",
        "default": "Novo Avatar"
    }
]

AVATAR_TRANSFORM_SCHEMA = [
    {
        "type": "custom_slider",
        "key": "render.scale",
        "title": "Escala / Tamanho (%):",
        "min_val": 10,
        "max_val": 400,
        "default": 100,
        "step": 1,
        "unit": "%",
        "decimals": 0,
        "ticks": [("10%", 10), ("100%", 100), ("400%", 400)]
    },
    {
        "type": "switch",
        "key": "render.flip_h",
        "title": "Inverter / Espelhar Horizontalmente",
        "default": False
    },
    {
        "type": "switch",
        "key": "render.locked",
        "title": "Travar Posição na Tela",
        "default": False
    }
]

AVATAR_ANIMATION_SCHEMA = [
    {
        "type": "combobox",
        "key": "animations.fps",
        "title": "Taxa de Quadros (FPS das Animações):",
        "options": ["12 FPS", "24 FPS", "30 FPS", "60 FPS"],
        "default": "24 FPS"
    }
]