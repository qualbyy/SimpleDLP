import sys
import subprocess
import os
import threading
import shutil
import urllib.request
import json
from datetime import datetime

THEME = "blue"
APPEARANCE_MODE = "System"
LANG = "RU"

def check_and_install_packages():
    try:
        import customtkinter
    except ImportError:
        print("Установка customtkinter...")
        command = [sys.executable, "-m", "pip", "install", "customtkinter"]
        if sys.platform.startswith("linux"):
            command.append("--break-system-packages")
        subprocess.check_call(command)
        os.execv(sys.executable, ['python'] + sys.argv)

def download_file(url, path):
    try:
        with urllib.request.urlopen(url) as response, open(path, "wb") as out_file:
            shutil.copyfileobj(response, out_file)
        os.chmod(path, 0o755)
        return True
    except Exception as e:
        print(f"Ошибка скачивания {url}: {e}")
        return False

def ensure_bin_tools_linux(bin_dir, ytdlp_path, ffmpeg_path):
    YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
    FFMPEG_URL = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
    if not os.path.exists(ytdlp_path):
        os.makedirs(bin_dir, exist_ok=True)
        download_file(YTDLP_URL, ytdlp_path)
    if not os.path.exists(ffmpeg_path):
        os.makedirs(bin_dir, exist_ok=True)
        archive_path = os.path.join(bin_dir, "ffmpeg.tar.xz")
        if download_file(FFMPEG_URL, archive_path):
            import tarfile
            try:
                with tarfile.open(archive_path, "r:xz") as tar:
                    for member in tar.getmembers():
                        if member.isfile() and member.name.endswith("/ffmpeg"):
                            tar.extract(member, bin_dir)
                            extracted_path = os.path.join(bin_dir, os.path.basename(member.name))
                            shutil.move(extracted_path, ffmpeg_path)
                            os.chmod(ffmpeg_path, 0o755)
                            break
                os.remove(archive_path)
            except Exception as e:
                print(f"Ошибка при распаковке ffmpeg: {e}")

def ensure_tools(bin_dir, ytdlp_path, ffmpeg_path):
    if sys.platform == "win32":
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            "Manual Download Required",
            (
                "Скачайте yt-dlp.exe и ffmpeg.exe вручную:\n"
                "yt-dlp.exe: https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe\n"
                "ffmpeg.exe: https://www.gyan.dev/ffmpeg/builds/\n"
                "Положите их в папку 'bin'."
            )
        )
    else:
        ensure_bin_tools_linux(bin_dir, ytdlp_path, ffmpeg_path)

CONFIG_PATH = None

def load_settings():
    global LANG, THEME, APPEARANCE_MODE
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            LANG = data.get("LANG", LANG)
            THEME = data.get("THEME", THEME)
            APPEARANCE_MODE = data.get("APPEARANCE_MODE", APPEARANCE_MODE)
            return data
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
    return {}

def save_settings(quality_var, audio_var):
    data = {
        "LANG": LANG,
        "THEME": THEME,
        "APPEARANCE_MODE": APPEARANCE_MODE,
        "QUALITY": quality_var.get(),
        "AUDIO_ONLY": audio_var.get()
    }
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Ошибка сохранения настроек: {e}")

def main():
    global THEME, LANG, APPEARANCE_MODE, CONFIG_PATH
    check_and_install_packages()
    import customtkinter
    from tkinter import messagebox, filedialog

    SCRIPTDIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_PATH = os.path.join(SCRIPTDIR, "config.json")

    settings = load_settings()

    customtkinter.set_appearance_mode(settings.get("APPEARANCE_MODE", APPEARANCE_MODE))
    customtkinter.set_default_color_theme(settings.get("THEME", THEME))

    BIN_DIR = os.path.join(SCRIPTDIR, "bin")
    if sys.platform == "win32":
        YTDLPPATH = os.path.join(BIN_DIR, "yt-dlp.exe")
        FFMPEGPATH = os.path.join(BIN_DIR, "ffmpeg.exe")
    else:
        YTDLPPATH = os.path.join(BIN_DIR, "yt-dlp")
        FFMPEGPATH = os.path.join(BIN_DIR, "ffmpeg")
    STREAMLINKPATH = "streamlink"

    ensure_tools(BIN_DIR, YTDLPPATH, FFMPEGPATH)

    current_process = None
    download_log = []

    def ensure_dependencies():
        missing_files = []
        if not os.path.exists(YTDLPPATH): missing_files.append(os.path.basename(YTDLPPATH))
        if not os.path.exists(FFMPEGPATH): missing_files.append(os.path.basename(FFMPEGPATH))
        if missing_files:
            messagebox.showerror("Dependency Error", f"Не найдены файлы: {', '.join(missing_files)}\n\nПоместите их в папку 'bin'.")
            return False
        return True

    def append_text(text):
        output_text.configure(state="normal")
        output_text.insert("end", text + "\n")
        output_text.see("end")
        output_text.configure(state="disabled")
        download_log.append(f"{datetime.now().strftime('%H:%M:%S')}: {text}")

    def save_log():
        fname = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if fname:
            with open(fname, "w", encoding="utf-8") as f:
                f.write("\n".join(download_log))
            append_text("Лог сохранен.")

    def start_stream():
        threading.Thread(target=_start_stream_task, daemon=True).start()

    def _start_stream_task():
        nonlocal current_process
        if not ensure_dependencies():
            append_text("Отсутствуют зависимости для стрима")
            return
        stream_url = stream_url_entry.get().strip()
        if not stream_url:
            append_text("Введите ссылку на стрим")
            return
        append_text(f"Запуск записи стрима: {stream_url}")
        stop_button.configure(state="normal")
        vods_dir = os.path.join(SCRIPTDIR, "vods")
        os.makedirs(vods_dir, exist_ok=True)
        cmd = f'"{STREAMLINKPATH}" --hls-live-restart "{stream_url}" best -O | "{FFMPEGPATH}" -i - -c copy "{os.path.join(vods_dir, "stream.mp4")}"'
        current_process = subprocess.Popen(cmd, shell=True)
        append_text("Stream capture started.")
        current_process.wait()
        append_text("Stream capture finished.")
        stop_button.configure(state="disabled")
        messagebox.showinfo("Stream finished", "Stream recording finished.")

    def start_video_download_thread():
        threading.Thread(target=_start_video_download_task, daemon=True).start()

    def _start_video_download_task():
        nonlocal current_process
        if not ensure_dependencies():
            append_text("Отсутствуют зависимости для видео")
            return
        videos_dir = os.path.join(SCRIPTDIR, "videos")
        os.makedirs(videos_dir, exist_ok=True)
        video_url = video_url_entry.get().strip()
        if not video_url:
            append_text("Введите ссылку на видео")
            return
        cookies_path = cookies_path_entry.get().strip()
        append_text(f"Начало загрузки видео: {video_url}")
        stop_button.configure(state="normal")

        format_code = quality_var.get()
        if audio_var.get():
            format_code = "bestaudio"
            output_format = "mp3"
        else:
            output_format = "mp4"

        out_template = f'"{os.path.join(videos_dir, "%(title)s.%(ext)s")}"'

        cmd_parts = [
            f'"{YTDLPPATH}"',
            '--ffmpeg-location',
            f'"{os.path.dirname(FFMPEGPATH)}"',
            '-f',
            format_code,
            '--merge-output-format',
            output_format,
            '-o',
            out_template,
            f'"{video_url}"'
        ]
        if cookies_path:
            cmd_parts.insert(1, f'--cookies "{cookies_path}"')
        cmd = " ".join(cmd_parts)
        append_text(f"Команда: {cmd}")

        current_process = subprocess.Popen(cmd, shell=True)
        current_process.wait()
        append_text("Загрузка видео завершена.")
        stop_button.configure(state="disabled")
        messagebox.showinfo("Загрузка завершена", "Видео успешно загружено.")
        current_process = None

    def stop_download():
        nonlocal current_process
        if current_process and current_process.poll() is None:
            try:
                if sys.platform == "win32":
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(current_process.pid)])
                else:
                    os.killpg(os.getpgid(current_process.pid), 9)
                append_text("Загрузка остановлена.")
            except Exception as e:
                append_text(f"Ошибка при остановке: {e}")
        else:
            append_text("Нет активного процесса загрузки.")
        stop_button.configure(state="disabled")
        current_process = None

    def browse_cookies():
        path = filedialog.askopenfilename(title="Выберите cookies.txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            cookies_path_entry.delete(0, "end")
            cookies_path_entry.insert(0, path)

    def open_videos_folder():
        videos_dir = os.path.join(SCRIPTDIR, "videos")
        open_downloads_folder(videos_dir)

    def open_downloads_folder(folder):
        if sys.platform.startswith("linux"):
            subprocess.Popen(["xdg-open", folder])
        elif sys.platform == "win32":
            os.startfile(folder)

    class App(customtkinter.CTk):
        def __init__(self):
            super().__init__()
            self.title("SimpleDLP")
            self.geometry("820x700")
            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(5, weight=1)

            # Переводы
            self.translations = {
                "RU": {
                    "appearance": "Внешний вид:",
                    "language": "Язык:",
                    "stream_url": "Ссылка на стрим:",
                    "video_url": "Ссылка на видео:",
                    "cookies_file": "Файл cookies:",
                    "browse": "Выбрать...",
                    "format": "Формат:",
                    "show_formats": "Показать форматы",
                    "audio_only": "Только аудио (mp3)",
                    "record_stream": "Записать стрим",
                    "download_video": "Скачать видео",
                    "open_folder": "Открыть папку",
                    "update_tools": "Обновить утилиты",
                    "stop": "Остановить",
                    "save_log": "Сохранить лог",
                    "title": "SIMPLEDLP",
                    "contacts": "YouTube: @qualby   |   Discord: qualbyyyy   |   Telegram: @qualbyy",
                },
                "EN": {
                    "appearance": "Appearance:",
                    "language": "Language:",
                    "stream_url": "Stream URL:",
                    "video_url": "Video URL:",
                    "cookies_file": "Cookies File:",
                    "browse": "Browse...",
                    "format": "Format:",
                    "show_formats": "Show formats",
                    "audio_only": "Audio only (mp3)",
                    "record_stream": "Record stream",
                    "download_video": "Download video",
                    "open_folder": "Open folder",
                    "update_tools": "Update tools",
                    "stop": "Stop",
                    "save_log": "Save log",
                    "title": "SIMPLEDLP",
                    "contacts": "YouTube: @qualby   |   Discord: qualbyyyy   |   Telegram: @qualbyy",
                }
            }

            # Все виджеты используемые для локализации - как атрибуты self
            self.title_label = customtkinter.CTkLabel(self, font=customtkinter.CTkFont(size=32, weight="bold"))
            self.title_label.grid(row=0, column=0, padx=20, pady=(16, 5), sticky="n")

            switches_frame = customtkinter.CTkFrame(self)
            switches_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
            switches_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

            self.appearance_label = customtkinter.CTkLabel(switches_frame)
            self.appearance_label.grid(row=0, column=0, padx=5)
            appearance_menu = customtkinter.CTkOptionMenu(switches_frame, values=["System", "Dark", "Light"], command=self.change_appearance_mode)
            appearance_menu.grid(row=0, column=1, padx=5)

            self.language_label = customtkinter.CTkLabel(switches_frame)
            self.language_label.grid(row=0, column=2, padx=5)
            lang_menu = customtkinter.CTkOptionMenu(switches_frame, values=["RU", "EN"], command=self.change_language)
            lang_menu.set(LANG)
            lang_menu.grid(row=0, column=3, padx=5)

            input_frame = customtkinter.CTkFrame(self)
            input_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
            input_frame.grid_columnconfigure(1, weight=1)

            self.stream_label = customtkinter.CTkLabel(input_frame)
            self.stream_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            nonlocal stream_url_entry
            stream_url_entry = customtkinter.CTkEntry(input_frame, placeholder_text="https://...")
            stream_url_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

            self.video_label = customtkinter.CTkLabel(input_frame)
            self.video_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
            nonlocal video_url_entry
            video_url_entry = customtkinter.CTkEntry(input_frame, placeholder_text="https://...")
            video_url_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

            self.cookies_label = customtkinter.CTkLabel(input_frame)
            self.cookies_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
            nonlocal cookies_path_entry
            cookies_path_entry = customtkinter.CTkEntry(input_frame, placeholder_text="C:/path/to/cookies.txt")
            cookies_path_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
            self.browse_button = customtkinter.CTkButton(input_frame, command=browse_cookies)
            self.browse_button.grid(row=2, column=2, padx=10, pady=10)

            self.format_label = customtkinter.CTkLabel(input_frame)
            self.format_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
            nonlocal quality_var
            quality_var = customtkinter.StringVar(value=settings.get("QUALITY", "bestvideo+bestaudio"))
            quality_menu = customtkinter.CTkOptionMenu(input_frame, values=["bestvideo+bestaudio", "best", "worst", "bestaudio"], variable=quality_var)
            quality_menu.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
            self.show_formats_button = customtkinter.CTkButton(input_frame, command=lambda: self.show_formats(video_url_entry.get().strip()))
            self.show_formats_button.grid(row=3, column=2, padx=10, pady=10)

            nonlocal audio_var
            audio_var = customtkinter.BooleanVar(value=settings.get("AUDIO_ONLY", False))
            self.audio_checkbox = customtkinter.CTkCheckBox(input_frame, variable=audio_var)
            self.audio_checkbox.grid(row=4, column=1, padx=10, pady=(0, 10), sticky="w")

            button_frame = customtkinter.CTkFrame(self)
            button_frame.grid(row=3, column=0, padx=20, pady=(0, 6), sticky="ew")
            button_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

            self.record_stream_button = customtkinter.CTkButton(button_frame, command=start_stream)
            self.record_stream_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

            self.download_video_button = customtkinter.CTkButton(button_frame, command=start_video_download_thread)
            self.download_video_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

            self.open_folder_button = customtkinter.CTkButton(button_frame, command=open_videos_folder)
            self.open_folder_button.grid(row=0, column=2, padx=10, pady=10, sticky="ew")

            self.update_tools_button = customtkinter.CTkButton(button_frame, command=lambda: update_bin_tools(BIN_DIR, YTDLPPATH, FFMPEGPATH, append_text))
            self.update_tools_button.grid(row=0, column=3, padx=10, pady=10, sticky="ew")

            nonlocal stop_button
            stop_button = customtkinter.CTkButton(button_frame, fg_color="#D32F2F", hover_color="#B71C1C", state="disabled",
                                                  command=stop_download)
            stop_button.grid(row=1, column=0, columnspan=4, padx=10, pady=8, sticky="ew")

            self.save_log_button = customtkinter.CTkButton(button_frame, command=save_log)
            self.save_log_button.grid(row=2, column=0, columnspan=4, padx=10, pady=6, sticky="ew")

            nonlocal output_text
            output_text = customtkinter.CTkTextbox(self, state="disabled")
            output_text.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="nsew")

            self.contacts_label = customtkinter.CTkLabel(self, font=customtkinter.CTkFont(size=13), text_color="#888")
            self.contacts_label.grid(row=5, column=0, pady=(6, 10), sticky="s")

            # Применить язык после создания всех виджетов
            self.change_language(LANG)

        def show_formats(self, url):
            show_formats(url, YTDLPPATH, append_text)

        def change_language(self, choice):
            global LANG
            LANG = choice
            t = self.translations.get(LANG, self.translations["EN"])
            self.title_label.configure(text=t["title"])
            self.appearance_label.configure(text=t["appearance"])
            self.language_label.configure(text=t["language"])
            self.stream_label.configure(text=t["stream_url"])
            self.video_label.configure(text=t["video_url"])
            self.cookies_label.configure(text=t["cookies_file"])
            self.browse_button.configure(text=t["browse"])
            self.format_label.configure(text=t["format"])
            self.show_formats_button.configure(text=t["show_formats"])
            self.audio_checkbox.configure(text=t["audio_only"])
            self.record_stream_button.configure(text=t["record_stream"])
            self.download_video_button.configure(text=t["download_video"])
            self.open_folder_button.configure(text=t["open_folder"])
            self.update_tools_button.configure(text=t["update_tools"])
            stop_button.configure(text=t["stop"])
            self.save_log_button.configure(text=t["save_log"])
            self.contacts_label.configure(text=t["contacts"])

        def change_appearance_mode(self, choice):
            global APPEARANCE_MODE
            APPEARANCE_MODE = choice
            customtkinter.set_appearance_mode(APPEARANCE_MODE)

    stream_url_entry, video_url_entry, cookies_path_entry, stop_button, output_text, quality_var, audio_var = \
        None, None, None, None, None, None, None

    app = App()
    # Сохраняем настройки при закрытии
    def on_closing():
        save_settings(quality_var, audio_var)
        app.destroy()
    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()

if __name__ == "__main__":
    main()
