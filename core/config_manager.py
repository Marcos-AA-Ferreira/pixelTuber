# core/config_manager.py
import json
import os

class ConfigManager:
    def __init__(self, profiles_dir="profiles", main_config="config.json"):
        self.profiles_dir = profiles_dir
        self.current_path = main_config
        
        # Garante que a pasta de perfis existe para evitar erros de escrita
        if not os.path.exists(self.profiles_dir):
            os.makedirs(self.profiles_dir)

        # Configuração Padrão (Fallback)
        self.default_data = {
            "render": {"scale": 1.0, "x": 100, "y": 100, "locked": False},
            "audio": {
                "gain": 1.0, 
                "device": None, 
                "thresholds": {"low": 0.05, "med": 0.2, "high": 0.5, "very_high": 0.8},
                "mode": "smooth",
                "hold_time": 0.2
            },
            "animations": {
                "main_set": "default",
                "sets": {"default": {"mute": "", "low": "", "med": "", "high": "", "very_high": ""}}
            },
            "aux_layers": {},
            "hotkeys": {"toggle_lock": "shift+f", "next_set": "shift+t"},
            "custom_effects": {}
        }
        
        self.data = self.load(self.current_path)

    def load(self, path):
        """Carrega um ficheiro JSON e funde-o com os padrões para evitar chaves em falta."""
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
        """Mescla dicionários aninhados sem perder sub-chaves."""
        res = default.copy()
        for k, v in user.items():
            if isinstance(v, dict) and k in res:
                res[k] = self._recursive_merge(res[k], v)
            else:
                res[k] = v
        return res

    def save(self):
        """Guarda os dados atuais no caminho do perfil ativo."""
        try:
            with open(self.current_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao guardar configuração: {e}")

    # --- Lógica de Perfis (Antigo ProfileManager) ---

    def switch_profile(self, profile_name):
        """Troca o perfil ativo e recarrega os dados."""
        self.save() # Guarda o perfil atual antes da troca
        
        if profile_name == "default":
            self.current_path = "config.json"
        else:
            self.current_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
            
        self.data = self.load(self.current_path)

    def list_profiles(self):
        """Retorna uma lista de nomes de perfis disponíveis."""
        profiles = ["default"]
        if os.path.exists(self.profiles_dir):
            files = [f.replace(".json", "") for f in os.listdir(self.profiles_dir) if f.endswith(".json")]
            profiles.extend(files)
        return profiles

    def delete_profile(self, profile_name):
        """Remove um ficheiro de perfil do disco."""
        if profile_name == "default": return
        path = os.path.join(self.profiles_dir, f"{profile_name}.json")
        if os.path.exists(path):
            os.remove(path)