import datetime
import os
import threading
import time
import tkinter as tk
import customtkinter as ctk
import pygame
import sounddevice as sd
import soundfile as sf
from utils import threaded

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

class AudioMessageWidget(ctk.CTkFrame):
    def __init__(self, parent, audio_file, duration, size, chat_app, **kwargs):
        super().__init__(parent, **kwargs)

        # Инстанцируем аудиоплеер
        self.audio_player = AudioPlayer()
        self.audio_file = audio_file
        self.duration = duration
        self.size = size
        self.current_time = 0
        self.chat_app = chat_app

        # Загружаем аудиофайл
        self.audio_player.load_audio(audio_file)

        self.configure(corner_radius=15, fg_color="#333")
        self.inner_frame = ctk.CTkFrame(self, fg_color="#333", corner_radius=15)
        self.inner_frame.pack(padx=5, pady=5, fill=tk.X)

        # Кнопка воспроизведения (делаем круглой)
        self.play_button = ctk.CTkButton(
            self.inner_frame, text="▶", command=self.toggle_play,
            fg_color="#444", text_color="white", hover_color="#555",
            width=40, height=40, corner_radius=20  # Круглая форма
        )
        self.play_button.grid(row=0, column=0, padx=5, pady=5, sticky="ns")  # Центрируем по вертикали

        self.waveform = ctk.CTkLabel(self.inner_frame, text="=== Waveform ===", text_color='white', fg_color='#333')
        self.waveform.grid(row=0, column=1, columnspan=2)

        self.time_label = ctk.CTkLabel(self.inner_frame, text="00:00 / " + self.format_time(self.duration), text_color='white', fg_color='#333')
        self.time_label.grid(row=1, column=1, pady=5)

        # Размер файла
        self.size_label = ctk.CTkLabel(self.inner_frame, text=f"{size} KB", text_color='white', fg_color='#333')
        self.size_label.grid(row=1, column=2, padx=5, sticky="e")

        self.timer_id = None

    @threaded
    def toggle_play(self):
        # Проверяем, если уже есть активный виджет аудио и это не текущий виджет
        if self.chat_app.active_audio_widget and self.chat_app.active_audio_widget != self:
            # Останавливаем предыдущий активный аудио виджет
            self.chat_app.active_audio_widget.stop_audio()

        if not self.audio_player.is_playing and not self.audio_player.is_paused and self.play_button.cget("text") == "▶":
            # Запускаем воспроизведение
            self.audio_player.load_audio(self.audio_file)
            self.audio_player.play_audio(self.on_audio_complete)
            self.play_button.configure(text="⏸")
            self.update_time()

            # Устанавливаем текущий виджет как активный
            self.chat_app.active_audio_widget = self

        elif self.audio_player.is_paused:
            # Возобновляем воспроизведение с текущей позиции
            self.audio_player.play_audio(self.on_audio_complete)
            self.play_button.configure(text="⏸")
            self.update_time()

            # Устанавливаем текущий виджет как активный
            self.chat_app.active_audio_widget = self

        else:
            # Ставим на паузу
            self.audio_player.pause_audio()
            self.play_button.configure(text="▶")


    def stop_audio(self):
        """Функция для остановки аудио и сброса состояния."""
        self.audio_player.stop_audio()
        self.play_button.configure(text="▶")
        self.current_time = 0
        self.time_label.configure(text=f"{self.format_time(self.current_time)} / {self.format_time(self.duration)}")

    @threaded
    def update_time(self):
        """Обновляем отображение текущего времени аудио."""
        while self.audio_player.is_playing:
            self.current_time = pygame.mixer.music.get_pos() // 1000  # Получаем текущее время в секундах
            self.time_label.configure(text=f"{self.format_time(self.current_time)} / {self.format_time(self.duration)}")
            time.sleep(1)

    def format_time(self, seconds):
        """Форматируем время в минуты и секунды."""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02}:{secs:02}"

    def on_audio_complete(self):
        """Вызывается, когда аудио заканчивается."""
        self.play_button.configure(text="▶")  # Сбрасываем кнопку в начальное состояние
        self.current_time = 0
        self.time_label.configure(text=f"{self.format_time(self.current_time)} / {self.format_time(self.duration)}")
        self.audio_player.stop_audio()  # Останавливаем воспроизведение



class AudioPlayer:
    def __init__(self):
        pygame.mixer.init()  # Инициализация микшера Pygame
        self.is_playing = False
        self.is_paused = False
        self.audio_file = None

    def load_audio(self, file_path):
        """Загружаем аудиофайл в Pygame."""
        self.audio_file = file_path
        pygame.mixer.music.load(self.audio_file)

    def play_audio(self, on_complete_callback):
        """Запуск или возобновление воспроизведения с сохраненной позиции."""
        if not self.is_playing and not self.is_paused:
            # Начинаем воспроизведение сначала
            pygame.mixer.music.play()
            self.is_playing = True
            # Запускаем проверку завершения аудио в отдельном потоке
            threading.Thread(target=self._check_audio_complete, args=(on_complete_callback,)).start()
        elif self.is_paused:
            # Возобновляем воспроизведение с паузы
            pygame.mixer.music.unpause()
            self.is_playing = True
            self.is_paused = False

    def pause_audio(self):
        """Ставим на паузу."""
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.is_playing = False

    def stop_audio(self):
        """Останавливаем аудио."""
        pygame.mixer.music.stop()
        self.is_paused = False
        self.is_playing = False

    def _check_audio_complete(self, on_complete_callback):
        """Проверка завершения аудио для вызова коллбэка."""
        while pygame.mixer.music.get_busy() or self.is_paused:
            time.sleep(0.1)
        on_complete_callback()  # Аудио завершено, вызываем коллбэк
