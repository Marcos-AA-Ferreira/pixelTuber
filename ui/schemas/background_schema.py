# src/ui/schemas/background_schema.py

# Opções de camada centralizadas para manter a integridade visual
LAYER_OPTIONS = [
    " Fundo (Atrás do Avatar)⬇️ ", 
    " Normal🟦 ", 
    " Sobrepor ⬆️ (Frente do Avatar)"
]

VISUAL_SCHEMA = [
    {
        "type": "combobox", 
        "key": "bg_layer_level", 
        "title": "Profundidade da Camada:", 
        "options": LAYER_OPTIONS, 
        "default": LAYER_OPTIONS[0]
    },
    {
        "type": "custom_slider", 
        "key": "bg_opacity", 
        "title": "Nível de Opacidade:", 
        "min_val": 0, "max_val": 100, "default": 100, "unit": "%"
    },
    {
        "type": "custom_slider", 
        "key": "bg_blur", 
        "title": "Intensidade do Desfoque:", 
        "min_val": 0, "max_val": 50, "default": 0, "unit": " px"
    }
]

AUDIO_TOP_SCHEMA = [
    {
        "type": "combobox", 
        "key": "system.toast_position", 
        "title": "Posição da Notificação (Toast):", 
        "options": [
            "Canto Inferior Direito", 
            "Canto Inferior Esquerdo", 
            "Canto Superior Direito", 
            "Canto Superior Esquerdo"
        ], 
        "default": "Canto Inferior Direito"
    }
]

AUDIO_BOTTOM_SCHEMA = [
    {
        "type": "switch", 
        "key": "bg_music_loop", 
        "title": "  Loop Automático🔂 ", 
        "default": True
    },
    {
        "type": "custom_slider", 
        "key": "bg_music_vol", 
        "title": "Volume Principal:", 
        "min_val": 0, "max_val": 100, "default": 50, "unit": "%"
    },
    {
        "type": "switch", 
        "key": "bg_music_muted", 
        "title": "  Mudo🔇 ", 
        "default": False
    }
]