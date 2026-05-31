# core/audio_manager.py
import sounddevice as sd
import numpy as np
from collections import deque

class AudioManager:
    def __init__(self, device_index=None, gain=1.0, sample_rate=44100):
        # --- Configurações de Hardware ---
        self.device_index = device_index
        self.sample_rate = sample_rate
        
        # --- Parâmetros de Processamento ---
        self.gain = gain
        self.noise_threshold = 0.02 # Ignora sons abaixo disto
        self.muted = False
        
        # --- Estado Interno ---
        self.volume = 0.0
        self.stream = None
        
        # Buffer para suavização rápida de leitura (opcional)
        self.vol_buffer = deque(maxlen=3)

    def audio_callback(self, indata, frames, time, status):
        """Processamento matemático do som (executado em thread de alta prioridade)."""
        if status:
            return

        if self.muted:
            self.volume = 0.0
            return

        # 1. Extração do sinal (Mono)
        signal = indata[:, 0]
        
        # 2. Cálculo de RMS (Intensidade Sonora)
        rms = np.sqrt(np.mean(signal ** 2))
        
        # 3. Aplicação do Ganho
        vol_total = rms * self.gain
        
        # 4. Noise Gate (Filtro de ruído de fundo)
        if vol_total < self.noise_threshold:
            self.volume = 0.0
        else:
            self.volume = min(vol_total, 1.0) # Limita a 1.0 (100%)

    def start(self):
        """Inicia a escuta do microfone."""
        if self.stream:
            self.stop()
            
        try:
            self.stream = sd.InputStream(
                channels=1,
                callback=self.audio_callback,
                device=self.device_index,
                samplerate=self.sample_rate,
                blocksize=1024
            )
            self.stream.start()
        except Exception as e:
            print(f"Erro ao iniciar áudio: {e}")

    def stop(self):
        """Fecha a stream de áudio com segurança."""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def get_volume(self):
        """Retorna o volume processado no callback."""
        return self.volume

    def toggle_mute(self):
        """Ativa/Desativa a captura de volume sem fechar a stream."""
        self.muted = not self.muted
        return self.muted

    def change_device(self, new_index):
        """Troca o microfone ativo em tempo real."""
        self.device_index = new_index
        self.start()

    @staticmethod
    def get_input_devices():
        """Auxiliar para preencher a ComboBox no painel de controlo."""
        devices = sd.query_devices()
        return {i: d['name'] for i, d in enumerate(devices) if d['max_input_channels'] > 0}