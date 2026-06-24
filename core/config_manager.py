# core/config_manager.py
import json
import os

class ConfigManager:
    def __init__(self, profiles_dir="profiles", main_config="config/config.json"):
        self.profiles_dir = profiles_dir
        self.current_path = main_config
        
        if not os.path.exists(self.profiles_dir):
            os.makedirs(self.profiles_dir)

        # --- CORREÇÃO: "device_index" no lugar de "device" ---
        self.default_data = {
            "render": {"scale": 1.0, "x": 100, "y": 100, "locked": False, "chroma_key": "transparent"},
            "audio": {
                "gain": 1.0, 
                "device_index": None, 
                "thresholds": {"low": 0.05, "med": 0.2, "high": 0.5, "very_high": 0.8},
                "mode": "smooth",
                "hold_time": 0.2,
                "use_bandpass": True,
                "auto_ducking": True
            },
            "visualizer": {
                "enabled": False,
                "style": "Clássico"
            },
            "animations": {
                "main_set": "default",
                "sets": {"default": {"mute": "", "low": "", "med": "", "high": "", "very_high": ""}}
            },
            "aux_layers": {},
            "hotkeys": {"toggle_lock": "shift+f", "next_set": "shift+t"},
            "custom_effects": {},
            "system": {"fps_limit": "60 FPS", "minimize_to_tray": False}
        }
        
        self.data = self.load(self.current_path)

    def load(self, path):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    user_data = json.load(f)
                    return self._recursive_merge(self.default_data, user_data)
            except Exception as e:
                print(f"Erro ao carregar config {path}: {e}")
                return self.default_data.copy()
        return self.default_data.copy()

    def _recursive_merge(self, default, user):
        res = default.copy()
        for k, v in user.items():
            if isinstance(v, dict) and k in res:
                res[k] = self._recursive_merge(res[k], v)
            else:
                res[k] = v
        return res

    def save(self):
        try:
            with open(self.current_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao guardar configuração: {e}")

    def switch_profile(self, profile_name):
        self.save()
        if profile_name == "default":
            self.current_path = "config.json"
        else:
            self.current_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
        self.data = self.load(self.current_path)

    def list_profiles(self):
        profiles = ["default"]
        if os.path.exists(self.profiles_dir):
            files = [f.replace(".json", "") for f in os.listdir(self.profiles_dir) if f.endswith(".json")]
            profiles.extend(files)
        return profiles

    def delete_profile(self, profile_name):
        if profile_name == "default": return
        path = os.path.join(self.profiles_dir, f"{profile_name}.json")
        if os.path.exists(path):
            os.remove(path)