import os
import sys
from pathlib import Path
import whisper
import srt
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import subprocess

# Хардкод пути вывода
OUTPUT_DIR = r"D:\download\vid\app2024_исходники\саб3титры"

class AudioToTextApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio/Video to Text Converter")
        self.root.geometry("600x500")
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        main_frame = tk.Frame(root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.select_btn = tk.Button(
            btn_frame, text="Выбрать файл", command=self.select_file,
            font=("Arial", 12), bg="#4CAF50", fg="white", padx=20, pady=10
        )
        self.select_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.file_label = tk.Label(btn_frame, text="Файл не выбран", font=("Arial", 10), fg="gray")
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.convert_btn = tk.Button(
            main_frame, text="Конвертировать", command=self.start_conversion,
            font=("Arial", 12), bg="#2196F3", fg="white", padx=20, pady=10, state=tk.DISABLED
        )
        self.convert_btn.pack(pady=(0, 10))
        
        self.progress_label = tk.Label(main_frame, text="", font=("Arial", 10), fg="blue")
        self.progress_label.pack(pady=(0, 10))
        
        result_frame = tk.Frame(main_frame)
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(result_frame, text="Результат:", font=("Arial", 11, "bold")).pack(anchor=tk.W)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, font=("Consolas", 10), height=15)
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        self.status_bar = tk.Label(root, text="Готов к работе", bd=1, relief=tk.SUNKEN, anchor=tk.W, font=("Arial", 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.selected_file = None
    
    def select_file(self):
        filetypes = [
            ("Все поддерживаемые файлы", "*.mp3 *.wav *.m4a *.flac *.ogg *.aac *.wma *.mp4 *.avi *.mkv *.mov"),
            ("Аудио файлы", "*.mp3 *.wav *.m4a *.flac *.ogg *.aac *.wma"),
            ("Видео файлы", "*.mp4 *.avi *.mkv *.mov"),
            ("Все файлы", "*.*")
        ]
        
        filename = filedialog.askopenfilename(title="Выберите аудио или видео файл", filetypes=filetypes)
        
        if filename:
            self.selected_file = filename
            self.file_label.config(text=os.path.basename(filename), fg="black")
            self.convert_btn.config(state=tk.NORMAL)
            self.status_bar.config(text=f"Выбран файл: {os.path.basename(filename)}")
    
    def extract_audio_from_video(self, video_path):
        """Извлекает СТЕРЕО аудио для лучшего разделения музыки и голоса"""
        audio_path = os.path.join(OUTPUT_DIR, "temp_audio.wav")
        
        try:
            cmd = [
                'ffmpeg', '-i', video_path, '-vn',
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '2',  # <-- ВАЖНО: Стерео вместо моно
                '-y', audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"FFmpeg ошибка: {result.stderr}")
            return audio_path
            
        except FileNotFoundError:
            raise Exception("FFmpeg не найден! Установи FFmpeg и добавь в PATH")
    
    def start_conversion(self):
        if not self.selected_file:
            messagebox.showerror("Ошибка", "Сначала выберите файл!")
            return
        
        self.convert_btn.config(state=tk.DISABLED)
        self.select_btn.config(state=tk.DISABLED)
        
        thread = threading.Thread(target=self.convert_file, daemon=True)
        thread.start()
    
    def convert_file(self):
        temp_audio = None
        
        try:
            file_ext = Path(self.selected_file).suffix.lower()
            audio_path = self.selected_file
            
            if file_ext in ['.mp4', '.avi', '.mkv', '.mov']:
                self.update_status("Извлечение аудио из видео...")
                temp_audio = self.extract_audio_from_video(self.selected_file)
                audio_path = temp_audio
            
            self.update_status("Загрузка модели Whisper (medium)...")
            
            # medium - оптимально для русского + скорости. large-v2 только если есть RTX 3060+
            model = whisper.load_model("medium") 
            
            self.update_status("Транскрибация...")
            
            # ВАЖНЫЕ ПАРАМЕТРЫ ДЛЯ МУЗЫКИ И РУССКОГО ЯЗЫКА:
            result = model.transcribe(
                audio_path, 
                language="ru",           # Принудительно русский
                condition_on_previous_text=False,  # Не дает модели "залипать" на прошлых фразах
                no_speech_threshold=0.6  # Игнорирует тишину/музыку без слов
            )
            
            base_name = Path(self.selected_file).stem
            txt_path = os.path.join(OUTPUT_DIR, f"{base_name}.txt")
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(result['text'])
            
            subtitles = []
            for i, segment in enumerate(result['segments'], 1):
                start_time = srt.timedelta(seconds=segment['start'])
                end_time = srt.timedelta(seconds=segment['end'])
                subtitle = srt.Subtitle(
                    index=i, start=start_time, end=end_time,
                    content=segment['text'].strip()
                )
                subtitles.append(subtitle)
            
            srt_content = srt.compose(subtitles)
            srt_path = os.path.join(OUTPUT_DIR, f"{base_name}.srt")
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            if temp_audio and os.path.exists(temp_audio):
                os.remove(temp_audio)
            
            self.root.after(0, lambda: self.show_result(result['text'], txt_path, srt_path))
            
        except Exception as e:
            if temp_audio and os.path.exists(temp_audio):
                os.remove(temp_audio)
            self.root.after(0, lambda: self.show_error(str(e)))
    
    def update_status(self, message):
        self.root.after(0, lambda: self.progress_label.config(text=message))
    
    def show_result(self, text, txt_path, srt_path):
        self.convert_btn.config(state=tk.NORMAL)
        self.select_btn.config(state=tk.NORMAL)
        
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, text)
        
        self.progress_label.config(text="✓ Готово!")
        self.status_bar.config(text=f"Файлы сохранены в: {OUTPUT_DIR}")
        
        messagebox.showinfo("Успех", f"Конвертация завершена!\n\nTXT: {txt_path}\nSRT: {srt_path}")
    
    def show_error(self, error_message):
        self.convert_btn.config(state=tk.NORMAL)
        self.select_btn.config(state=tk.NORMAL)
        self.progress_label.config(text="✗ Ошибка")
        self.status_bar.config(text="Произошла ошибка")
        messagebox.showerror("Ошибка", f"Произошла ошибка:\n{error_message}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioToTextApp(root)
    root.mainloop()