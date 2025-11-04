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
        print("Installing customtkinter...")
        command = [sys.executable, "-m", "pip", "install", "customtkinter"]
        subprocess.check_call(command)
        os.execv(sys.executable, ['python'] + sys.argv)

def ensure_tools(bin_dir, ytdlp_path, ffmpeg_path):
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(
        "Manual Download Required",
        (
            "Please download yt-dlp.exe and ffmpeg.exe manually:\n\n"
            "yt-dlp.exe: https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe\n"
            "ffmpeg.exe: https://www.gyan.dev/ffmpeg/builds/\n\n"
            "Place them in the 'bin' folder next to this program."
        )
    )

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
            print(f"Loading settings error: {e}")
    return {}

def save_settings(app):
    data = {
        "LANG": LANG,
        "THEME": THEME,
        "APPEARANCE_MODE": APPEARANCE_MODE,
        "QUALITY": app.quality_var.get(),
        "AUDIO_ONLY": app.audio_var.get()
    }
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Saving settings error: {e}")

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
    YTDLPPATH = os.path.join(BIN_DIR, "yt-dlp.exe")
    FFMPEGPATH = os.path.join(BIN_DIR, "ffmpeg.exe")
    STREAMLINKPATH = "streamlink"

    ensure_tools(BIN_DIR, YTDLPPATH, FFMPEGPATH)

    current_process = None
    download_log = []

    def ensure_dependencies():
        missing_files = []
        if not os.path.exists(YTDLPPATH): missing_files.append(os.path.basename(YTDLPPATH))
        if not os.path.exists(FFMPEGPATH): missing_files.append(os.path.basename(FFMPEGPATH))
        if missing_files:
            messagebox.showerror("Dependency Error", f"Missing files: {', '.join(missing_files)}\n\nPlace them in the 'bin' folder.")
            return False
        return True

    def append_text(text):
        app.output_text.configure(state="normal")
        app.output_text.insert("end", text + "\n")
        app.output_text.see("end")
        app.output_text.configure(state="disabled")
        download_log.append(f"{datetime.now().strftime('%H:%M:%S')}: {text}")

    def save_log():
        fname = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if fname:
            with open(fname, "w", encoding="utf-8") as f:
                f.write("\n".join(download_log))
            append_text("Log saved.")

    def start_stream():
        threading.Thread(target=_start_stream_task, daemon=True).start()

    def _start_stream_task():
        nonlocal current_process
        if not ensure_dependencies():
            append_text("Missing dependencies for streams")
            return
        stream_url = app.stream_url_entry.get().strip()
        if not stream_url:
            append_text("Enter stream URL")
            return
        append_text(f"Starting stream recording: {stream_url}")
        app.stop_button.configure(state="normal")
        vods_dir = os.path.join(SCRIPTDIR, "vods")
        os.makedirs(vods_dir, exist_ok=True)
        cmd = f'"{STREAMLINKPATH}" --hls-live-restart "{stream_url}" best -O | "{FFMPEGPATH}" -i - -c copy "{os.path.join(vods_dir, "stream.mp4")}"'
        current_process = subprocess.Popen(cmd, shell=True)
        append_text("Stream capture started.")
        current_process.wait()
        append_text("Stream capture finished.")
        app.stop_button.configure(state="disabled")
        messagebox.showinfo("Stream finished", "Stream recording finished.")

    def start_video_download_thread():
        chosen_quality = app.quality_var.get()
        chosen_audio = app.audio_var.get()
        threading.Thread(target=_start_video_download_task, args=(chosen_quality, chosen_audio), daemon=True).start()

    def _start_video_download_task(chosen_quality, chosen_audio):
        nonlocal current_process
        if not ensure_dependencies():
            append_text("Missing dependencies for video")
            return
        videos_dir = os.path.join(SCRIPTDIR, "videos")
        os.makedirs(videos_dir, exist_ok=True)
        video_url = app.video_url_entry.get().strip()
        if not video_url:
            append_text("Enter video URL")
            return
        cookies_path = app.cookies_path_entry.get().strip()
        append_text(f"Starting video download: {video_url}")
        app.stop_button.configure(state="normal")

        if chosen_quality == "best":
            cmd_parts = [
                f'"{YTDLPPATH}"',
                '--ffmpeg-location',
                f'"{os.path.dirname(FFMPEGPATH)}"',
                '--merge-output-format',
                'mp4',
                '-o',
                f'"{os.path.join(videos_dir, "%(title)s.%(ext)s")}"',
                f'"{video_url}"'
            ]
        else:
            cmd_parts = [
                f'"{YTDLPPATH}"',
                '--ffmpeg-location',
                f'"{os.path.dirname(FFMPEGPATH)}"',
                '-f',
                chosen_quality,
                '--merge-output-format',
                'mp4',
                '-o',
                f'"{os.path.join(videos_dir, "%(title)s.%(ext)s")}"',
                f'"{video_url}"'
            ]

        if chosen_audio:
            cmd_parts.insert(3, '-f')
            cmd_parts.insert(4, 'bestaudio')
            cmd_parts.insert(5, '--merge-output-format')
            cmd_parts.insert(6, 'mp3')

        if cookies_path:
            cmd_parts.insert(1, f'--cookies "{cookies_path}"')

        cmd = " ".join(cmd_parts)
        append_text(f"Command: {cmd}")

        current_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = current_process.communicate()
        append_text(stdout.decode(errors='ignore'))
        if stderr:
            append_text(stderr.decode(errors='ignore'))

        app.stop_button.configure(state="disabled")

        if current_process.returncode == 0:
            append_text("Video download finished successfully.")
            messagebox.showinfo("Download complete", "Video has been downloaded successfully.")
        else:
            append_text("Video download failed. Check logs for details.")
            messagebox.showerror("Download failed", "See logs for error details.")

        current_process = None

    def stop_download():
        nonlocal current_process
        if current_process and current_process.poll() is None:
            try:
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(current_process.pid)])
                append_text("Download stopped.")
            except Exception as e:
                append_text(f"Error stopping process: {e}")
        else:
            append_text("No active download process.")
        app.stop_button.configure(state="disabled")
        current_process = None

    def browse_cookies():
        path = filedialog.askopenfilename(title="Select cookies.txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            app.cookies_path_entry.delete(0, "end")
            app.cookies_path_entry.insert(0, path)

    def open_videos_folder():
        videos_dir = os.path.join(SCRIPTDIR, "videos")
        try:
            os.startfile(videos_dir)
        except Exception as e:
            append_text(f"Error opening folder: {e}")

    class App(customtkinter.CTk):
        def __init__(self):
            super().__init__()
            self.title("SimpleDLP")
            self.geometry("820x700")
            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(5, weight=1)

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
                    "quality": "Качество:",
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
                    "quality": "Quality:",
                    "title": "SIMPLEDLP",
                    "contacts": "YouTube: @qualby   |   Discord: qualbyyyy   |   Telegram: @qualbyy",
                }
            }

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
            self.stream_url_entry = customtkinter.CTkEntry(input_frame, placeholder_text="https://...")
            self.stream_url_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

            self.video_label = customtkinter.CTkLabel(input_frame)
            self.video_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
            self.video_url_entry = customtkinter.CTkEntry(input_frame, placeholder_text="https://...")
            self.video_url_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

            self.cookies_label = customtkinter.CTkLabel(input_frame)
            self.cookies_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
            self.cookies_path_entry = customtkinter.CTkEntry(input_frame, placeholder_text="C:/path/to/cookies.txt")
            self.cookies_path_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
            self.browse_button = customtkinter.CTkButton(input_frame, command=browse_cookies)
            self.browse_button.grid(row=2, column=2, padx=10, pady=10)

            self.format_label = customtkinter.CTkLabel(input_frame)
            self.format_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")

            self.quality_var = customtkinter.StringVar(value=settings.get("QUALITY", "best"))
            self.quality_label = customtkinter.CTkLabel(input_frame)
            self.quality_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")

            quality_menu = customtkinter.CTkOptionMenu(
                input_frame,
                values=[
                    "best",
                    "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                    "bestvideo[height<=720]+bestaudio/best[height<=720]",
                    "bestaudio"
                ],
                variable=self.quality_var
            )
            quality_menu.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

            self.show_formats_button = customtkinter.CTkButton(input_frame, command=lambda: self.show_formats(self.video_url_entry.get().strip()))
            self.show_formats_button.grid(row=3, column=2, padx=10, pady=10)

            self.audio_var = customtkinter.BooleanVar(value=settings.get("AUDIO_ONLY", False))
            self.audio_checkbox = customtkinter.CTkCheckBox(input_frame, variable=self.audio_var)
            self.audio_checkbox.grid(row=4, column=1, padx=10, pady=(0,10), sticky="w")

            button_frame = customtkinter.CTkFrame(self)
            button_frame.grid(row=3, column=0, padx=20, pady=(0,6), sticky="ew")
            button_frame.grid_columnconfigure((0,1,2,3), weight=1)

            self.record_stream_button = customtkinter.CTkButton(button_frame, command=start_stream)
            self.record_stream_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

            self.download_video_button = customtkinter.CTkButton(button_frame, command=start_video_download_thread)
            self.download_video_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

            self.open_folder_button = customtkinter.CTkButton(button_frame, command=open_videos_folder)
            self.open_folder_button.grid(row=0, column=2, padx=10, pady=10, sticky="ew")

            self.update_tools_button = customtkinter.CTkButton(button_frame, command=lambda: print("Manual update required for yt-dlp & ffmpeg"))
            self.update_tools_button.grid(row=0, column=3, padx=10, pady=10, sticky="ew")

            self.stop_button = customtkinter.CTkButton(button_frame, fg_color="#D32F2F", hover_color="#B71C1C", state="disabled", command=stop_download)
            self.stop_button.grid(row=1, column=0, columnspan=4, padx=10, pady=8, sticky="ew")

            self.save_log_button = customtkinter.CTkButton(button_frame, command=save_log)
            self.save_log_button.grid(row=2, column=0, columnspan=4, padx=10, pady=6, sticky="ew")

            self.output_text = customtkinter.CTkTextbox(self, state="disabled")
            self.output_text.grid(row=4, column=0, padx=20, pady=(0,10), sticky="nsew")

            self.contacts_label = customtkinter.CTkLabel(self, font=customtkinter.CTkFont(size=13), text_color="#888")
            self.contacts_label.grid(row=5, column=0, pady=(6,10), sticky="s")

            self.change_language(LANG)

        def show_formats(self, url):
            # Добавьте реализацию если нужно
            pass

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
            self.quality_label.configure(text=t["quality"])
            self.show_formats_button.configure(text=t["show_formats"])
            self.audio_checkbox.configure(text=t["audio_only"])
            self.record_stream_button.configure(text=t["record_stream"])
            self.download_video_button.configure(text=t["download_video"])
            self.open_folder_button.configure(text=t["open_folder"])
            self.update_tools_button.configure(text=t["update_tools"])
            self.stop_button.configure(text=t["stop"])
            self.save_log_button.configure(text=t["save_log"])
            self.contacts_label.configure(text=t["contacts"])

        def change_appearance_mode(self, choice):
            global APPEARANCE_MODE
            APPEARANCE_MODE = choice
            customtkinter.set_appearance_mode(APPEARANCE_MODE)

    app = App()

    def on_closing():
        save_settings(app)
        app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()

if __name__ == "__main__":
    main()
