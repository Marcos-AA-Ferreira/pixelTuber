class ConfigKeys:
    """Chaves principais do arquivo config.json."""
    RENDER = "render"
    AUDIO = "audio"
    VISUALIZER = "visualizer"
    ANIMATIONS = "animations"
    AUX_LAYERS = "aux_layers"
    HOTKEYS = "hotkeys"
    CUSTOM_EFFECTS = "custom_effects"
    SYSTEM = "system"

class AudioKeys:
    """Sub-chaves do domínio de Áudio."""
    GAIN = "gain"
    DEVICE_INDEX = "device_index"
    THRESHOLDS = "thresholds"
    MODE = "mode"
    HOLD_TIME = "hold_time"
    USE_BANDPASS = "use_bandpass"
    AUTO_DUCKING = "auto_ducking"
    NOISE_GATE = "noise_gate"
    STYLE = "style"

class SystemKeys:
    """Sub-chaves do domínio de Sistema."""
    FPS_LIMIT = "fps_limit"
    MINIMIZE_TO_TRAY = "minimize_to_tray"
    TOAST_POSITION = "toast_position"