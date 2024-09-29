import datetime
import os
import threading

import sounddevice as sd
import soundfile as sf

class VoiceRecorder:
    def __init__(self, output_file=None, device_index=None):
        self.chunk = 1024  # Размер блока данных
        self.channels = 1  # Каналы (моно)
        self.sample_rate = 44100  # Частота дискретизации
        self.device_index = device_index  # Индекс микрофона, если есть
        self.is_recording = False  # Флаг записи
        self.output_file = None
        self.recording = None

        if not os.path.exists("Save"):
            os.makedirs("Save")


    def start_recording(self):
        """Start recording and dynamically set the file name."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.output_file = os.path.join("Save", f"audio_{timestamp}.ogg")  # Record in .wav

        self.is_recording = True
        #print(f"Recording started: {self.output_file}")

        self.recording = threading.Thread(target=self._record, daemon=True)
        self.recording.start()

    def _record(self):
        """Частная функция для захвата аудио"""
        with sf.SoundFile(self.output_file, mode='w', samplerate=self.sample_rate, channels=self.channels, format='OGG') as file:
            with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, dtype='float32', device=self.device_index) as stream:
                while self.is_recording:
                    data = stream.read(self.sample_rate)[0]  # Читаем аудиоданные
                    file.write(data)  # Сохраняем данные в файл по частям

    def stop_recording(self):
        """Останавливаем запись и закрываем поток"""
        if not self.is_recording:
            return  # Запись уже остановлена
        self.is_recording = False
        if self.recording is not None:
            self.recording.join()
        #print(f"Запись завершена и сохранена в {self.output_file}")

    def close(self):
        """Закрываем аудиоинтерфейс"""
        sd.stop()


    def list_microphones(self):
        """Получаем список доступных микрофонов."""
        microphones = []
        for i in range(sd.query_devices()):
            device_info = sd.query_devices(i)
            if device_info['max_input_channels'] > 0:
                microphones.append((i, device_info['name']))
        return microphones
