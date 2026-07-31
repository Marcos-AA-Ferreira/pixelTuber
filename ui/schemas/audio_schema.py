# src/ui/schemas/audio_schema.py

# Se você já estiver usando o constants.py rigorosamente, 
# pode importar as chaves aqui (ex: AudioKeys.GAIN). 
# Por enquanto, manterei as strings literais originais do seu código para não quebrar nada.

VISUALIZER_SCHEMA = [
    {
        "type": "combobox",
        "key": "style",
        "title": "Estilo do Gráfico:",
        "options": ["Clássico", "Onda Contínua", "Barras Digitais", "Neon Simétrico", "Pontos de Energia"],
        "default": "Clássico"
    }
]

PROCESSING_SCHEMA = [
    {
        "type": "custom_slider", 
        "key": "gain",
        "title": "Ganho do Microfone (Volume de Entrada):",
        "min_val": 0, "max_val": 5, "default": 1.0, "step": 0.1, "unit": "x",
        "ticks": [("0x", 0), ("1x", 1), ("5x", 5)], "decimals": 1
    },
    {
        "type": "custom_slider", 
        "key": "noise_gate",
        "title": "Noise Gate (Corte de Ruído):",
        "min_val": 0, "max_val": 1, "default": 0.02, "step": 0.01, "unit": "",
        "ticks": [("0", 0), ("0.5", 0.5), ("1", 1)], "decimals": 2
    },
    {
        "type": "custom_slider", 
        "key": "hold_time",
        "title": "Tempo de Retenção (Hold Time):",
        "min_val": 0, "max_val": 1000, "default": 200, "step": 10, "unit": " ms",
        "decimals": 0
    },
    {
        "type": "switch", 
        "key": "auto_ducking",
        "title": "Auto-Ducking (Abaixar música de fundo ao falar)",
        "default": False
    }
]