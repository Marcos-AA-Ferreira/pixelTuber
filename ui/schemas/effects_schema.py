# src/ui/schemas/effects_schema.py

VISUAL_EFFECT_SCHEMA = [
    {
        "type": "custom_slider", 
        "key": "scale", 
        "title": "ESCALA DO ITEM:", 
        "min_val": 5, 
        "max_val": 300, 
        "default": 1.0, 
        "unit": "%", 
        "decimals": 2
    },
    {
        "type": "custom_slider", 
        "key": "opacity", 
        "title": "OPACIDADE:", 
        "min_val": 0, 
        "max_val": 100, 
        "default": 1.0, 
        "unit": "%", 
        "decimals": 2
    }
]
