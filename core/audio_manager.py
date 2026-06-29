# core/audio_manager.py
from PySide6.QtCore import QObject, Signal
import sounddevice as sd
import numpy as np
from collections import deque


class AudioManager(QObject):

    volumeChanged = Signal(float)
    muteToggled = Signal(bool)
    audioProcessed = Signal(float, list)

    def __init__(self, config_manager, sample_rate=None):
        super().__init__()
        self.cfg = config_manager
        self.sample_rate = sample_rate
        
        # --- O CORE BUSCA E CENTRALIZA SEUS PRÓPRIOS DADOS ---
        audio_cfg = self.cfg.data.get("audio", {})
        viz_cfg = self.cfg.data.get("visualizer", {})
        
        # Configurações do dispositivo e ganho
        self.device_index = audio_cfg.get("device_index")
        self.gain = audio_cfg.get("gain", 1.0)
        self.noise_threshold = audio_cfg.get("noise_gate", 0.02)
        self.muted = False
        self.use_bandpass = audio_cfg.get("use_bandpass", True)

        # Novas propriedades absorvidas para proteger o dicionário JSON da UI
        self.hold_time = audio_cfg.get("hold_time", 0.2)
        self.auto_ducking = audio_cfg.get("auto_ducking", True)
        self.mode = audio_cfg.get("mode", "standard")
        self.thresholds = audio_cfg.get("thresholds", {})
        
        # Propriedades do Visualizador controladas pelo Core
        self.visualizer_enabled = viz_cfg.get("enabled", False)
        self.visualizer_style = viz_cfg.get("style", "Clássico")

        # Estado dinâmico do fluxo
        self.eq_bands = [0.0] * 8 
        self.volume = 0.0
        self.stream = None
        self.vol_buffer = deque(maxlen=3)

    def get_filtered_input_devices(self):
        """
        Reinicia o subsistema de áudio de baixo nível, varre os hardwares disponíveis,
        aplica os filtros de exclusão e formata os nomes conforme a API de som ativa.
        Substitui inteiramente a lógica pesada que rodava dentro da UI.
        """
        try:
            sd._terminate()
            sd._initialize()
        except Exception:
            pass

        banned_words = ["mapeador", "mapper", "primary", "principal"]
        devices_list = []
        
        for i, d in enumerate(sd.query_devices()):
            if d['max_input_channels'] > 0:
                name = d['name']
                if any(banned in name.lower() for banned in banned_words):
                    continue
                try:
                    api = sd.query_hostapis(d['hostapi'])['name']
                except Exception:
                    api = "Desconhecido"
                
                # Formatação inteligente do nome de exibição
                display_name = name if "MME" in api else f"{name} [{api}]"
                devices_list.append((display_name, i))
                
        return devices_list

    def set_noise_gate(self, val):
        self.noise_threshold = val
        self.cfg.data.setdefault("audio", {})["noise_gate"] = val
        self.cfg.save()

    def set_gain(self, val):
        self.gain = val
        self.cfg.data.setdefault("audio", {})["gain"] = val
        self.cfg.save()
        
    def set_use_bandpass(self, state):
        self.use_bandpass = state
        self.cfg.data.setdefault("audio", {})["use_bandpass"] = state
        self.cfg.save()

    def audio_callback(self, indata, frames, time, status):
        """Callback do sounddevice processando blocos de áudio."""
        if status:
            print(status)

        if self.muted:
            self.volume = 0.0
            self.eq_bands = [0.0] * 8
            self.volumeChanged.emit(0.0)
            self.audioProcessed.emit(0.0, self.eq_bands)
            return

        signal = indata[:, 0]
        
        # 1. Transformada de Fourier (Para o Visualizador)
        try:
            fft_data = np.fft.rfft(signal)
            if self.sample_rate: 
                freqs = np.fft.rfftfreq(len(signal), d=1.0/self.sample_rate)
            else:
                freqs = np.fft.rfftfreq(len(signal), d=1.0/48000.0)
            
            # --- NOVA LÓGICA DE BARRAS (Mais Sensível e Fluida) ---
            magnitudes = np.abs(fft_data)
            limit_idx = len(magnitudes) // 3 
            if limit_idx > 8:
                bands_split = np.array_split(magnitudes[:limit_idx], 8)
                for i, b in enumerate(bands_split):
                    weight = 1.0 + (i * 0.3)
                    raw_val = (np.mean(b) * self.gain * weight) / 35.0 
                    target = np.clip(raw_val, 0.0, 1.0)
                    
                    if target > self.eq_bands[i]:
                        self.eq_bands[i] += (target - self.eq_bands[i]) * 0.7
                    else:
                        self.eq_bands[i] += (target - self.eq_bands[i]) * 0.15
            
            if self.use_bandpass:
                fft_data[(freqs < 300) | (freqs > 3000)] = 0
                
            signal_filtered = np.fft.irfft(fft_data)
        except Exception:
            signal_filtered = signal
            self.eq_bands = [0.0] * 8

        # 2. Cálculo de Volume e ENVELOPE FOLLOWER
        rms = np.sqrt(np.mean(signal_filtered ** 2))
        vol_total = rms * self.gain  # O ganho (ex: 2.0 para 200%) multiplica o RMS aqui
        
        # Se o volume total for menor que o corte de ruído, zera
        target_vol = 0.0 if vol_total < self.noise_threshold else min(vol_total, 1.0)

        # Ataque rápido para detectar o início da fala à noite, queda lenta
        if target_vol > self.volume:
            self.volume += (target_vol - self.volume) * 0.85
        else:
            self.volume += (target_vol - self.volume) * 0.15 

        self.volumeChanged.emit(self.volume)
        self.audioProcessed.emit(self.volume, self.eq_bands)

    def start(self):
        if self.stream: 
            self.stop()
            
        try:
            # Tenta validar se o dispositivo atual é de entrada
            if self.device_index is not None:
                sd.query_devices(self.device_index, 'input')
            else:
                raise ValueError("Nenhum dispositivo de áudio selecionado.")
        except Exception:
            # Caso o índice antigo seja inválido ou de saída, busca o padrão do sistema
            print(f"⚠️ Dispositivo index {self.device_index} inválido para entrada. Buscando padrão do sistema...")
            try:
                default_device = sd.default.device[0] # Índice padrão de gravação (Input)
                if default_device != -1:
                    self.device_index = default_device
                    # Atualiza o arquivo de configuração para corrigir futuros boots
                    self.cfg.data.setdefault("audio", {})["device_index"] = default_device
                    self.cfg.save()
                else:
                    print("❌ Nenhum dispositivo de entrada padrão encontrado no Windows.")
                    return
            except Exception as env_err:
                print(f"❌ Falha crítica ao obter dispositivo padrão de áudio: {env_err}")
                return

        try:
            device_info = sd.query_devices(self.device_index, 'input')
            native_sr = int(device_info['default_samplerate'])
            current_sr = self.sample_rate if self.sample_rate else native_sr
            self.sample_rate = current_sr 

            self.stream = sd.InputStream(
                channels=1, callback=self.audio_callback,
                device=self.device_index, samplerate=current_sr, blocksize=1024
            )
            self.stream.start()
            print(f"🎙️ Motor de áudio iniciado com sucesso no dispositivo index: {self.device_index}")
        except Exception as e:
            print(f"❌ Erro ao inicializar o InputStream de áudio: {e}")

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def get_volume(self): 
        return self.volume
    
    def set_muted(self, state):
        self.muted = state
        self.muteToggled.emit(self.muted)

    def toggle_mute(self): 
        self.muted = not self.muted
        self.muteToggled.emit(self.muted)
        return self.muted
    
    def change_device(self, new_index): 
        self.device_index = new_index
        self.cfg.data.setdefault("audio", {})["device_index"] = new_index
        self.cfg.save()
        self.start()

    def set_auto_ducking(self, state):
        """Define, sincroniza o estado interno e grava o Auto-Ducking."""
        self.auto_ducking = state
        self.cfg.data.setdefault("audio", {})["auto_ducking"] = state
        self.cfg.save()

    def set_visualizer_enabled(self, state):
        """Define, sincroniza o estado interno e grava se o visualizador está ativo."""
        self.visualizer_enabled = state
        self.cfg.data.setdefault("visualizer", {})["enabled"] = state
        self.cfg.save()

    def set_visualizer_style(self, style):
        """Define, sincroniza o estilo visual e grava."""
        self.visualizer_style = style
        self.cfg.data.setdefault("visualizer", {})["style"] = style
        self.cfg.save()

    def set_mode(self, mode):
        """Define, sincroniza o modo de voz (smooth ou standard) e grava."""
        self.mode = mode
        self.cfg.data.setdefault("audio", {})["mode"] = mode
        self.cfg.save()

    def set_hold_time(self, val):
        """Define, sincroniza o tempo de retenção do áudio e grava."""
        self.hold_time = val
        self.cfg.data.setdefault("audio", {})["hold_time"] = val
        self.cfg.save()

    def set_threshold(self, key, val):
        """Define, sincroniza os limites de ativação (thresholds) por chave e grava."""
        self.thresholds[key] = val
        self.cfg.data.setdefault("audio", {}).setdefault("thresholds", {})[key] = val
        self.cfg.save()

    def set_device_index(self, new_index):
        """Define e grava o índice do dispositivo de áudio atual e reinicia o stream."""
        self.device_index = new_index
        self.cfg.data.setdefault("audio", {})["device_index"] = new_index
        self.cfg.save()
        
        # Se o microfone mudar com o app rodando, para o antigo e inicia o novo
        if hasattr(self, 'stream') and self.stream is not None:
            self.stop()
        self.start()

    @staticmethod
    def get_input_devices():
        """Mantido por compatibilidade estática legado se necessário em outros escopos."""
        devices = sd.query_devices()
        return {i: d['name'] for i, d in enumerate(devices) if d['max_input_channels'] > 0}