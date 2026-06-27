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
        
        # O AudioManager busca seus próprios dados!
        audio_cfg = self.cfg.data.get("audio", {})
        self.device_index = audio_cfg.get("device_index")
        self.gain = audio_cfg.get("gain", 1.0)
        self.noise_threshold = audio_cfg.get("noise_gate", 0.02)
        self.muted = False
        self.use_bandpass = audio_cfg.get("use_bandpass", True)

        self.eq_bands = [0.0] * 8 
        
        self.volume = 0.0
        self.stream = None
        self.vol_buffer = deque(maxlen=3)

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
                    # Multiplicador progressivo para realçar agudos e normalizar o visual
                    weight = 1.0 + (i * 0.3)
                    raw_val = (np.mean(b) * self.gain * weight) / 35.0 
                    target = np.clip(raw_val, 0.0, 1.0)
                    
                    # Animação Suave (Sobe rápido, desce um pouco mais devagar)
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

        # 2. Cálculo de Volume e ENVELOPE FOLLOWER (Corrige o corte da animação)
        rms = np.sqrt(np.mean(signal_filtered ** 2))
        vol_total = rms * self.gain
        
        target_vol = 0.0 if vol_total < self.noise_threshold else min(vol_total, 1.0)

        # O Segredo: Sobe em 80% (rápido), desce em 8% (suave). Liga as sílabas da voz!
        if target_vol > self.volume:
            self.volume += (target_vol - self.volume) * 0.8
        else:
            self.volume += (target_vol - self.volume) * 0.08 

        self.volumeChanged.emit(self.volume)
        self.audioProcessed.emit(self.volume, self.eq_bands)

    def start(self):
        if self.stream: self.stop()
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
        except Exception as e:
            print(f"❌ Erro ao iniciar áudio: {e}")

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def get_volume(self): 
        return self.volume
    
    def set_muted(self, state):
        """Define o estado de mudo explicitamente e notifica a UI de forma reativa."""
        self.muted = state
        self.muteToggled.emit(self.muted)

    def toggle_mute(self): 
        """Inverte o estado de mudo e dispara o sinal reativo correspondente."""
        self.muted = not self.muted
        self.muteToggled.emit(self.muted)
        return self.muted
    
    def change_device(self, new_index): 
        self.device_index = new_index
        # O próprio gestor agora grava o novo dispositivo
        self.cfg.data.setdefault("audio", {})["device_index"] = new_index
        self.cfg.save()
        self.start()

    def set_auto_ducking(self, state):
        """Define e grava o estado do Auto-Ducking."""
        self.cfg.data.setdefault("audio", {})["auto_ducking"] = state
        self.cfg.save()

    def set_visualizer_enabled(self, state):
        """Define e grava se o visualizador está ativo."""
        self.cfg.data.setdefault("visualizer", {})["enabled"] = state
        self.cfg.save()

    def set_visualizer_style(self, style):
        """Define e grava o estilo visual do visualizador."""
        self.cfg.data.setdefault("visualizer", {})["style"] = style
        self.cfg.save()

    def set_mode(self, mode):
        """Define e grava o modo de voz (smooth ou standard)."""
        self.cfg.data.setdefault("audio", {})["mode"] = mode
        self.cfg.save()

    def set_hold_time(self, val):
        """Define e grava o tempo de retenção do áudio."""
        self.cfg.data.setdefault("audio", {})["hold_time"] = val
        self.cfg.save()

    def set_threshold(self, key, val):
        """Define e grava os limites (thresholds) de ativação por chave (low, med, etc)."""
        self.cfg.data.setdefault("audio", {}).setdefault("thresholds", {})[key] = val
        self.cfg.save()

    @staticmethod
    def get_input_devices():
        devices = sd.query_devices()
        return {i: d['name'] for i, d in enumerate(devices) if d['max_input_channels'] > 0}